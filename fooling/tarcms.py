#!/usr/bin/env python
import sys, os, stat, os.path, time
sys.path.insert(0, '.')
sys.path.insert(0, '..')
stdout = sys.stdout
stderr = sys.stderr


##  TarCMS
##
##   db = TarCMS()
##   db.create()
##   db.open()
##   artid = db.new_article(type='a')
##   snapid = db.modify_content(artid, data)
##   snapid = db.get_snapshot(artid, mtime)
##   db.find_article(query)
##   db.find_snapshot(query)
##   db.get_strand_by_artid(artid)
##   db.get_strand_by_snapid(snapid)
##   db.set_label(artid, labels)
##   db.get_label(artid, labels)
##   db.close()
##
class TarCMS(object):

  def __init__(self, basedir, doctype, encoding, indexstyle=None):
    from fooling.indexdb import IndexDB
    from fooling.corpus import GzipTarDBCorpus
    from fooling.tardb import FixedDB
    self.basedir = basedir
    self.corpus = GzipTarDBCorpus(os.path.join(basedir, 'src'), doctype, encoding,
                                  indexstyle=indexstyle, namelen=8)
    self.artdb = FixedDB(os.path.join(basedir, 'articles'))
    self.indexdb = IndexDB(os.path.join(basedir, 'idx'), 'idx')
    self._loctoindex = set()
    return

  def create(self):
    self.corpus.create()
    self.artdb.create(9)
    self.indexdb.create()
    return

  def open(self, mode='r'):
    self.corpus.open(mode=mode)
    self.artdb.open(mode=mode)
    return

  def close(self):
    self.flush()
    self.corpus.close()
    self.artdb.close()
    return

  def add_data(self, data, name, ext, mtime=0, labels=None):
    loc = self.corpus.add_data(data, name, ext, mtime=mtime, labels=labels)
    self._loctoindex.add(loc)
    return loc

  def add_file(self, path, mtime=None, labels=None):
    (_,ext) = os.path.splitext(path)
    st = os.stat(path)
    fp = file(path, 'rb')
    data = fp.read()
    fp.close()
    if not mtime:
      mtime = st[stat.ST_MTIME]
    return self.add_data(data, ext, mtime=mtime, labels=labels)

  def flush(self, verbose=False, threshold=100, cleanup=True):
    from fooling.indexer import Indexer
    from fooling.merger import Merger
    indexer = Indexer(self.indexdb, self.corpus, verbose=verbose)
    for loc in self._loctoindex:
      indexer.index_loc(loc)
    indexer.finish()
    self._loctoindex.clear()
    Merger(self.indexdb, max_docs_threshold=threshold).run(cleanup=cleanup)
    self.corpus.flush()
    self.artdb.flush()
    return

  def create_article(self, ext, data, mtime=0, labels=None):
    assert len(ext) == 3
    aid = '%08x' % self.artdb.nextrecno()
    loc = self.add_data(data, aid, ext, mtime=mtime, labels=labels)
    assert aid == loc
    self.artdb.add_record(loc)
    return aid

  def modify_article(self, aid, data, mtime=0, labels=None):
    loc0 = self.artdb.get_record(int(aid, 16))
    ext = self.corpus.get_ext(loc0)
    loc = self.add_data(data, aid, ext, mtime=mtime, labels=labels)
    tid = '%08x' % self.artdb.add_record(loc0)
    self.artdb.set_record(int(aid, 16), tid)
    return

  def get_article(self, aid, n=1):
    loc = aid
    while 0 < n:
      loc = self.artdb.get_record(int(loc, 16))
      n -= 1
    return self.get_snapshot(loc)

  def get_snapshot(self, loc):
    return self.corpus.get_data(loc)

  def get_snapshots(self, aid):
    loc = self.artdb.get_record(int(aid, 16))
    r = []
    while aid != loc:
      r.append(loc)
      loc = self.artdb.get_record(int(loc, 16))
    r.append(loc)
    return r

  def find_articles(self, preds, disjunctive=False):
    from fooling.selection import Selection
    sel = Selection(self.indexdb, preds, disjunctive=disjunctive)
    for (_,x) in sel:
      (mtime, loc, title, snippet) = sel.get_snippet(x)
      aid = self.corpus.get_name(loc)
      yield (aid, loc, mtime, title, snippet)
    return


if 1:
  from fooling.document import EMailDocument
  from fooling.selection import KeywordPredicate
  from fooling.pycdb import CDBReader
  import unittest, shutil, tarfile, gzip, random, struct
  encoding = 'euc-jp'
  class TarCMSTest(unittest.TestCase):
    
    def setUp(self):
      dirname = './test.%s/' % self.id()
      try:
        shutil.rmtree(dirname)
      except OSError:
        pass
      self.cms = TarCMS(dirname, EMailDocument, encoding)
      self.cms.create()
      self.cms.open(mode='w')
      return
    
    def tearDown(self):
      self.cms.close()
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
      aid = self.cms.create_article('msg', 'text1')
      self.assertEqual(self.cms.get_article(aid), 'text1')
      self.cms.modify_article(aid, 'mod1 mod1')
      self.assertEqual(self.cms.get_article(aid), 'mod1 mod1')
      self.cms.modify_article(aid, 'mod2.\nmodd')
      self.assertEqual(self.cms.get_article(aid), 'mod2.\nmodd')
      self.cms.flush()
      self.assertEqual(self.cms.get_snapshots(aid),
                       ['00000002', '00000001' , '00000000'])
      self.assertEqual([ (aid,title,loc) for (aid,loc,mtime,title,snippet) in self.cms.find_articles([KeywordPredicate('text1')]) ],
                       [ ('00000000', u'text1', '00000000') ])
      self.assertEqual([ (aid,title,loc) for (aid,loc,mtime,title,snippet) in self.cms.find_articles([KeywordPredicate('modd')]) ],
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
                        [(1,0),(2,0),(3,0),(3,1), u'mod1', u'mod2', u'modd', u'text1'])
      self.assertAid(self.cms,
                     ['00000002',
                      '00000000',
                      '00000001'])
      return
  
    def testArts(self):
      aid1 = self.cms.create_article('msg', 'art1')
      aid2 = self.cms.create_article('msg', 'art2')
      self.cms.modify_article(aid1, 'art1r')
      self.cms.modify_article(aid2, 'art2r')
      self.assertEqual(self.cms.get_article(aid1), 'art1r')
      self.assertEqual(self.cms.get_snapshots(aid1),
                       ['00000002', '00000000'])
      self.assertEqual(self.cms.get_article(aid2), 'art2r')
      self.assertEqual(self.cms.get_snapshots(aid2),
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
      return
    
    def testLabel(self):
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
      return
  
  unittest.main()
