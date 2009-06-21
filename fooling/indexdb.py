#!/usr/bin/env python
##
##  indexdb.py
##

import sys, os, os.path, stat, re
import fooling.pycdb as cdb
from fooling.util import idx_info, idx_docid2info, idx_loc2docid


__all__ = [
  'IndexDB'
  ]


##  IndexDB
##
class IndexDB(object):

  class IndexDBError(Exception): pass

  # Index filename pattern: "xxxNNNNN.cdb"
  IDX_PAT = re.compile(r'^...\d{5}\.cdb$')
  
  # cdb object cache. Shared among all instances.
  _cdb_cache = {}
  @classmethod
  def get_idx(klass, path):
    if path in klass._cdb_cache:
      idx = klass._cdb_cache[path]
    else:
      idx = cdb.init(path)
      klass._cdb_cache[path] = idx
    return idx

  def __init__(self, idxdir, prefix=''):
    self.idxdir = idxdir
    self.prefix = prefix
    self.reset()
    return

  def __repr__(self):
    return '<IndexDB: idxdir=%r, prefix=%r>' % (self.idxdir, self.prefix)

  # Resets the internal list and ignore all the existing index files.
  def reset(self):
    self.mtime = 0
    self.idxs = []
    return

  def open(self):
    # All index filenames are grobbed and sorted initially.
    self.refresh()
    return

  def close(self):
    self.reset()
    return

  def create(self):
    try:
      os.makedirs(self.idxdir)
    except OSError:
      raise IndexDB.IndexDBError('cannot create directory: %r' % self.idxdir)
    return

  # (Internal) Returns a new cdb name.
  def gen_idx_fname(self, idxid):
    assert len(self.prefix) == 3
    return os.path.join(self.idxdir, '%s%05d.cdb' % (self.prefix, idxid))
  
  # (Internal) Returns a new cdb maker.
  def add_idx(self, idxid):
    fname = self.gen_idx_fname(idxid)
    maker = cdb.cdbmake(fname, fname+'.tmp')
    return (fname, maker)

  # (Internal) Returns an iterator for the index files.
  def iteridxs(self, start=0, end=sys.maxint-1):
    for idxid in xrange(start, min(end+1, len(self.idxs))):
      fname = os.path.join(self.idxdir, self.idxs[idxid])
      idx = self.get_idx(fname)
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
