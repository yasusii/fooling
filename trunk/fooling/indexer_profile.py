#!/usr/bin/env python
import sys
from indexer import index
stderr = sys.stderr

if __name__ == '__main__':
  import hotshot, hotshot.stats
  prof = hotshot.Profile('indexer.prof')
  prof.runcall(lambda : index(sys.argv))
  prof.close()
  stats = hotshot.stats.load('indexer.prof')
  stats.strip_dirs()
  stats.sort_stats('time', 'calls')
  stats.print_stats(100)
  
