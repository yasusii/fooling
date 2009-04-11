#!/usr/bin/env python
import sys, re
stderr = sys.stderr
p=re.compile(r'\S', re.UNICODE)

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
  basedir = ''
  prefix = 'idx'
  doctype = document.PlainTextDocument
  encoding = locale.getpreferredencoding()
  for (k, v) in opts:
    if k == '-d': verbose += 1
    elif k == '-b': basedir = v
    elif k == '-p': prefix = v
    elif k == '-t': doctype = getattr(document, v)
    elif k == '-e': encoding = v
  assert len(prefix) == 3
  corpus = FilesystemCorpus(basedir, '/tmp', prefix, doctype, encoding)
  corpus.open()
  for fname in args:
    doc = corpus.get_doc(fname)
    n = 0
    c = 0
    for (pos,sent) in doc.get_sents(0):
      n += 1
      c += len(p.findall(sent))
    print fname, n, c
  return

if __name__ == '__main__': index(sys.argv)
