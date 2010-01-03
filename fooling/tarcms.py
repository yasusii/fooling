#!/usr/bin/env python
import sys
import os, os.path, stat
from indexdb import IndexDB
from corpus import GzipTarDBCorpus
from tardb import FixedDB
from indexer import Indexer
from selection import Selection
from tardb import ezip


##  TarCMS
##
class TarCMS(object):

  """Content Management with tar files

  Sample usage:
    # Create a TarCMS object.
    cms = TarCMS(basedir)
    # Actually create the structure on disk.
    cms.create()
    # Open it.
    cms.open()
    # Add a new document.
    aid = cms.create_article('msg', 'this is my text.')
    # Modify the document.
    tid = cms.modify_article(aid, 'this is my revised text.')
    # Search all documents.
    for (aid,tid,mtime,title,snippet) in cms.find_articles(queries):
      data = cms.get_snapshot(tid)
    # Retrieve all revisions of an article:
    for tid in cms.get_article(aid):
      data = cms.get_snapshot(tid)
    # Close it.
    cms.close()
    # Check the validity of the metadata.
    cms.validate()
    # Recover the metadata.
    cms.recover()
  """
     
  class TarCMSError(Exception): pass

  def __init__(self, basedir, doctype, encoding='utf-8', indexstyle=None, threshold=100, verbose=False):
    self.basedir = basedir
    self.threshold = threshold
    self.verbose = verbose
    self._corpus = GzipTarDBCorpus(os.path.join(basedir, 'src'),
                                   doctype, encoding,
                                   indexstyle=indexstyle, namelen=8)
    self._artdb = FixedDB(os.path.join(basedir, 'articles'))
    self._indexdb = IndexDB(os.path.join(basedir, 'idx'), 'idx')
    self._loctoindex = None
    self._mode = None
    return

  def __repr__(self):
    return '<TarCMS: basedir=%r>' % (self.basedir,)

  def __iter__(self):
    return self.list_articles()
  
  def create(self):
    if self._mode: raise TarCMS.TarCMSError('already open: %r' % self)
    self._corpus.create()
    self._artdb.create(9)
    self._indexdb.create()
    return

  def open(self, mode='r'):
    if self._mode: raise TarCMS.TarCMSError('already open: %r' % self)
    self._corpus.open(mode=mode)
    self._artdb.open(mode=mode)
    self._indexdb.open()
    self._loctoindex = set()
    self._mode = mode
    return

  def close(self):
    if not self._mode: raise TarCMS.TarCMSError('not open: %r' % self)
    self.flush()
    self._corpus.close()
    self._artdb.close()
    self._indexdb.close()
    self._mode = None
    return

  def _add_data(self, data, name, ext, mtime=0, labels=None):
    if not self._mode: raise TarCMS.TarCMSError('not open: %r' % self)
    loc = self._corpus.add_data(data, name, ext, mtime=mtime, labels=labels)
    self._loctoindex.add(loc)
    if self.threshold and self.threshold <= len(self._loctoindex):
      self.flush()
    return loc

  def _add_file(self, path, name, mtime=None, labels=None):
    (_,ext) = os.path.splitext(path)
    st = os.stat(path)
    fp = file(path, 'rb')
    data = fp.read()
    fp.close()
    if not mtime:
      mtime = st[stat.ST_MTIME]
    return self._add_data(data, name, ext, mtime=mtime, labels=labels)

  def flush(self):
    self._corpus.flush()
    self._artdb.flush()
    indexer = Indexer(self._indexdb, self._corpus, verbose=self.verbose)
    for loc in self._loctoindex:
      indexer.index_loc(loc)
    indexer.finish()
    self._loctoindex.clear()
    return

  def create_article(self, ext, data, mtime=0, labels=None):
    if not self._mode: raise TarCMS.TarCMSError('not open: %r' % self)
    assert len(ext) == 3
    aid = '%08x' % self._artdb.nextrecno()
    loc = self._add_data(data, aid, ext, mtime=mtime, labels=labels)
    assert aid == loc
    self._artdb.add_record(loc)
    return aid

  def modify_article(self, aid, data, mtime=0, labels=None):
    if not self._mode: raise TarCMS.TarCMSError('not open: %r' % self)
    loc0 = self._artdb.get_record(int(aid, 16))
    ext = self._corpus.get_ext(loc0)
    loc = self._add_data(data, aid, ext, mtime=mtime, labels=labels)
    tid = '%08x' % self._artdb.add_record(loc0)
    self._artdb.set_record(int(aid, 16), tid)
    return tid

  def get_article(self, aid):
    """Get all revisions of an article."""
    if not self._mode: raise TarCMS.TarCMSError('not open: %r' % self)
    loc = self._artdb.get_record(int(aid, 16))
    while aid != loc:
      yield loc
      loc = self._artdb.get_record(int(loc, 16))
    yield loc
    return

  def list_articles(self):
    for (aid,tid) in enumerate(self._artdb):
      aid = '%08x' % aid
      if aid == tid:
        yield aid
    return

  def find_articles(self, preds, disjunctive=False):
    """Find articles that match to the predicates."""
    if not self._mode: raise TarCMS.TarCMSError('not open: %r' % self)
    sel = Selection(self._indexdb, preds, disjunctive=disjunctive)
    for (_,x) in sel:
      (mtime, tid, title, snippet) = sel.get_snippet(x)
      aid = self._corpus.get_name(tid)
      yield (aid, tid, mtime, title, snippet)
    return

  def get_snapshot(self, tid):
    """Get a particular revision of article specified by tid."""
    if not self._mode: raise TarCMS.TarCMSError('not open: %r' % self)
    return self._corpus.get_data(tid)

  def get_latest(self, aid):
    """Equivalent to self.get_snapshot(self.get_article(aid)[0])."""
    for tid in self.get_article(aid):
      return self.get_snapshot(tid)
    raise KeyError(aid)

  def list_snapshots(self):
    for (aid,_) in enumerate(self._artdb):
      yield '%08x' % aid
    return

  def _get_catalog(self):
    if self._mode: raise TarCMS.TarCMSError('already open: %r' % self)
    self._corpus.open(mode='r')
    arts = []
    for loc in self._corpus.get_all_locs():
      tid = self._corpus.get_recno(loc)
      aid = int(self._corpus.get_name(loc), 16)
      if tid == aid:
        arts.append(loc)
      else:
        arts.append(arts[aid])
        arts[aid] = loc
    self._corpus.close()
    return arts

  def validate_catalog(self):
    if self._mode: raise TarCMS.TarCMSError('already open: %r' % self)
    self._artdb.open(mode='r')
    for (entry,loc) in ezip(self._artdb, self._get_catalog()):
      if entry != loc: raise TarCMS.TarCMSError
    self._artdb.close()
    return

  def recover_catalog(self):
    if self._mode: raise TarCMS.TarCMSError('already open: %r' % self)
    self._artdb.open(mode='w')
    for loc in self._get_catalog():
      self._artdb.add_record(loc)
    self._artdb.close()
    return

  def validate(self):
    if self._mode: raise TarCMS.TarCMSError('already open: %r' % self)
    self._corpus.validate_catalog()
    self.validate_catalog()
    return

  def recover(self):
    if self._mode: raise TarCMS.TarCMSError('already open: %r' % self)
    self._corpus.recover_catalog()
    self.recover_catalog()
    self._indexdb.reset()
    indexer = Indexer(self._indexdb, self._corpus, verbose=verbose)
    for loc in self._corpus.get_all_locs():
      indexer.index_loc(loc)
    indexer.finish()
    return
    

# 
if __name__ == '__main__':
  from document import EMailDocument
  from selection import KeywordPredicate
  from pycdb import CDBReader
  import unittest, shutil, tarfile, gzip, random, struct
  cleanup = True

  class TarCMSTest(unittest.TestCase):
    
    def setUp(self):
      dirname = './test.%s/' % self.id()
      try:
        shutil.rmtree(dirname)
      except OSError:
        pass
      self.cms = TarCMS(dirname, EMailDocument)
      self.cms.create()
      return
    
    def tearDown(self):
      try:
        if cleanup:
          shutil.rmtree(self.cms.basedir)
      except OSError:
        pass
      return

    def assertLock(self, path):
      self.assertTrue((os.path.isfile(path) and not os.path.isfile(path+'.locked')) or
                      (not os.path.isfile(path) and os.path.isfile(path+'.locked')))
      return

    def assertCMS(self, cms):
      self.assertTrue(os.path.isdir(cms.basedir))
      srcdir = os.path.join(cms.basedir, 'src')
      self.assertTrue(os.path.isdir(srcdir))
      self.assertLock(os.path.join(srcdir, 'lock'))
      self.assertLock(os.path.join(srcdir, 'catalog'))
      idxdir = os.path.join(cms.basedir, 'idx')
      self.assertTrue(os.path.isdir(idxdir))
      self.assertLock(os.path.join(cms.basedir, 'articles'))
      return

    def assertCMSTar(self, cms, fname, names):
      path = os.path.join(os.path.join(cms.basedir, 'src'), fname)
      self.assertLock(path)
      if os.path.isfile(path+'.locked'):
        path += '.locked'
      fp = tarfile.TarFile(path)
      r = []
      for info in fp:
        r.append(info.name)
      fp.close()
      self.assertEqual(r, names)
      return

    def assertCMSTarData(self, cms, fname, name, data):
      path = os.path.join(os.path.join(cms.basedir, 'src'), fname)
      self.assertLock(path)
      if os.path.isfile(path+'.locked'):
        path += '.locked'
      fp = tarfile.TarFile(path)
      x = gzip.GzipFile(fileobj=fp.extractfile(name)).read()
      fp.close()
      self.assertEqual(x, data)
      return

    def assertCMSIdx(self, cms, fname, keys):
      path = os.path.join(os.path.join(cms.basedir, 'idx'), fname)
      db = CDBReader(path)
      r = []
      for k in db.iterkeys():
        if k[0] == '\x00':
          (docid,sentid) = struct.unpack('>xll', k)
          r.append((docid, sentid))
        elif k[0] == '\xfd':
          pass
        elif k[0] == '\xfe':
          pass
        elif k == '\xff':
          pass
        else:
          (c,k) = (k[0], k[1:])
          w = k
          if '\x10' <= c and c <= '\x13':
            w = unicode(k, 'utf-8')
          elif c == '\x20':
            w = u''.join( unichr(0x3000+ord(c)) for c in k )
          elif c == '\xf0':
            if len(k) == 2:
              w = '%04d' % struct.unpack('>h', k)
            elif len(k) == 3:
              w = '%04d/%02d' % struct.unpack('>hb', k)
            elif len(k) == 4:
              w = '%04d/%02d/%02d' % struct.unpack('>hbb', k)
          r.append(w)
      self.assertEqual(r, keys)
      return

    def assertAid(self, cms, names):
      path = os.path.join(cms.basedir, 'articles')
      self.assertLock(path)
      if os.path.isfile(path+'.locked'):
        path += '.locked'
      fp = open(path)
      r = [ line.strip() for line in fp ]
      del r[0]
      fp.close()
      self.assertEqual(r, names)
      return

    def testBasic(self):
      self.cms.open(mode='w')
      aid = self.cms.create_article('msg', 'text1')
      self.assertEqual(self.cms.get_latest(aid), 'text1')
      self.cms.modify_article(aid, 'mod1 mod1')
      self.assertEqual(self.cms.get_latest(aid), 'mod1 mod1')
      self.cms.modify_article(aid, 'mod2.\nmodd')
      self.assertEqual(self.cms.get_latest(aid), 'mod2.\nmodd')
      self.cms.flush()
      self.assertEqual(list(self.cms.get_article(aid)),
                       ['00000002', '00000001' , '00000000'])
      self.assertEqual([ (aid,title,loc) for (aid,loc,mtime,title,snippet) in
                         self.cms.find_articles([KeywordPredicate('text1')]) ],
                       [ ('00000000', u'text1', '00000000') ])
      self.assertEqual([ (aid,title,loc) for (aid,loc,mtime,title,snippet) in
                         self.cms.find_articles([KeywordPredicate('modd')]) ],
                       [ ('00000000', u'mod2.', '00000002') ])
      self.assertCMS(self.cms)
      self.assertCMSTar(self.cms, 'db00000.tar',
                        ['00000000msg00000000.gz',
                         '00000000msg00000001.gz',
                         '00000000msg00000002.gz'])
      self.assertCMSTarData(self.cms, 'db00000.tar',
                            '00000000msg00000000.gz',
                            'text1')
      self.assertCMSTarData(self.cms, 'db00000.tar',
                            '00000000msg00000001.gz',
                            'mod1 mod1')
      self.assertCMSTarData(self.cms, 'db00000.tar',
                            '00000000msg00000002.gz',
                            'mod2.\nmodd')
      self.assertCMSIdx(self.cms, 'idx00000.cdb',
                        [(1,0),(2,0),(3,0),(3,1),
                         u'mod1', u'mod2', u'modd', u'text1'])
      self.assertAid(self.cms,
                     ['00000002',
                      '00000000',
                      '00000001'])
      self.cms.close()
      self.cms.validate()
      return
  
    def testArts(self):
      self.cms.open(mode='w')
      aid1 = self.cms.create_article('msg', 'art1')
      aid2 = self.cms.create_article('msg', 'art2')
      self.cms.modify_article(aid1, 'art1r')
      self.cms.modify_article(aid2, 'art2r')
      self.assertEqual(self.cms.get_latest(aid1), 'art1r')
      self.assertEqual(list(self.cms.get_article(aid1)),
                       ['00000002', '00000000'])
      self.assertEqual(self.cms.get_latest(aid2), 'art2r')
      self.assertEqual(list(self.cms.get_article(aid2)),
                       ['00000003', '00000001'])
      self.cms.flush()
      self.assertCMS(self.cms)
      self.assertCMSTar(self.cms, 'db00000.tar',
                        ['00000000msg00000000.gz',
                         '00000001msg00000001.gz',
                         '00000000msg00000002.gz',
                         '00000001msg00000003.gz'])
      self.assertCMSTarData(self.cms, 'db00000.tar',
                            '00000000msg00000000.gz',
                            'art1')
      self.assertCMSTarData(self.cms, 'db00000.tar',
                            '00000001msg00000001.gz',
                            'art2')
      self.assertCMSTarData(self.cms, 'db00000.tar',
                            '00000000msg00000002.gz',
                            'art1r')
      self.assertCMSTarData(self.cms, 'db00000.tar',
                            '00000001msg00000003.gz',
                            'art2r')
      self.assertAid(self.cms,
                     ['00000002',
                      '00000003',
                      '00000000',
                      '00000001'])
      self.cms.close()
      self.cms.validate()
      return
    
    def testLabel(self):
      self.cms.open(mode='w')
      aid = self.cms.create_article('msg', 'text2', labels=('def','abc'))
      self.cms.flush()
      self.assertCMS(self.cms)
      self.assertCMS(self.cms)
      self.assertCMSTar(self.cms, 'db00000.tar',
                        ['00000000msg00000000abc.def.gz'])
      self.assertCMSTarData(self.cms, 'db00000.tar',
                            '00000000msg00000000abc.def.gz',
                            'text2')
      self.assertCMSIdx(self.cms, 'idx00000.cdb',
                        [(1,0), u'text2', 'abc', 'def'])
      self.cms.close()
      self.cms.validate()
      return
  
    def testRandom(self):
      import random
      MAX_DATA_SIZE = 1000
      MAX_ARTICLES = 1000
      RATIO_CREATE_NEW = 10
      def randstr():
        return ''.join( chr(random.randrange(96)+32) for _ in
                        xrange(random.randrange(MAX_DATA_SIZE)) )
      self.cms.open(mode='w')
      arts = {}
      for _ in xrange(MAX_ARTICLES):
        data = randstr()
        if not arts or random.randrange(100) < RATIO_CREATE_NEW:
          aid = self.cms.create_article('msg', data)
        else:
          aid = random.choice(arts.keys())
          tid = self.cms.modify_article(aid, data)
        arts[aid] = data
      self.cms.close()
      self.cms.open(mode='r')
      self.assertCMS(self.cms)
      for aid in arts.iterkeys():
        self.assertEqual(self.cms.get_latest(aid), arts[aid])
      self.cms.close()
      self.cms.validate()
      return
    
  unittest.main()
