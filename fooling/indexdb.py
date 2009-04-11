#!/usr/bin/env python
##
##  indexdb.py
##

import sys, os, os.path, stat, re
import pycdb as cdb
from util import idx_info, idx_docid2info, idx_loc2docid


__all__ = [
  'IndexDB'
  ]


##  IndexDB
##
class IndexDB(object):

  # Index filename pattern: "xxxNNNNN.cdb"
  IDX_PAT = re.compile(r'^...\d{5}\.cdb$')
  
  def __init__(self, idxdir, prefix=''):
    self.idxdir = idxdir
    self.prefix = prefix
    # mtime: index modification time.
    self.mtime = 0
    # cdb object cache. Should not be pickled.
    self._idxcache = {}
    # All index filenames are grobbed and sorted initially.
    self.refresh()
    return

  def __repr__(self):
    return '<IndexDB: idxdir=%r, prefix=%r>' % (self.idxdir, self.prefix)

  def __getstate__(self):
    # Avoid pickling cdb objects.
    odict = self.__dict__.copy()
    del odict['_idxcache']
    return odict

  def __setstate__(self, dict):
    self.__dict__.update(dict)
    self._idxcache = {}
    return

  # (Internal) Returns a new index file name.
  def gen_idx_fname(self, idxid):
    assert len(self.prefix) == 3
    fname = os.path.join(self.idxdir, '%s%05d.cdb' % (self.prefix, idxid))
    return fname

  # (Internal) Returns an iterator for the index files.
  def iteridxs(self, start=0, end=sys.maxint-1):
    for idxid in xrange(start, min(end+1, len(self.idxs))):
      fname = self.idxs[idxid]
      if fname in self._idxcache:
        idx = self._idxcache[fname]
      else:
        idx = cdb.init(os.path.join(self.idxdir, fname))
        self._idxcache[fname] = idx
      yield (idxid, idx)
    return

  # (Internal) Grab all the index filenames.
  def refresh(self):
    # Reversed lexical order: the latest comes first.
    self.idxs = sorted(( fname for fname in os.listdir(self.idxdir)
                         if fname.startswith(self.prefix) and self.IDX_PAT.match(fname) ),
                         reverse=True)
    if self.idxs:
      self.mtime = os.stat(os.path.join(self.idxdir, self.idxs[0]))[stat.ST_MTIME]
    self._idxcache.clear()
    return

  # Resets the internal list and ignore all the existing index files.
  def reset(self):
    self.idxs = []
    self._idxcache.clear()
    return

  # Returns the modification time of the indices.
  def index_mtime(self):
    return self.mtime

  # Returns the last location indexed.
  def index_lastloc(self):
    lastloc = None
    for (_,idx) in self.iteridxs():
      (ndocs,_) = idx_info(idx)
      (_,lastloc) = idx_docid2info(idx, ndocs-1)
      # the first index must be newest, so we stop here.
      break
    return lastloc

  # Returns the total number of documents indexed.
  def total_docs(self):
    total = 0
    for (_,idx) in self.iteridxs():
      (ndocs,_) = idx_info(idx)
      total += ndocs
    return total

  # Returns (i,docid) if the location is already indexed.
  def loc_indexed(self, loc):
    for (idxid,idx) in self.iteridxs():
      try:
        return (idxid, idx_loc2docid(idx, loc))
      except KeyError:
        pass
    return None
