#!/usr/bin/env python
import sys, time
import pycdb as cdb
from struct import pack
from array import array
from util import isplit, encodew, encode_array
stderr = sys.stderr


__all__ = [ 'Indexer' ]


##  Indexer
##
class Indexer:
  
  def __init__(self, corpus,
               max_docs_threshold=2000,
               max_terms_threshold=50000,
               verbose=0):
    assert len(corpus.prefix) == 3
    self.corpus = corpus
    self.idx_count = len(self.corpus.idxs)
    self.max_docs_threshold = max_docs_threshold
    self.max_terms_threshold = max_terms_threshold
    self.verbose = verbose
    # (docid,loc) mappings in the current index.
    # docid is local to each index.
    self.docid2loc = []
    # terms indexed in the current index.
    self.terms = {}
    return

  # Adds a new index file.
  def new_idx(self):
    fname = self.corpus.gen_idx_fname(self.idx_count)
    self.idx_count += 1
    m = cdb.cdbmake(fname, fname+'.tmp')
    return (fname, m)

  # Index a new Document at a given location.
  def index_doc(self, loc, maxpos=1000000, titleonly=False, indexyomi=False):
    doc = self.corpus.get_doc(loc)
    if not doc: return False
    docid = len(self.docid2loc)
    self.docid2loc.append((pack('>i', docid), loc))
    if 2 <= self.verbose:
      print >>stderr, 'Reading: %r' % doc
    elif 1 <= self.verbose:
      stderr.write('.'); stderr.flush()
    terms = self.terms
    if titleonly:
      get_terms = [(0, doc.get_title())]
    else:
      if indexyomi:
        from yomi import index_yomi
        def splitterms(s):
          for x in isplit(s):
            yield encodew(x)
          for x in index_yomi(s):
            yield '\x05'+x
          return
      else:
        def splitterms(s):
          for x in isplit(s):
            yield encodew(x)
          return
      get_terms = doc.get_terms(splitterms, maxpos)
    for (pos, words) in get_terms:
      for w in words:
        if w not in terms:
          occs = []
          terms[w] = occs
        else:
          occs = terms[w]
        occs.append((docid, pos))
    if ((self.max_docs_threshold and self.max_docs_threshold < len(self.docid2loc)) or 
        (self.max_terms_threshold and self.max_terms_threshold < len(terms))):
      self.flush()
    return True

  # Build a cdb file.
  def flush(self):
    if not self.docid2loc: return
    (fname, m) = self.new_idx()
    if self.verbose:
      print >>stderr, 'Building index %r(%d)...' % (fname, len(self.docid2loc))
      t0 = time.time()
    # All keys must be lexically sorted except the last one.
    # DocID -> location.
    self.docid2loc.sort(key=lambda (docid,loc): docid)
    for (docid,loc) in self.docid2loc:
      m.add('\x00'+docid, loc)
    # Term -> pos.
    nrefs = 0
    for w in sorted(self.terms.iterkeys()):
      occs = self.terms[w]
      occs.sort(reverse=True)
      a = array('i')
      for (docid,pos) in occs:
        a.append(docid)
        a.append(pos)
      m.add(w, encode_array(len(occs), a))
      nrefs += len(occs)
    # location -> DocID
    self.docid2loc.sort(key=lambda (docid,loc): loc)
    for (docid,loc) in self.docid2loc:
      m.add('\xff'+loc, docid)
    # The number of documents
    m.add('', pack('>ii', len(self.docid2loc), len(self.terms)))
    m.finish()
    if self.verbose:
      t = time.time() - t0
      print >>stderr, 'docs=%d, keys=%d, refs=%d, time=%.1fs(%.1fdocs/s)' % \
            (len(self.docid2loc), len(self.terms), nrefs, t, len(self.docid2loc)/t)
    # Clear the files and terms.
    self.docid2loc = []
    self.terms.clear()
    return

  def finish(self):
    self.flush()
    self.corpus.refresh()
    return


##  index
##
def index(argv):
  import getopt, locale
  import document
  from corpus import FilesystemCorpus
  def usage():
    print 'usage: %s [-v] [-F|-N|-R] [-Y] [-b basedir] [-p prefix] [-t doctype] [-e encoding] [-D maxdocs] [-T maxterms] idxdir [file ...]' % argv[0]
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(argv[1:], 'vFRNYb:p:t:e:D:T:')
  except getopt.GetoptError:
    usage()
  verbose = 1
  mode = 0
  basedir = ''
  prefix = 'idx'
  doctype = document.PlainTextDocument
  encoding = locale.getdefaultlocale()[1] or 'euc-jp'
  maxdocs = 2000
  maxterms = 50000
  indexyomi = False
  for (k, v) in opts:
    if k == '-d': verbose += 1
    elif k == '-F': mode = 1
    elif k == '-N': mode = 2
    elif k == '-R': mode = 3
    elif k == '-Y': indexyomi = True
    elif k == '-b': basedir = v
    elif k == '-p': prefix = v
    elif k == '-t': doctype = getattr(document, v)
    elif k == '-e': encoding = v
    elif k == '-D': maxdocs = int(v)
    elif k == '-T': maxterms = int(v)
  if not args: usage()
  assert len(prefix) == 3
  idxdir = args[0]
  corpus = FilesystemCorpus(basedir, idxdir, prefix, doctype, encoding)
  corpus.open()
  if mode == 3:
    corpus.reset()
  indexer = Indexer(corpus, maxdocs, maxterms, verbose=verbose)
  print >>stderr, \
        'Index: basedir=%r, idxdir=%r, max_docs_threshold=%d, max_terms_threshold=%d ' % \
        (basedir, idxdir, maxdocs, maxterms)

  files = args[1:]
  lastmod = corpus.index_mtime()
  if not files:
    files = sys.stdin
  for fname in files:
    fname = fname.strip()
    if not corpus.loc_exists(fname): continue
    if (mode == 2) and corpus.loc_indexed(fname): continue
    if (mode == 0) and corpus.loc_mtime(fname) < lastmod: continue
    indexer.index_doc(fname, indexyomi=indexyomi)

  indexer.finish()
  print >>stderr, 'Done.'
  return

if __name__ == '__main__': index(sys.argv)
