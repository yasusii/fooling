#!/usr/bin/env python
import sys
from fooling.indexdb import IndexDB
from fooling.merge import Merger


##  merge
##
def merge(argv):
  import getopt
  def usage():
    print 'usage: %s [-v] [-p prefix] [-D maxdocs] [-T maxterms] idxdir' % argv[0]
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(argv[1:], 'vp:D:T:')
  except getopt.GetoptError:
    usage()
  (verbose, prefix, max_docs_threshold, max_terms_threshold) = (1, 'idx', 2000, 50000)
  for (k, v) in opts:
    if k == '-v': verbose += 1
    elif k == '-p': prefix = v
    elif k == '-D': max_docs_threshold = int(v)
    elif k == '-T': max_terms_threshold = int(v)
  if not args: usage()
  assert len(prefix) == 3
  idxdir = args[0]
  indexdb = IndexDB(idxdir, prefix)
  indexdb.open()
  Merger(indexdb, max_docs_threshold, max_terms_threshold, verbose).run()
  return

# main
if __name__ == "__main__": merge(sys.argv)
