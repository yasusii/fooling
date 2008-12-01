#!/usr/bin/env python
import sys, os, os.path, stat, fileinput
stderr = sys.stderr

def main(argv):
  import getopt
  def usage():
    print 'usage: %s [-b basedir] [-r] [file ...]' % argv[0]
    return 100
  try:
    (opts, args) = getopt.getopt(argv[1:], 'b:r')
  except getopt.GetoptError:
    return usage()
  basedir = None
  rev = False
  for (k, v) in opts:
    if k == '-b': basedir = v
    elif k == '-r': rev = True
  files = []
  for fname in fileinput.input(args):
    fname = fname.strip()
    if basedir:
      path = os.path.join(basedir, fname)
    else:
      path = fname
    if not os.path.exists(path):
      print >>stderr, 'File does not exist: %r' % path
      continue
    files.append((os.stat(path)[stat.ST_MTIME], fname))
  for (_,fname) in sorted(files, reverse=rev):
    print fname
  return

if __name__ == '__main__': sys.exit(main(sys.argv))
