#!/usr/bin/env python
import sys, os, os.path
import pycdb as cdb
from util import encode_array, decode_array, idx_info, \
     PROP_SENT, PROP_DOCID, PROP_LOC, PROP_INFO
from struct import pack, unpack
stderr = sys.stderr

__all__ = [ 'Merger' ]


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
    self.offset = 0L
    self.key = None
    self.iter = None
    return

  def __repr__(self):
    return '<%s (docs=%d, terms=%d)>' % (self.fname, self.ndocs, self.nterms)

  def iteritems(self):
    self.iter = self.cdb.iteritems(startkey=self.key)
    return self.iter


# cdbmerge
def cdbmerge(idxs):
  q = []
  for idx in idxs:
    try:
      idx.iteritems()
      q.append((idx.iter.next(), idx))
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
      q.append((idx.iter.next(), idx))
    except StopIteration:
      continue
  if vs: yield (k0,vs)
  return


##  idxmerge
##
def idxmerge(cdbname, idxs, verbose=0):
  maker = cdb.cdbmake(cdbname, cdbname+'.tmp')
  offset = 0L
  for idx in idxs:
    idx.offset = offset
    offset += idx.ndocs
  idxs.sort(key=lambda idx:idx.offset)
  if verbose:
    print >>stderr, 'Merging: %r (docs=%d, est. terms=%d): %r' % \
          (cdbname, sum( idx.ndocs for idx in idxs ),
           estimate_terms( idx.nterms for idx in idxs ), idxs)
  
  def merge1(bits, idx):
    offset = idx.offset
    a = decode_array(bits)
    for i in xrange(0, len(a), 2):
      a[i] += offset
    return (offset,a)

  # copy sentences to a new idx with unique ids.
  for idx in idxs:
    for (k,v) in idx.iteritems():
      if k[0] != PROP_SENT:
        idx.key = k
        break
      (docid, pos) = unpack('>xii', k)
      maker.add(pack('>cii', PROP_SENT, idx.offset+docid, pos), v)

  nterms = 0
  total = 0
  docid2info = []
  loc2docid = {}
  for (k,vs) in cdbmerge(idxs):
    if k[0] == PROP_LOC or k[0] == PROP_INFO:
      break
    if k[0] == PROP_DOCID: 
      # read a docid->loc mapping
      (docid,) = unpack('>xi', k)
      for (info,idx) in vs:
        docid1 = docid+idx.offset
        docid2info.append((docid1, info))
        loc = info[4:]
        if verbose and loc in loc2docid:
          print >>stderr, 'Skip duplicated: %r' % loc
        loc2docid[loc] = docid1
    else:
      # merge docid+pos sets
      vs = sorted(( merge1(v, idx) for (v,idx) in vs ), reverse=True)
      ents = sum( len(a) for (base,a) in vs )/2
      (_,all) = vs.pop(0)
      for (base,a) in vs:
        all.extend(a)
      nterms += 1
      total += ents
      maker.add(k, encode_array(ents, all))
      if verbose and nterms % 1000 == 0:
        sys.stderr.write('.'); sys.stderr.flush()

  # write docid->loc mappings (avoiding dupes)
  docid2info.sort()
  for (docid,info) in docid2info:
    maker.add(pack('>ci', PROP_DOCID, docid), info)
  # write loc->docid mappings (avoiding dupes)
  for (loc,docid) in sorted(loc2docid.iteritems()):
    maker.add(PROP_LOC+loc, pack('>i', docid))

  if verbose:
    print >>stderr, 'done: docs=%d, terms=%d, ents=%d' % \
          (len(docid2info), nterms, total)
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

  def flush(self, idxid, merged):
    if not merged: return
    fname = self.indexdb.gen_idx_fname(idxid)
    if 1 < len(merged):
      idxmerge(fname+'.new', merged, self.verbose)
      for idx in merged:
        os.rename(idx.fname, idx.fname+'.bak')
      os.rename(fname+'.new', fname)
    elif merged[0].fname == fname:
      if self.verbose:
        print >>stderr, 'Remain: %r' % (fname)
    else:
      os.rename(merged[0].fname, fname)
      if self.verbose:
        print >>stderr, 'Rename: %r <- %r' % (fname, merged[0].fname)
    return

  def run(self, cleanup=False):
    idxs = [ IndexFile(os.path.join(self.indexdb.idxdir, fname)) for fname in reversed(self.indexdb.idxs) ]
    (ndocs, nterms) = (0, [])
    newidx = 0
    merged = []
    for idx in idxs:
      if ((self.max_docs_threshold and self.max_docs_threshold < ndocs) or
          (self.max_terms_threshold and self.max_terms_threshold < estimate_terms(nterms))):
        self.flush(newidx, merged)
        newidx += 1
        merged = []
        (ndocs, nterms) = (0, [])
      ndocs += idx.ndocs
      nterms.append(idx.nterms)
      merged.append(idx)
    self.flush(newidx, merged)
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
  from corpus import IndexDB
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
  Merger(indexdb, max_docs_threshold, max_terms_threshold, verbose).run()
  return

# main
if __name__ == "__main__": merge(sys.argv)
