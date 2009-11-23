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

def ezip(s1, s2):
  s1 = iter(s1)
  s2 = iter(s2)
  while 1:
    try:
      obj1 = s1.next()
      end1 = False
    except StopIteration:
      end1 = True
    try:
      obj2 = s2.next()
      end2 = False
    except StopIteration:
      end2 = True
    if end1 != end2: raise ValueError
    if end1 or end2: break
    yield (obj1, obj2)
  return


##  FileLock
##
##  lock = FileLock('foo')
##  lock.open(lock=False)
##  lock.close()
##
class FileLock(object):

  class FileLockError(IOError): pass
  class Failed(FileLockError): pass
  class Exists(FileLockError): pass
  
  def __init__(self, fname):
    self.fname = fname
    self._locked = False
    self._fp = None
    atexit.register(self._emerge)
    return

  def __repr__(self):
    return '<FileLock: %r, locked=%r>' % (self.fname, self._locked)

  def _filename(self, locked):
    if locked:
      return self.fname+'.locked'
    else:
      return self.fname

  def create(self):
    if os.path.exists(self._filename(True)):
      raise FileLock.Exists
    if os.path.exists(self._filename(False)):
      raise FileLock.Exists
    fp = open(self.fname, 'wb')
    fp.close()
    return

  def open(self, mode='r'):
    write = (mode == 'w')
    if self._fp:
      if write and not self._locked:
        self._fp.close()
      else:
        return
    if write:
      try:
        os.rename(self._filename(0), self._filename(1))
      except OSError:
        raise FileLock.Failed('cannot lock: %r' % self)
      self._locked = True
      mode = 'r+b'
    else:
      mode = 'r'
    try:
      self._fp = open(self._filename(self._locked), mode)
    except IOError, e:
      raise FileLock.FileLockError(e)
    return self

  def close(self):
    if self._fp:
      self._fp.close()
      self._fp = None
      if self._locked:
        try:
          os.rename(self._filename(1), self._filename(0))
        except OSError:
          raise FileLock.Failed('cannot release: %r (THIS MUST NOT HAPPEN!)' % self)
        self._locked = False
    return
  
  def flush(self):
    if self._fp:
      self._fp.flush()
    return

  def _emerge(self):
    if self._fp:
      print >>sys.stderr, 'Emergency close: %d: %r' % (os.getpid(), self.fname)
      self.close()
    return

  def write(self, data):
    if not self._locked: raise IOError('not locked: %r' % self)
    self._fp.write(data)
    return

  def read(self, size=0):
    if not self._fp: raise IOError('not open: %r' % self)
    return self._fp.read(size)

  def tell(self):
    if not self._fp: raise IOError('not open: %r' % self)
    return self._fp.tell()
  
  def seek(self, offset, whence=0):
    if not self._fp: raise IOError('not open: %r' % self)
    return self._fp.seek(offset, whence)


##  FixedDB
##
##  db = FixedDB()
##  db.create()
##  db.open()
##  db.close()
##  recno = db.add_record('data')
##  db.set_record('data', recno)
##  db.get_record(recno)
##
class FixedDB(FileLock):

  class FixedDBError(IOError): pass
  class Corrupted(FixedDBError): pass
  class InvalidRecord(FixedDBError): pass
  
  def __init__(self, fname):
    FileLock.__init__(self, fname)
    self.record_size = None
    self._nrecords = None
    self._cache = {}
    return

  def __repr__(self):
    return '<FixedDB: fname=%r, record_size=%s, nrecords=%s, locked=%r>' % \
           (self.fname, self.record_size, self._nrecords, self._locked)

  def create(self, record_size):
    try:
      FileLock.create(self)
    except FileLock.Exists:
      raise FixedDB.FixedDBError('already exists')
    FileLock.open(self, mode='w')
    FileLock.write(self, ''.join( str((i+1) % 10) for i in xrange(record_size-1) )+'\n')
    FileLock.close(self)
    return

  def open(self, mode='r'):
    FileLock.open(self, mode=mode)
    self.record_size = len(self._fp.readline())
    self._fp.seek(0, 2)
    file_size = self._fp.tell()
    if file_size % self.record_size != 0:
      raise FixedDB.Corrupted('open: illegal filesize: %r: %d mod %d != 0' %
                              (self, file_size, self.record_size))
    self._nrecords = int(file_size / self.record_size)-1
    return self

  def close(self):
    FileLock.close(self)
    self._cache.clear()
    return

  def flush(self):
    self._fp.flush()
    return
    
  def nextrecno(self):
    return self._nrecords

  def add_record(self, record):
    nspaces = self.record_size - len(record) - 1
    if nspaces < 0:
      raise FixedDB.Corrupted('too long record: %r: size=%r' % (self, len(record)))
    record += ' '*nspaces
    # open file
    self.seek(0, 2)
    self.write(record+'\n')
    # cache
    recno = self.nextrecno()
    self._nrecords = recno+1
    self._cache[recno] = record
    return recno

  def set_record(self, recno, record):
    if recno < 0 or self._nrecords <= recno:
      raise FixedDB.InvalidRecord('invalid recno: %r: recno=%d' % (self, recno))
    nspaces = self.record_size - len(record) - 1
    if nspaces < 0:
      raise FixedDB.Corrupted('too long record: %r: size=%r' % (self, len(record)))
    record += ' '*nspaces
    offset = (recno+1) * self.record_size
    self.seek(offset)
    self.write(record+'\n')
    self._cache[recno] = record
    return

  def get_record(self, recno):
    if recno < 0 or self._nrecords <= recno:
      raise FixedDB.InvalidRecord('invalid recno: %r: recno=%d' % (self, recno))
    if recno in self._cache:
      return self._cache[recno]
    offset = (recno+1) * self.record_size
    self.seek(offset)
    record = self.read(self.record_size)
    if len(record) != self.record_size:
      raise FixedDB.Corrupted('premature eof: %r: recno=%d, offset=%d' %
                              (self, recno, offset))
    if record[-1] != '\n':
      raise FixedDB.Corrupted('record currupted: %r: recno=%d, offset=%d' %
                              (self, recno, offset))
    record = record[:-1]
    self._cache[recno] = record
    return record

  def __len__(self):
    if not self._fp: raise FileLock.FileLockError('not opened: %r' % self)
    return self._nrecords

  def __getitem__(self, recno):
    if not self._fp: raise FileLock.FileLockError('not opened: %r' % self)
    if recno < 0:
      recno %= self._nrecords
    return self.get_record(recno)

  def __iter__(self):
    if not self._fp: raise FileLock.FileLockError('not opened: %r' % self)
    for recno in xrange(self._nrecords):
      yield self.get_record(recno)
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

  @classmethod
  def name2idx(klass, name):
    m = re.match(r'^db(\d+)\.tar$', name, re.I)
    if not m: raise ValueError
    return int(m.group(1))
  @classmethod
  def idx2name(klass, idx):
    return ('db%05d.tar' % idx)

  @classmethod
  def entry2idxoffset(klass, x):
    return (int(x[:8], 16), int(x[8:].rstrip(), 16))
  @classmethod
  def idxoffset2entry(klass, idx, offset):
    return '%08x%07x' % (idx, offset)
  ENTRY_SIZE = 16  
      
  def __init__(self, basedir, catfile='catalog', lockfile='lock', maxsize=MAX_TARSIZE):
    self.basedir = basedir
    self.maxsize = maxsize
    self._catalog = FixedDB(os.path.join(basedir, catfile))
    self._dirlock = FileLock(os.path.join(basedir, lockfile))
    self._mode = None
    self._tarfps = {}
    return

  def __repr__(self):
    return '<TarDB: basedir=%r, catalog=%r, dirlock=%r, maxsize=%d>' % \
           (self.basedir, self._catalog, self._dirlock, self.maxsize)

  def create(self):
    if self._mode:
      raise TarDB.FileError('already open: %r' % self)
    try:
      os.makedirs(self.basedir)
    except OSError:
      raise TarDB.FileError('cannot create directory: %r' % self.basedir)
    self._catalog.create(self.ENTRY_SIZE)
    self._dirlock.create()
    return

  def open(self, mode='r'):
    if self._mode: raise TarDB.FileError('already open: %r' % self)
    try:
      self._catalog.open(mode=mode)
      self._mode = mode
    except FixedDB.FileLockError, e:
      raise TarDB.FileError(e)
    return self

  def close(self):
    if self._mode:
      for fp in self._tarfps.itervalues():
        fp.close()
      self._tarfps.clear()
      self._catalog.close()
      self._mode = None
    return

  def flush(self):
    if self._mode:
      for fp in self._tarfps.itervalues():
        fp.flush()
      self._catalog.flush()
    return
    
  def _get_fp(self, idx):
    if idx not in self._tarfps:
      fp = FileLock(os.path.join(self.basedir, self.idx2name(idx)))
      self._tarfps[idx] = fp
    else:
      fp = self._tarfps[idx]
    return fp
  
  def nextrecno(self):
    return self._catalog.nextrecno()

  def get_filepos(self, recno):
    try:
      record = self._catalog.get_record(recno)
    except FixedDB.InvalidRecord, e:
      raise TarDB.InvalidRecord(e)
    try:
      (idx, offset) = self.entry2idxoffset(record)
    except ValueError:
      raise TarDB.Corrupted('get: record corrputed: %r: recno=%d, offset=%d' %
                            (self, recno, offset))
    return (idx, offset)

  def add_record(self, info, data):
    if self._mode != 'w': raise TarDB.FileError('not writable: %r' % self)
    try:
      self._dirlock.open(mode='w')
    except FileLock.Failed, e:
      raise TarDB.LockError(e)
    try:
      # Find the last tar file index.
      idx = 0
      for fname in os.listdir(self.basedir):
        try:
          idx = max(idx, self.name2idx(fname))
        except ValueError:
          pass
      while 1:
        fp = self._get_fp(idx)
        try:
          fp.create()
        except FileLock.Exists:
          pass
        try:
          fp.open(mode='w')
        except FileLock.Failed, e:
          raise TarDB.LockError(e)
        fp.seek(0, 2)
        offset = fp.tell()
        if offset < self.maxsize: break
        idx += 1
      if offset % BLOCKSIZE != 0:
        raise TarDB.Corrupted('add_record: invalid tar size: %r: info_offset=%d' %
                              (self, offset))
      info.size = len(data)
      fp.write(info.tobuf())
      fp.write(data)
      fp.flush()
      padsize = info.size % BLOCKSIZE
      if padsize:
        fp.write('\x00' * (BLOCKSIZE-padsize))
      recno = self._catalog.add_record(self.idxoffset2entry(idx, offset))
    finally:
      self._dirlock.close()
    return recno
    
  def set_info(self, recno, info):
    if not self._mode: raise TarDB.FileError('not open: %r' % self)
    (idx, offset) = self.get_filepos(recno)
    fp = self._get_fp(idx)
    try:
      fp.open(mode='w')
    except FileLock.Failed, e:
      raise TarDB.LockError(e)
    fp.seek(offset)
    fp.write(info.tobuf())
    fp.close()
    return

  def get_record(self, recno):
    if not self._mode: raise TarDB.FileError('not open: %r' % self)
    (idx, offset) = self.get_filepos(recno)
    fp = self._get_fp(idx)
    try:
      fp.open()
    except FileLock.Failed, e:
      raise TarDB.LockError(e)
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
    fp.close()
    return (info, data)

  def get_info(self, recno):
    if not self._mode: raise TarDB.FileError('not open: %r' % self)
    (idx, offset) = self.get_filepos(recno)
    fp = self._get_fp(idx)
    try:
      fp.open()
    except FileLock.Failed, e:
      raise TarDB.LockError(e)
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
    if not self._mode: raise TarDB.FileError('not open: %r' % self)
    return len(self._catalog)

  def __iter__(self):
    if not self._mode: raise TarDB.FileError('not open: %r' % self)
    for recno in xrange(len(self._catalog)):
      yield self.get_info(recno)
    return
    
  def __getitem__(self, recno):
    return self.get_info(recno)

  def __setitem__(self, recno, info):
    return self.set_info(recno, info)

  def _get_catalog(self):
    for fname in os.listdir(self.basedir):
      try:
        idx = self.name2idx(fname)
      except ValueError:
        continue
      try:
        fp = file(os.path.join(self.basedir, fname), 'rb')
      except IOError, e:
        raise TarDB.FileError(e)
      while 1:
        offset = fp.tell()
        buf = fp.read(BLOCKSIZE)
        if len(buf) != BLOCKSIZE: break
        info = TarInfo.frombuf(buf)
        size = ((info.size + BLOCKSIZE-1) / BLOCKSIZE) * BLOCKSIZE
        if len(fp.read(size)) != size: break
        yield (idx, offset)
      fp.close()
    return

  def validate_catalog(self):
    if self._mode: raise TarDB.FileError('already open: %r' % self)
    try:
      self._catalog.open(mode='r')
    except FixedDB.FileLockError, e:
      raise TarDB.FileError(e)
    for (recno, (entry, (idx,offset))) in enumerate(ezip(self._catalog, self._get_catalog())):
      if entry != self.idxoffset2entry(idx, offset):
        raise TarDB.Corrupted('validate_catalog: tar catalog corrupted: recno=%d' % recno)
    self._catalog.close()
    return
  
  def recover_catalog(self):
    if self._mode: raise TarDB.FileError('already open: %r' % self)
    self._catalog.create(self.ENTRY_SIZE)
    self._catalog.open(mode='w')
    recno = None
    for (idx,offset) in self._get_catalog():
      recno = self._catalog.add_record(self.idxoffset2entry(idx, offset))
    self._catalog.close()
    return recno


# unittests
if 0:
  import unittest
  dirname = './test_tardb/'
  class TarDBTest(unittest.TestCase):
    
    def setUp(self):
      db = TarDB(dirname)
      db.create()
      return
      
    def tearDown(self):
      for fname in os.listdir(dirname):
        if fname.startswith('.'): continue
        os.unlink(os.path.join(dirname, fname))
      os.rmdir(dirname)
      return

    def test_basic(self):
      # writing
      db = TarDB(dirname).open(mode='w')
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
      db = TarDB(dirname, maxsize=2048).open(mode='w')
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
      db = TarDB(dirname).open(mode='w')
      data_foo = '123'
      mtime = 12345
      info = TarInfo('foo')
      info.mtime = mtime
      db.add_record(info, data_foo)
      db.close()
      # reading
      db = TarDB(dirname).open(mode='w')
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
      db = TarDB(dirname).open(mode='w')
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
  elif cmd == 'ls':
    db.open()
    for (i,info) in enumerate(db):
      print i,info
  elif cmd == 'get':
    recno = int(args.pop(0))
    db.open()
    data = db.get_record(recno)
    sys.stdout.write(data)
    db.close()
  elif cmd == 'add':
    db.open(mode='w')
    name = args.pop(0)
    data = open(args.pop(0), 'rb').read()
    db.add_record(TarInfo(name), data)
    db.close()
  elif cmd == 'getinfo':
    recno = int(args.pop(0))
    db.open()
    info = db.get_info(recno)
    print info
    db.close()
  elif cmd == 'setinfo':
    recno = int(args.pop(0))
    db.open()
    info = db.get_info(recno)
    info.name = args.pop(0)
    db.set_info(recno, info)
    print info, name
    db.close()
  elif cmd == 'recover':
    db.recover_catalog()
  elif cmd == 'validate':
    db.validate_catalog()
  return

if __name__ == '__main__': sys.exit(main(sys.argv))
