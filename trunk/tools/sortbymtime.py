#!/usr/bin/env python
import sys, os, os.path, stat, fileinput
stderr = sys.stderr

def main(args):
  files = []
  for fname in fileinput.input(args):
    fname = fname.strip()
    if not os.path.exists(fname):
      print >>stderr, 'File does not exist: %r' % fname
      continue
    files.append((os.stat(fname)[stat.ST_MTIME], fname))
  for (_,fname) in sorted(files):
    print fname
  return

if __name__ == "__main__": main(sys.argv[1:])

