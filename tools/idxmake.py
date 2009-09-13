#!/usr/bin/env python
import sys
from fooling import document, corpus
from fooling.indexdb import IndexDB
from fooling.indexer import Indexer


##  index
##
def index(argv):
  import getopt, locale
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
  cps = corpustype(basedir, doctype, encoding, indexstyle)
  cps.open()
  indexdb = IndexDB(idxdir, prefix)
  try:
    indexdb.create()
  except IndexDB.IndexDBError:
    pass
  indexdb.open()
  if mode == 3:
    indexdb.reset()
  indexer = Indexer(indexdb, cps, maxdocs, maxterms, verbose=verbose)
  print >>sys.stderr, \
        'Index: basedir=%r, idxdir=%r, max_docs_threshold=%d, max_terms_threshold=%d ' % \
        (basedir, idxdir, maxdocs, maxterms)

  files = args[1:]
  lastmod = indexdb.index_mtime()
  if not files:
    files = sys.stdin
  for fname in files:
    fname = fname.strip()
    print fname
    if not cps.loc_exists(fname): continue
    if (mode == 0) and cps.loc_mtime(fname) < lastmod: continue
    if (mode == 2) and indexdb.loc_indexed(fname): continue
    indexer.index_loc(fname)

  indexer.finish()
  print >>sys.stderr, 'Done.'
  return

if __name__ == '__main__': index(sys.argv)
