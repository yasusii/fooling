#!/usr/bin/env python
import sys, os, stat, os.path, time, re
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
class TarCMS(object):

  def __init__(self, basedir, doctype, encoding, indexstyle=None):
    from fooling.indexdb import IndexDB
    from fooling.corpus import GzipTarDBCorpus
    from fooling.tardb import FixedDB
    self.corpus = GzipTarDBCorpus(os.path.join(basedir, 'src'), doctype, encoding, indexstyle)
    self.artdb = FixedDB(os.path.join(basedir, 'articles'))
    self.indexdb = IndexDB(os.path.join(basedir, 'idx'), 'idx')
    self._loctoindex = set()
    return

  def create(self):
    self.corpus.create()
    self.artdb.create(32)
    self.indexdb.create()
    return

  def open(self, mode='r'):
    self.corpus.open(mode=mode)
    self.artdb.open(mode=mode)
    return

  def close(self):
    self.corpus.close()
    self.artdb.close()
    return

  def add_data(self, data, name, mtime=0, labels=None):
    loc = self.corpus.add_doc(data, name, mtime=mtime, labels=labels)
    self._loctoindex.add(loc)
    return loc

  def add_file(self, path, mtime=None):
    (_,ext) = os.path.splitext(path)
    st = os.stat(path)
    fp = file(path, 'rb')
    data = fp.read()
    fp.close()
    if not mtime:
      mtime = st[stat.ST_MTIME]
    return self.add_data(data, ext, mtime)

  def flush(self, verbose=False, threshold=100, cleanup=True):
    from fooling.indexer import Indexer
    from fooling.merger import Merger
    indexer = Indexer(self.indexdb, self.corpus, verbose=verbose)
    for loc in self._loctoindex:
      indexer.index_loc(loc)
    indexer.finish()
    self._loctoindex.clear()
    Merger(self.indexdb, max_docs_threshold=threshold).run(cleanup=cleanup)
    return

  def create_article(self, data, ext, mtime=0, labels=None):
    aid = self.artdb.nextrecno()
    name = '%08x.%s' % (aid,ext)
    loc = self.add_data(data, name, mtime=mtime, labels=labels)
    self.artdb.add_record(loc+'.'+name)
    print (loc,name)
    return aid

  REC_PAT = re.compile(r'^([^.]*)\.([^.]*)\.(.*)$')
  def modify_article(self, aid, data, mtime=0, labels=None):
    m = self.REC_PAT.match(self.artdb.get_record(aid))
    loc = self.add_data(data, '%s.%s' % (m.group(2), m.group(3)), mtime=mtime, labels=labels)
    tid = self.artdb.add_record('%s.%s.%s' % (loc, m.group(2), m.group(3)))
    self.artdb.set_record(aid, '%s.%08x.%s' % (m.group(1), tid, m.group(3)))
    return
    

if 1:
  from fooling.document import EMailDocument
  import unittest, shutil
  dirname = './test_tarcms/'
  encoding = 'euc-jp'
  class TarCMSTest(unittest.TestCase):
    
    def setUp(self):
      self.cms = TarCMS(dirname, EMailDocument, encoding)
      self.cms.create()
      self.cms.open(mode='w')
      return
    def tearDown(self):
      self.cms.close()
      shutil.rmtree(dirname)
      self.cms = None
      return

    def testBasic(self):
      aid = self.cms.create_article('foo', 'hoge.msg')
      self.cms.modify_article(aid, 'bar')
      return
  
  unittest.main()
