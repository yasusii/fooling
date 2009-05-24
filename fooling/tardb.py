#!/usr/bin/env python
##
##  tardb.py - tar database
##
##  TarDB is a simplistic data archival system using ordinary
##  filesystems. It is suitable for storing a large number of small
##  chunk of data. Unlike other database systems, TarDB uses
##  a data format that is extremely simple, well-known, and can be
##  manipulated with a standard Unix tools. With TarDB, you can add
##  a new record, retrieve an existing record using the record number,
##  scanning all the records. TarDB is an archival system, which
##  means you cannot modify a record once it is created.
##
##  Usage:
##
##   # creation of TarDB
##   from tarfile import TarInfo
##   TarDB.create('mydb')
##
##   (The following files are created.)
##   -rw-r--r--  1 yusuke   16 Dec 29 18:04 mydb/catalog
##   -rw-r--r--  1 yusuke    0 Dec 29 18:04 mydb/lock
##
##   # writing TarDB
##   db = TarDB('mydb')
##   db.open()
##   print db.add_record(TarInfo('foo'), '123')  # 0
##   print db.add_record(TarInfo('bar'), '456')  # 1
##   db.close()
##
##   # reading TarDB
##   db = TarDB('mydb')
##   db.open()
##   (info0,data0) = get_record(0)
##   (info1,data1) = get_record(1)
##
##   # scanning all the records
##   for info in db:
##     print info
##   db.close()
##
##   # modifying TarDB (only meta information is changeable)
##   db = TarDB('mydb')
##   db.open()
##   db[0] = TarInfo('zzz')
##   db.close()
##

import sys, os, os.path, re, atexit
from tarfile import BLOCKSIZE, TarInfo


##  FileLock
##
##  lock = FileLock('foo')
##  lock.acquire()
##  lock.release()
##
class FileLock(object):

  class Failed(Exception): pass
  
  def __init__(self, fname):
    self.fname = fname
    self.locked = False
    atexit.register(self.emerge)
    return

  def __repr__(self):
    return '<FileLock: %r, locked=%r>' % (self.fname, self.locked)

  def create(self):
    fp = file(self.filename(False), 'ab')
    fp.close()
    return

  def filename(self, locked=None):
    if locked == None:
      locked = self.locked
    if locked:
      return self.fname+'.locked'
    else:
      return self.fname

  def acquire(self):
    if self.locked:
      raise FileLock.Failed('already acquired: %r' % self)
    try:
      os.rename(self.filename(False), self.filename(True))
    except OSError:
      raise FileLock.Failed('failed to acquire: %r' % self)
    self.locked = True
    return
  
  def acquire_open(self, mode):
    if self.locked:
      raise FileLock.Failed('already acquired: %r' % self)
    try:
      os.rename(self.filename(False), self.filename(True))
    except OSError:
      raise FileLock.Failed('failed to acquire: %r' % self)
    try:
      fp = file(self.filename(True), mode)
    except IOError, e:
      try:
        os.rename(self.filename(True), self.filename(False))
      except OSError:
        pass
      raise FileLock.Failed(e)
    self.locked = True
    return fp
  
  def release(self):
    if not self.locked:
      raise FileLock.Failed('not acquired: %r' % self)
    try:
      os.rename(self.filename(True), self.filename(False))
    except OSError:
      raise FileLock.Failed('failed to release: %r (THIS MUST NOT HAPPEN!)' % self)
    self.locked = False
    return
  
  def emerge(self):
    if self.locked:
      print >>sys.stderr, 'Emergency lock released: %d: %r' % (os.getpid(), self.fname)
      self.release()
    return


##  Catalog
##
class Catalog(object):

  class CatalogError(Exception): pass
  class FileError(CatalogError): pass
  class Corrupted(CatalogError): pass
  class InvalidRecord(CatalogError): pass
  
  DEFAULT_RECORD_SIZE = 16
  
  def __init__(self, fname, record_size=DEFAULT_RECORD_SIZE):
    self.fname = fname
    self.record_size = record_size
    self._fp = None
    self._nrecords = None
    self._cache = {}
    return

  def __repr__(self):
    return '<Catalog: fname=%r, record_size=%s, nrecords=%s>' % \
           (self.fname, self.record_size, self._nrecords)

  def create(self):
    fp = open(self.fname, 'wb')
    fp.write(''.join( str((i+1) % 10) for i in xrange(self.record_size-1) )+'\n')
    fp.close()
    return

  def open(self):
    if self._fp:
      raise Catalog.FileError('open: already opened: %r' % self)
    try:
      self._fp = open(os.path.join(self.fname), 'rb')
    except IOError, e:
      raise Catalog.FileError(e)
    record_size = len(self._fp.next())
    if record_size != self.record_size:
      raise Catalog.Corrupted('open: illegal record size: %r: %d != %d' %
                              (self, record_size, self.record_size))
    self._fp.seek(0, 2)
    file_size = self._fp.tell()
    if file_size % self.record_size != 0:
      raise Catalog.Corrupted('open: illegal filesize: %r: %d mod %d != 0' %
                              (self, file_size, self.record_size))
    self._nrecords = int(file_size / self.record_size)-1
    return self

  def close(self):
    if self._fp:
      self._fp.close()
      self._fp = None
      self._cache.clear()
    return self
    
  def get(self, recno):
    if not self._fp:
      raise Catalog.FileError('get: not opened: %r' % self)
    if recno < 0 or self._nrecords <= recno:
      raise Catalog.InvalidRecord('get: invalid recno: %r: recno=%d' % (self, recno))
    if recno in self._cache:
      return self._cache[recno]
    offset = (recno+1) * self.record_size
    self._fp.seek(offset)
    line = self._fp.read(self.record_size)
    if len(line) != self.record_size:
      raise Catalog.Corrupted('get: premature eof: %r: recno=%d, offset=%d' %
                              (self, recno, offset))
    try:
      rec_offset = int(line[:8], 16)
    except ValueError:
      raise Catalog.Corrupted('get: record corrputed: %r: recno=%d, offset=%d' %
                              (self, recno, offset))
    rec_file = line[8:].rstrip()
    self._cache[recno] = (rec_file, rec_offset)
    return (rec_file, rec_offset)

  def add(self, rec_file, rec_offset):
    if not self._fp:
      raise Catalog.FileError('add: not opened: %r' % self)
    line = '%08x%s' % (rec_offset, rec_file)
    nspaces = self.record_size - len(line) - 1
    if nspaces < 0:
      raise Catalog.Corrupted('add: too long record: %r: rec_file=%r' % (self, rec_file))
    line += ' '*nspaces
    # open file
    lock = FileLock(self.fname)
    fp = lock.acquire_open('r+b')
    fp.seek(0, 2)
    fp.write(line+'\n')
    fp.close()
    lock.release()
    # cache
    recno = self._nrecords
    self._cache[recno] = (rec_file, rec_offset)
    self._nrecords += 1
    return recno

  def __len__(self):
    if not self._fp:
      raise Catalog.FileError('__len__: not opened: %r' % self)
    return self._nrecords

  def __getitem__(self, recno):
    if not self._fp:
      raise Catalog.FileError('__getitem__: not opened: %r' % self)
    if recno < 0:
      recno %= self._nrecords
    return self.get(recno)

  def __iter__(self):
    if not self._fp:
      raise Catalog.FileError('__iter__: not opened: %r' % self)
    for recno in xrange(self._nrecords):
      yield self.get(recno)
    return


##  TarDB
##
class TarDB(object):

  class TarDBError(Exception): pass
  class LockError(TarDBError): pass
  class FileError(TarDBError): pass
  class Corrupted(TarDBError): pass
  class InvalidRecord(TarDBError): pass

  MAX_TARSIZE = 10*1024*1024            # default: 10Mbytes max
  EMPTY_BLOCK = '\x00' * BLOCKSIZE

  def __init__(self, basedir, catfile='catalog', lockfile='lock', maxsize=MAX_TARSIZE):
    self.basedir = basedir
    self.maxsize = maxsize
    self._catalog = Catalog(os.path.join(basedir, catfile))
    self._dirlock = FileLock(os.path.join(basedir, lockfile))
    self._opened = False
    self._tarfps = {}
    return

  def __repr__(self):
    return '<TarDB: basedir=%r, catalog=%r, dirlock=%r, maxsize=%d>' % \
           (self.basedir, self._catalog, self._dirlock, self.maxsize)

  def create(self):
    if not os.path.isdir(self.basedir):
      raise TarDB.FileError('%r is not a directory.' % self.basedir)
    self._catalog.create()
    self._dirlock.create()
    return

  def open(self):
    if self._opened:
      raise TarDB.FileError('open: already opened: %r' % self)
    try:
      self._catalog.open()
    except Catalog.FileError, e:
      raise TarDB.FileError(e)
    self._opened = True
    return self

  def close(self):
    if not self._opened:
      raise TarDB.FileError('close: not opened: %r' % self)
    for fp in self._tarfps.itervalues():
      fp.close()
    self._tarfps.clear()
    self._catalog.close()
    self._opened = False
    return self

  def add_record(self, info, data):
    if not self._opened:
      raise TarDB.FileError('add_record: not opened: %r' % self)
    try:
      self._dirlock.acquire()
    except FileLock.Failed, e:
      raise TarDB.LockError(e)
    try:
      TARNAME_PAT = re.compile(r'^db(\d+)\.tar$')
      idx = 0
      for fname in os.listdir(self.basedir):
        m = TARNAME_PAT.match(fname)
        if m:
          idx = max(idx, int(m.group(1)))
      while 1:
        name = ('db%05d' % idx)
        lock = FileLock(os.path.join(self.basedir, name+'.tar'))
        lock.create()
        try:
          fp = lock.acquire_open('r+b')
        except FileLock.Failed, e:
          raise TarDB.LockError(e)
        fp.seek(0, 2)
        offset = fp.tell()
        if offset < self.maxsize: break
        idx += 1
        fp.close()
        lock.release()
      try:
        if offset % BLOCKSIZE != 0:
          raise TarDB.Corrupted('add_record: invalid tar size: %r: info_offset=%d' %
                                (self, offset))
        recno = self._catalog.add(name, offset)
        info.size = len(data)
        fp.write(info.tobuf())
        fp.write(data)
        padsize = info.size % BLOCKSIZE
        if padsize:
          fp.write('\x00' * (BLOCKSIZE-padsize))
      finally:
        fp.close()
        lock.release()
    finally:
      self._dirlock.release()
    return recno
    
  def set_info(self, recno, info):
    if not self._opened:
      raise TarDB.FileError('set_info: not opened: %r' % self)
    try:
      (name, offset) = self._catalog.get(recno)
    except Catalog.InvalidRecord:
      raise TarDB.InvalidRecord(recno)
    lock = FileLock(os.path.join(self.basedir, name+'.tar'))
    try:
      fp = lock.acquire_open('r+b')
    except FileLock.Failed, e:
      raise TarDB.LockError(e)
    fp.seek(offset)
    fp.write(info.tobuf())
    fp.close()
    lock.release()
    return

  def _get_fp(self, name):
    if name not in self._tarfps:
      fname = os.path.join(self.basedir, name)+'.tar'
      fp = open(fname, 'rb')
      self._tarfps[name] = fp
    else:
      fp = self._tarfps[name]
    return fp
  
  def get_record(self, recno):
    if not self._opened:
      raise TarDB.FileError('get_record: not opened: %r' % self)
    try:
      (name, offset) = self._catalog.get(recno)
    except Catalog.InvalidRecord:
      raise TarDB.InvalidRecord(recno)
    fp = self._get_fp(name)
    fp.seek(offset)
    buf = fp.read(BLOCKSIZE)
    if len(buf) != BLOCKSIZE:
      raise TarDB.Corrupted('get_record: premature eof info: %r, recno=%d, info_offset=%d' %
                            (self, recno, offset))
    try:
      info = TarInfo.frombuf(buf)
    except ValueError:
      raise TarDB.Corrupted('get_record: record corrupted: %r, recno=%d, offset=%d' %
                            (self, recno, offset))
    data = fp.read(info.size)
    if len(data) != info.size:
      raise TarDB.Corrupted('get_record: premature eof data: %r, recno=%d, info_offset=%d' %
                            (self, recno, offset))
    return (info, data)

  def get_info(self, recno):
    if not self._opened:
      raise TarDB.FileError('get_info: not opened: %r' % self)
    try:
      (name, offset) = self._catalog.get(recno)
    except Catalog.InvalidRecord:
      raise TarDB.InvalidRecord(recno)
    fp = self._get_fp(name)
    fp.seek(offset)
    buf = fp.read(BLOCKSIZE)
    if len(buf) != BLOCKSIZE:
      raise TarDB.Corrupted('get_info: premature eof in info block: %r, recno=%d, info_offset=%d' %
                            (self, recno, offset))
    try:
      return TarInfo.frombuf(buf)
    except ValueError:
      raise TarDB.Corrupted('get_info: tar record corrupted: %r, recno=%d, info_offset=%d' %
                            (self, recno, offset))

  def __len__(self):
    if not self._opened:
      raise TarDB.FileError('__len__: not opened: %r' % self)
    return len(self._catalog)

  def __iter__(self):
    if not self._opened:
      raise TarDB.FileError('__iter__: not opened: %r' % self)
    for recno in xrange(len(self._catalog)):
      yield self.get_info(recno)
    return
    
  def __getitem__(self, recno):
    return self.get_info(recno)

  def __setitem__(self, recno, info):
    return self.set_info(recno, info)


# unittests
if 0:
  import unittest
  dirname = './test_tardb/'
  class TarDBTest(unittest.TestCase):
    
    def setUp(self):
      os.mkdir(dirname)
      db = TarDB(dirname)
      db.create()
      return
      
    def test_basic(self):
      # writing
      db = TarDB(dirname).open()
      data_foo = '123'
      data_bar = 'ABCDEF'
      db.add_record(TarInfo('foo'), data_foo)
      db.add_record(TarInfo('bar'), data_bar)
      db.close()
      #
      files = os.listdir(dirname)
      self.assertEqual(len(files), 3)
      self.assertTrue('catalog' in files)
      self.assertTrue('lock' in files)
      self.assertTrue('db00000.tar' in files)
      # reading
      db = TarDB(dirname).open()
      (info1, data1) = db.get_record(0)
      self.assertEqual(data1, data_foo)
      self.assertEqual(len(data1), info1.size)
      (info2, data2) = db.get_record(1)
      self.assertEqual(data2, data_bar)
      self.assertEqual(len(data2), info2.size)
      # iter
      infos = list(db)
      self.assertEqual(len(infos), 2)
      self.assertEqual(infos[0].name, info1.name)
      self.assertEqual(infos[1].name, info2.name)
      db.close()
      return
    
    def test_split_tarfiles(self):
      # writing
      db = TarDB(dirname, maxsize=2048).open()
      data_foo = '123'
      data_bar = 'ABCDEF'
      data_zzz = '!@#$%$'
      db.add_record(TarInfo('foo'), data_foo)
      db.add_record(TarInfo('bar'), data_bar)
      db.add_record(TarInfo('zzz'), data_zzz)
      db.close()
      #
      files = os.listdir(dirname)
      self.assertEqual(len(files), 4)
      self.assertTrue('catalog' in files)
      self.assertTrue('lock' in files)
      self.assertTrue('db00000.tar' in files)
      self.assertTrue('db00001.tar' in files)
      # reading
      db = TarDB(dirname).open()
      (info1, data1) = db.get_record(0)
      self.assertEqual(data1, data_foo)
      self.assertEqual(len(data1), info1.size)
      (info2, data2) = db.get_record(1)
      self.assertEqual(data2, data_bar)
      self.assertEqual(len(data2), info2.size)
      (info3, data3) = db.get_record(2)
      self.assertEqual(data3, data_zzz)
      self.assertEqual(len(data3), info3.size)
      # iter
      infos = list(db)
      self.assertEqual(len(infos), 3)
      self.assertEqual(infos[0].name, info1.name)
      self.assertEqual(infos[1].name, info2.name)
      self.assertEqual(infos[2].name, info3.name)
      db.close()
      return
    
    def test_change_info(self):
      # writing
      db = TarDB(dirname).open()
      data_foo = '123'
      mtime = 12345
      info = TarInfo('foo')
      info.mtime = mtime
      db.add_record(info, data_foo)
      db.close()
      # reading
      db = TarDB(dirname).open()
      info = db[0]
      self.assertEqual(info.mtime, mtime)
      db[0] = info
      db.close()
      return
    
    def test_failure(self):
      # cannot open
      self.assertRaises(TarDB.FileError, lambda : TarDB('fungea').open())
      # not opened
      db = TarDB(dirname)
      self.assertRaises(TarDB.FileError, lambda : db.add_record(TarInfo('foo'), '123'))
      # invalid record
      db.open()
      self.assertRaises(TarDB.InvalidRecord, lambda : db.get_record(0))
      db.close()
      return
    
    def test_tar_compatibility(self):
      # writing
      db = TarDB(dirname).open()
      data_foo = '123'
      mtime = 12345
      info = TarInfo('foo')
      info.mtime = mtime
      db.add_record(info, data_foo)
      db.close()
      # reading with tarfile
      import tarfile
      tar = tarfile.TarFile(os.path.join(dirname, 'db00000.tar'))
      info = tar.next()
      data = tar.extractfile(info).read()
      self.assertEqual(data, data_foo)
      self.assertEqual(len(data), info.size)
      self.assertEqual(info.mtime, mtime)
      tar.close()
      return

    def test_lock(self):
      # opening multiple tars
      db1 = TarDB(dirname).open()
      db2 = TarDB(dirname).open()
      files = os.listdir(dirname)
      self.assertTrue('lock' in files)
      self.assertTrue('lock.locked' not in files)
      db1.close()
      db2.close()
      return
    
    def tearDown(self):
      for fname in os.listdir(dirname):
        if fname.startswith('.'): continue
        os.unlink(os.path.join(dirname, fname))
      os.rmdir(dirname)
      return

  unittest.main()
  assert 0, 'not reached'

def main(argv):
  import getopt, locale
  def usage():
    print 'usage: %s {create,ls,get,add,getinfo,setinfo} basedir [args]' % argv[0]
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(argv[1:], 'v')
  except getopt.GetoptError:
    usage()
  if len(args) < 2: return usage()
  verbose = 1
  for (k, v) in opts:
    if k == '-d': verbose += 1
  cmd = args.pop(0)
  db = TarDB(args.pop(0))
  if cmd == 'create':
    db.create()
    return
  if cmd == 'ls':
    db.open()
    for (i,info) in enumerate(db):
      print i,info
  elif cmd == 'get':
    recno = int(args.pop(0))
    db.open()
    data = db.get_record(recno)
    sys.stdout.write(data)
  elif cmd == 'add':
    db.open()
    name = args.pop(0)
    data = open(args.pop(0), 'rb').read()
    db.add_record(TarInfo(name), data)
  elif cmd == 'getinfo':
    recno = int(args.pop(0))
    db.open()
    info = db.get_info(recno)
    print info
  elif cmd == 'setinfo':
    recno = int(args.pop(0))
    db.open()
    info = db.get_info(recno)
    info.name = args.pop(0)
    db.set_info(recno, info)
    print info, name
  db.close()
  return

if __name__ == '__main__': sys.exit(main(sys.argv))
