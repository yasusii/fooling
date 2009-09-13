#!/usr/bin/env python
import sys
from fooling import document
from fooling.indexdb import IndexDB
from fooling.selection import Selection, SearchTimeout, \
     KeywordPredicate, YomiKeywordPredicate, \
     StrictKeywordPredicate, EMailPredicate


##  search
##
def show_results(selection, n, encoding, timeout=0):
  def e(s): return s.encode(encoding, 'replace')
  window = []
  for (found,loc) in selection.iter(timeout=timeout):
    (mtime, loc, title, s) = selection.get_snippet(loc,
                                                   highlight=lambda x: '\033[31m%s\033[m' % x,
                                                   maxchars=200, maxlr=100)
    print '%d: [%s] %s' % (found+1, e(title or 'unknown'), e(s))
    window.append(found)
    if len(window) == n: break
  (finished, estimated) = selection.status()
  if not window:
    print 'Not found.'
  else:
    print '%d-%d' % (window[0]+1, window[-1]+1),
    if finished:
      print 'of %d results.' % estimated
    else:
      print 'of about %d results.' % estimated
  return

def save_selection(fname, selection):
  import pickle
  print 'Saving the selection: %r' % fname
  fp = file(fname, 'wb')
  pickle.dump(selection, fp)
  fp.close()
  return

def load_selection(fname):
  import pickle
  print 'Loading the selection: %r' % fname
  fp = file(fname, 'rb')
  selection = pickle.load(fp)
  fp.close()
  return selection

def search(argv):
  import getopt, locale, time
  def usage():
    print ('usage: %s [-d] [-T timeout] [-s|-Y] [-S] [-D] [-a] '
           '[-c savefile] [-b basedir] [-p prefix] [-t doctype] '
           '[-e encoding] [-n results] idxdir [keyword ...]') % argv[0]
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(argv[1:], 'dT:sYSDac:b:p:t:e:n:')
  except getopt.GetoptError:
    usage()
  debug = 0
  timeout = 0
  safe = True
  stat = False
  disjunctive = False
  savefile = ''
  basedir = ''
  prefix = ''
  doctype = document.PlainTextDocument
  predtype = KeywordPredicate
  encoding = locale.getpreferredencoding()
  n = 10
  for (k, v) in opts:
    if k == '-d': debug += 1
    elif k == '-T': timeout = int(v)
    elif k == '-S': safe = False
    elif k == '-D': disjunctive = True
    elif k == '-a': stat = True
    elif k == '-Y': predtype = YomiKeywordPredicate
    elif k == '-s': predtype = StrictKeywordPredicate
    elif k == '-c': savefile = v
    elif k == '-b': basedir = v
    elif k == '-p': prefix = v
    elif k == '-t': doctype = getattr(document, v)
    elif k == '-e': encoding = v
    elif k == '-n': n = int(v)

  if doctype == document.EMailDocument:
    predtype = EMailPredicate

  t0 = time.time()
  if args:
    idxdir = args[0]
    keywords = args[1:]
    indexdb = IndexDB(idxdir, prefix)
    indexdb.open()
    preds = [ predtype(unicode(kw, encoding)) for kw in keywords ]
    selection = Selection(indexdb, preds, safe=safe, disjunctive=disjunctive)
    try:
      show_results(selection, n, encoding, timeout)
    except SearchTimeout:
      print 'SearchTimeout.'
  elif savefile:
    selection = load_selection(savefile)
    try:
      show_results(selection, n, encoding, timeout)
    except SearchTimeout:
      print 'SearchTimeout.'
  else:
    usage()
  
  if savefile:
    save_selection(savefile, selection)

  if stat:
    print '%.2f sec, %d/%d hit' % (time.time()-t0, len(selection.found_docs), selection.narrowed)
  return

# main
if __name__ == '__main__': search(sys.argv)
