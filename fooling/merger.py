#!/usr/bin/env python
##
##  merger.py
##

import sys, os, os.path
from array import array
from struct import pack, unpack
import fooling.pycdb as cdb
from fooling.util import encode_array, decode_array, idx_info, \
     PROP_SENT, PROP_DOCID, PROP_LOC, PROP_INFO
stderr = sys.stderr


__all__ = [
  'Merger'
  ]


# Estimate the number of unique terms:
# assuming roughly 25% of the words are common.
def estimate_terms(nterms):
  return reduce(lambda r,n: r + max(n - int(r*0.25), 0), nterms, 0)


##  IndexFile
##
class IndexFile(object):
  
  def __init__(self, fname):
    self.fname = fname
    self.cdb = cdb.init(fname)
    (self.ndocs, self.nterms) = idx_info(self.cdb)
    return

  def __repr__(self):
    return '<%s (docs=%d, terms=%d)>' % (self.fname, self.ndocs, self.nterms)

  def assignnewids1(self, newids):
    self.oldids = []
    for (k,v) in self.cdb.iteritems(startkey=pack('>ci', PROP_DOCID, 1)):
      if k[0] == PROP_LOC: break
      loc = v[4:]
      if loc in newids: continue
      (oldid,) = unpack('>xi', k)
      self.oldids.append((oldid, loc))
    #assert self.ndocs == len(self.oldids), (self.ndocs, self.oldids)
    for (oldid,loc) in sorted(self.oldids, reverse=True):
      newid = len(newids)
      newids[loc] = newid
    return
  def assignnewids2(self, newids):
    self.old2new = {}
    for (oldid,loc) in self.oldids:
      self.old2new[oldid] = newids[loc]
    return

  def copysents(self, maker):
    for (k,v) in self.cdb.iteritems():
      if k[0] != PROP_SENT: break
      (oldid, pos) = unpack('>xii', k)
      if oldid in self.old2new:
        maker.add(pack('>cii', PROP_SENT, self.old2new[oldid], pos), v)
    else:
      raise ValueError('empty index')
    self.next = self.cdb.iteritems(startkey=k).next
    return

  def convertoldids(self, bits):
    a = decode_array(bits)
    r = array('i')
    for i in xrange(0, len(a), 2):
      if a[i] in self.old2new:
        r.append(self.old2new[a[i]])
        r.append(a[i+1])
    return r


# cdbmerge
def cdbmerge(idxs):
  q = []
  for idx in idxs:
    try:
      q.append((idx.next(), idx))
    except StopIteration:
      pass
  k0 = None
  vs = None
  while q:
    q.sort()
    ((k,v), idx) = q.pop(0)
    if k0 != k:
      if vs: yield (k0,vs)
      vs = []
    vs.append((v, idx))
    k0 = k
    try:
      q.append((idx.next(), idx))
    except StopIteration:
      continue
  if vs: yield (k0,vs)
  return


##  idxmerge
##
##  idxs: a list of indices to merge (the oldest index first).
##
def idxmerge(cdbname, idxstomerge, verbose=0):
  # Count all the unique locations and assign new document ids.
  idxorder = {}
  loc2docid = {}
  for (i,idx) in enumerate(reversed(idxstomerge)):
    idx.assignnewids1(loc2docid)
    idxorder[idx] = i
  n = len(loc2docid)
  loc2docid = dict( (loc,n-docid) for (loc,docid) in loc2docid.iteritems() )
  for idx in idxstomerge:
    idx.assignnewids2(loc2docid)
  # Create a new index file.
  maker = cdb.cdbmake(cdbname, cdbname+'.tmp')
  if verbose:
    print >>stderr, 'Merging: %r (docs=%d, est. terms=%d): %r' % \
          (cdbname, sum( idx.ndocs for idx in idxstomerge ),
           estimate_terms( idx.nterms for idx in idxstomerge ), idxstomerge)
  # Copy sentences to a new index file with unique ids.
  for idx in idxstomerge:
    idx.copysents(maker)
  # Merge document ids and offsets.
  nterms = 0
  docid2info = []
  for (k,vs) in cdbmerge(idxstomerge):
    if k[0] == PROP_LOC or k[0] == PROP_INFO: break
    if k[0] == PROP_DOCID: 
      # read a docid->loc mapping
      (oldid,) = unpack('>xi', k)
      for (info,idx) in vs:
        if oldid not in idx.old2new: continue
        newid = idx.old2new[oldid]
        docid2info.append((newid, info))
        assert loc2docid[info[4:]] == newid
    else:
      # merge docid+pos sets
      vs = sorted(( (idxorder[idx], idx.convertoldids(v)) for (v,idx) in vs ))
      ents = sum( len(a) for (_,a) in vs )/2
      (_,r) = vs.pop(0)
      for (_,a) in vs:
        r.extend(a)
      maker.add(k, encode_array(ents, r))
      nterms += 1
      if verbose and nterms % 1000 == 0:
        sys.stderr.write('.'); sys.stderr.flush()

  # write docid->loc mappings (avoiding dupes)
  docid2info.sort()
  for (docid,info) in docid2info:
    maker.add(pack('>ci', PROP_DOCID, docid), info)
  # write loc->docid mappings (avoiding dupes)
  for (loc,docid) in sorted(loc2docid.iteritems()):
    if loc:
      maker.add(PROP_LOC+loc, pack('>i', docid))

  if verbose:
    print >>stderr, 'done: docs=%d, terms=%d' % (len(docid2info), nterms)
  maker.add(PROP_INFO, pack('>ii', len(docid2info), nterms))
  maker.finish()
  return


##  Merger
##
class Merger(object):

  def __init__(self, indexdb,
               max_docs_threshold=2000,
               max_terms_threshold=50000,
               verbose=0):
    self.indexdb = indexdb
    self.max_docs_threshold = max_docs_threshold
    self.max_terms_threshold = max_terms_threshold
    self.verbose = verbose
    return

  def flush(self, idxid, idxstomerge):
    if not idxstomerge: return
    fname = self.indexdb.gen_idx_fname(idxid)
    if 1 < len(idxstomerge):
      idxmerge(fname+'.new', idxstomerge, self.verbose)
      for idx in idxstomerge:
        os.rename(idx.fname, idx.fname+'.bak')
      os.rename(fname+'.new', fname)
    elif idxstomerge[0].fname == fname:
      if self.verbose:
        print >>stderr, 'Remain: %r' % (fname)
    else:
      os.rename(idxstomerge[0].fname, fname)
      if self.verbose:
        print >>stderr, 'Rename: %r <- %r' % (fname, idxstomerge[0].fname)
    return

  def run(self, cleanup=False):
    # idxs: a list of indices (the oldest index comes first).
    idxs = [ IndexFile(os.path.join(self.indexdb.idxdir, fname)) for fname in reversed(self.indexdb.idxs) ]
    ndocs = 0
    nterms = []
    newidx = 0
    idxstomerge = []
    for idx in idxs:
      if ((self.max_docs_threshold and self.max_docs_threshold < ndocs) or
          (self.max_terms_threshold and self.max_terms_threshold < estimate_terms(nterms))):
        self.flush(newidx, idxstomerge)
        newidx += 1
        idxstomerge = []
        ndocs = 0
        nterms = []
      ndocs += idx.ndocs
      nterms.append(idx.nterms)
      idxstomerge.append(idx)
    self.flush(newidx, idxstomerge)
    if cleanup:
      for fname in os.listdir(self.indexdb.idxdir):
        if fname.endswith('.cdb.bak'):
          fname = os.path.join(self.indexdb.idxdir, fname)
          if self.verbose:
            print >>stderr, 'Removing: %r' % fname
          os.unlink(fname)
    self.indexdb.refresh()
    return


##  merge
##
def merge(argv):
  import getopt
  from fooling.indexdb import IndexDB
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
