#!/usr/bin/env python
import sys, os, os.path
import pycdb as cdb
from util import encode_array, decode_array
from struct import pack, unpack
stderr = sys.stderr

__all__ = [ 'Merger' ]


# Estimate the number of unique terms:
# assuming roughly 25% of the words are common.
def estimate_terms(nterms):
  return reduce(lambda r,n: r + max(n - int(r*0.25), 0), nterms, 0)


##  IndexFile
##
class IndexFile:
  
  def __init__(self, fname):
    self.fname = fname
    self.db = cdb.init(fname)
    (self.ndocs, self.nterms) = unpack('>II', self.db[''])
    self.offset = 0L
    return

  def __repr__(self):
    return '<%s (docs=%d, terms=%d)>' % (self.fname, self.ndocs, self.nterms)
  
  def each(self):
    return self.db.each()


##  cdbmerge
##
def cdbmerge(dbs):
  poss = [ (db.each(), db) for db in dbs ]
  k0 = None
  vs = None
  while poss:
    poss.sort()
    (x,db) = poss.pop(0)
    if not x: continue
    (k,v) = x
    if k0 != k:
      if vs:
        yield (k0,vs)
      vs = []
    vs.append((v,db))
    poss.append((db.each(), db))
    k0 = k
  if vs:
    yield (k0,vs)
  return


##  idxmerge
##
def idxmerge(cdbname, idxs, verbose=0):
  m = cdb.cdbmake(cdbname, cdbname+'.tmp')
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

  total = 0
  nterms = 0
  docid2loc = []
  loc2docid = {}
  for (k,vs) in cdbmerge(idxs):
    # ignore loc->docid mapping
    if not k: continue
    if k[0] == '\xff': break
    if k[0] == '\x00':
      # read a docid->loc mapping
      (docid,) = unpack('>I', k[1:])
      for (loc,idx) in vs:
        docid1 = docid+idx.offset
        docid2loc.append((docid1, loc))
        if verbose and loc in loc2docid:
          print >>stderr, 'Skip duplicated: %r' % loc
        loc2docid[loc] = docid1
      continue
    elif nterms == 0:
      # write docid->loc mappings (avoiding dupes)
      docid2loc.sort()
      for (docid,loc) in docid2loc:
        m.add('\x00'+pack('>I', docid), loc)

    # merge docid+pos sets
    vs = sorted(( merge1(v, idx) for (v,idx) in vs ), reverse=True)
    ents = sum( len(a) for (base,a) in vs )/2
    (_,all) = vs.pop(0)
    for (base,a) in vs:
      all.extend(a)
    nterms += 1
    total += ents
    m.add(k, encode_array(ents, all))
    if verbose and nterms % 1000 == 0:
      sys.stderr.write('.'); sys.stderr.flush()

  # write loc->docid mappings (avoiding dupes)
  for (loc,docid) in sorted(loc2docid.iteritems()):
    m.add('\xff'+loc, pack('>I', docid))

  if verbose:
    print >>stderr, 'done: docs=%d, terms=%d, ents=%d' % \
          (len(docid2loc), nterms, total)
  m.add('', pack('>II', len(docid2loc), nterms))
  m.finish()
  return


##  Merger
##
class Merger:

  def __init__(self, corpus,
               max_docs_threshold=2000,
               max_terms_threshold=50000,
               verbose=0):
    self.corpus = corpus
    self.max_docs_threshold = max_docs_threshold
    self.max_terms_threshold = max_terms_threshold
    self.verbose = verbose
    return

  def flush(self, idxid, merged):
    if not merged: return
    fname = self.corpus.gen_idx_fname(idxid)
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
    idxs = [ IndexFile(os.path.join(self.corpus.idxdir, fname)) for fname in reversed(self.corpus.idxs) ]
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
      for fname in os.listdir(self.corpus.idxdir):
        if fname.endswith('.cdb.bak'):
          fname = os.path.join(self.corpus.idxdir, fname)
          if self.verbose:
            print >>stderr, 'Removing: %r' % fname
          os.unlink(fname)
    self.corpus.refresh()
    return


##  merge
##
def merge(argv):
  import getopt
  from corpus import FilesystemCorpus
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
  corpus = FilesystemCorpus('', idxdir, prefix)
  Merger(corpus, max_docs_threshold, max_terms_threshold, verbose).run()
  return

# main
if __name__ == "__main__": merge(sys.argv)
