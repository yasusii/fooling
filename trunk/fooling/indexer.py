#!/usr/bin/env python
##
##  indexer.py
##

import sys, time
from struct import pack
from array import array
from util import encode_array, zen2han, rmsp, \
     PROP_SENT, PROP_DOCID, PROP_LOC, PROP_INFO
from indexdb import IndexDB
stderr = sys.stderr


__all__ = [
  'Indexer'
  ]


def add_features(terms, docid, sentid, feats):
  for w in feats:
    if w not in terms:
      occs = []
      terms[w] = occs
    else:
      occs = terms[w]
    occs.append((docid, sentid))
  return

def linux_process_memory():
  v = None
  try:
    fp = file('/proc/self/status')
    for line in fp:
      if line.startswith('VmRSS:'):
        v = line[6:].strip()
    fp.close()
  except IOError:
    pass
  return v
  


##  Indexer
##
class Indexer(object):
  
  def __init__(self, indexdb, corpus, 
               max_docs_threshold=1000,
               max_terms_threshold=50000,
               verbose=0):
    assert len(indexdb.prefix) == 3
    self.indexdb = indexdb
    self.corpus = corpus
    self.idx_count = len(self.indexdb.idxs)
    self.max_docs_threshold = max_docs_threshold
    self.max_terms_threshold = max_terms_threshold
    self.verbose = verbose
    # (docid,doc) mappings in the current index.
    # docid is local to each index.
    self.docinfo = []
    # terms indexed in the current index.
    self.terms = {}
    # cdbmaker
    self.maker = None
    return

  # Adds a new index file.
  def create_new_idx(self):
    (fname, self.maker) = self.indexdb.add_idx(self.idx_count)
    self.idx_count += 1
    if self.verbose:
      print >>stderr, 'Building index %r(%d)...' % (fname, self.idx_count)
    return

  # Index a new Document at a given location.
  def index_loc(self, loc, maxsents=100000):
    doc = self.corpus.get_doc(loc)
    if not doc: return False
    return self.index_doc(doc, maxsents=maxsents)
  
  def index_doc(self, doc, maxsents=100000):
    if self.maker == None:
      self.create_new_idx()
    docid = len(self.docinfo)+1
    self.docinfo.append((docid, doc))
    if 2 <= self.verbose:
      print >>stderr, 'Reading: %r' % doc
    elif 1 <= self.verbose:
      stderr.write('.'); stderr.flush()
    terms = self.terms
    # other features
    add_features(terms, docid, 0, self.corpus.loc_feats(doc.loc))
    add_features(terms, docid, 0, doc.get_feats())
    # sents
    sentid = 0
    title = doc.get_title()
    if title:
      title = zen2han(rmsp(title))
      self.maker.add(pack('>cii', PROP_SENT, docid, sentid), title.encode('utf-8'))
      add_features(terms, docid, sentid, set(doc.splitterms(title)))
      sentid += 1
    for sent in doc.get_sents():
      sent = zen2han(rmsp(sent))
      if not sent: continue
      self.maker.add(pack('>cii', PROP_SENT, docid, sentid), sent.encode('utf-8'))
      add_features(terms, docid, sentid, set(doc.splitterms(sent)))
      sentid += 1
      if maxsents <= sentid: break
    if ((self.max_docs_threshold and self.max_docs_threshold <= len(self.docinfo)) or 
        (self.max_terms_threshold and self.max_terms_threshold <= len(terms))):
      self.flush()
    for subdoc in doc.get_subdocs():
      if subdoc:
        self.index_doc(subdoc, maxsents=maxsents)
    return True

  # Build a cdb file.
  def flush(self):
    if not self.docinfo: return
    assert self.maker
    t0 = time.time()
    # All keys must be lexically sorted except the last one.
    # DocID -> Document.
    self.docinfo.sort(key=lambda (docid,_): docid)
    # Term -> pos.
    nrefs = 0
    for w in sorted(self.terms.iterkeys()):
      occs = self.terms[w]
      occs.sort(reverse=True)
      a = array('i')
      for (docid,pos) in occs:
        a.append(docid)
        a.append(pos)
      self.maker.add(w, encode_array(len(occs), a))
      nrefs += len(occs)
    # location -> DocID
    for (docid,doc) in self.docinfo:
      self.maker.add(pack('>ci', PROP_DOCID, docid), pack('>i', doc.get_mtime())+doc.loc)
    self.docinfo.sort(key=lambda (_,doc): doc.loc)
    # DocID -> location
    for (docid,doc) in self.docinfo:
      self.maker.add(PROP_LOC+doc.loc, pack('>i', docid))
    # The number of documents
    self.maker.add(PROP_INFO, pack('>ii', len(self.docinfo), len(self.terms)))
    self.maker.finish()
    self.maker = None
    if self.verbose:
      t = time.time() - t0
      print >>stderr, 'docs=%d, keys=%d, refs=%d, time=%.1fs(%.1fdocs/s), memory=%s' % \
            (len(self.docinfo), len(self.terms), nrefs, t, len(self.docinfo)/t,
             linux_process_memory())
    # Clear the files and terms.
    self.docinfo = []
    self.terms.clear()
    return

  def finish(self):
    self.flush()
    self.indexdb.refresh()
    return


##  index
##
def index(argv):
  import getopt, locale
  import document, corpus
  def usage():
    print 'usage: %s [-v] [-F|-N|-R] [-Y] [-b basedir] [-p prefix] [-c corpustype] [-t doctype] [-e encoding] [-D maxdocs] [-T maxterms] idxdir [file ...]' % argv[0]
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(argv[1:], 'vFRNYb:p:c:t:e:D:T:')
  except getopt.GetoptError:
    usage()
  verbose = 1
  mode = 0
  basedir = ''
  prefix = 'idx'
  corpustype = corpus.FilesystemCorpus
  doctype = document.PlainTextDocument
  encoding = locale.getpreferredencoding()
  maxdocs = 1000
  maxterms = 50000
  indexstyle = 'normal'
  for (k, v) in opts:
    if k == '-d': verbose += 1
    elif k == '-F': mode = 1
    elif k == '-N': mode = 2
    elif k == '-R': mode = 3
    elif k == '-Y': indexstyle = 'yomi'
    elif k == '-b': basedir = v
    elif k == '-p': prefix = v
    elif k == '-c': corpustype = getattr(corpus, v)
    elif k == '-t': doctype = document.get_doctype(v)
    elif k == '-e': encoding = v
    elif k == '-D': maxdocs = int(v)
    elif k == '-T': maxterms = int(v)
  if not args: usage()
  assert len(prefix) == 3
  idxdir = args[0]
  corpus = corpustype(basedir, doctype, encoding, indexstyle)
  corpus.open()
  indexdb = IndexDB(idxdir, prefix)
  if mode == 3:
    indexdb.reset()
  indexer = Indexer(indexdb, corpus, maxdocs, maxterms, verbose=verbose)
  print >>stderr, \
        'Index: basedir=%r, idxdir=%r, max_docs_threshold=%d, max_terms_threshold=%d ' % \
        (basedir, idxdir, maxdocs, maxterms)

  files = args[1:]
  lastmod = indexdb.index_mtime()
  if not files:
    files = sys.stdin
  for fname in files:
    fname = fname.strip()
    if not corpus.loc_exists(fname): continue
    if (mode == 2) and corpus.loc_indexed(fname): continue
    if (mode == 0) and corpus.loc_mtime(fname) < lastmod: continue
    indexer.index_loc(fname)

  indexer.finish()
  print >>stderr, 'Done.'
  return

if __name__ == '__main__': index(sys.argv)
