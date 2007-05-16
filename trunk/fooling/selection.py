#!/usr/bin/env python
# -*- encoding: euc-jp -*-

import re, sys, time
from util import zen2han, rsplit, encodew
from util import splitchars
from util import intersect, merge, union, decode_array
from struct import pack, unpack
from array import array

upperbound = min
lowerbound = max

__all__ = [ 'Predicate', 'StrictPredicate', 'EMailPredicate', 'Selection',
            'SelectionWithContinuation', 'DummySelection',
            'parse_preds' ]


# retrieval date features
DATE_PAT = re.compile(r'(\d+)(/\d+)?(/\d+)?')
def rdatefeats(dates):
  r = []
  
  def getdate(x):
    mc = DATE_PAT.match(x)
    (y,m,d) = (0,0,0)
    if mc:
      if mc.group(3):
        d = upperbound(lowerbound(int(mc.group(3)[1:]), 1), 31)
      if mc.group(2):
        m = upperbound(lowerbound(int(mc.group(2)[1:]), 1), 12)
      y = upperbound(lowerbound(int(mc.group(1)), 1970), 2037)
    return (y,m,d)
  
  def addrange((ya,ma,da),(yb,mb,db)):
    if da and da:
      r.extend( '\x20'+pack('>hbb', ya, ma, d) for d in xrange(da,db+1) )
    elif ma and mb:
      r.extend( '\x20'+pack('>hb', ya, m) for m in xrange(ma,mb+1) )
    elif ya and yb:
      r.extend( '\x20'+pack('>h', y) for y in xrange(ya,yb+1) )
    return
    
  for x in dates:
    if '-' not in x:
      (y,m,d) = getdate(x)
      addrange((y,m,d), (y,m,d))
      continue
    x = x.split('-')
    if len(x) != 2: continue
    ((y1,m1,d1), (y2,m2,d2)) = (getdate(x[0]), getdate(x[1]))
    if (y2,m2,d2) <= (y1,m1,d1): continue
    if y1 == y2 and m1 == m2 and d1 and d2:
      addrange((y1,m1,d1), (y2,m2,d2))
      continue
    if d1:
      addrange((y1,m1,d1), (y1,m1,31))
      m1 += 1
    if d2:
      addrange((y2,m2,1), (y2,m2,d2))
      m2 -= 1
    if y1 == y2 and m1 and m2:
      addrange((y1,m1,0), (y2,m2,0))
      continue
    if m1:
      addrange((y1,m1,0), (y1,12,0))
      y1 += 1
    if m2:
      addrange((y2,1,0), (y2,m2,0))
      y2 -= 1
    addrange((y1,0,0), (y2,0,0))
  return r
  

##  Predicate
##
class Predicate:

  def __init__(self, s):
    self.priority = 0
    self.pos_filter = None
    self.pos_filter_func = None
    self.reg_pat = None
    s = zen2han(s)
    self.q = s
    if s.startswith('-') or s.startswith('!'):
      s = s[1:]
      self.neg = True
    else:
      self.neg = False
    (pat, self.r0, self.r1, self.r2) = self.setup(s)
    if pat:
      self.reg_pat = re.compile(pat, re.I | re.UNICODE)
    #print (pat, self.r0, self.r1, self.r2)
    if self.pos_filter:
      self.pos_filter_func = eval(self.pos_filter)
    return

  def __repr__(self):
    return '<Predicate: %r>' % self.q

  def __getstate__(self):
    odict = self.__dict__.copy()
    del odict['pos_filter_func']
    return odict

  def __setstate__(self, dict):
    self.__dict__.update(dict)
    self.pos_filter_func = None
    if self.pos_filter:
      self.pos_filter_func = eval(self.pos_filter)
    return

  def setup(self, s):
    if s.startswith('date:'):
      self.priority = 1
      return (None, rdatefeats(s[5:].split(',')), [], [])
    if s.startswith('title:'):
      s = s[6:]
      self.pos_filter = 'lambda pos: pos == 0'
    (r0,r1,r2) = rsplit(s)
    return ('('+r'\W*'.join( c for (c,t) in splitchars(s) if t )+')',
            [ encodew(w) for w in r0 ],
            [ encodew(w) for w in r1 ],
            [ encodew(w) for w in r2 ])


##  StrictPredicate
##
class StrictPredicate(Predicate):

  ALL_ALPHABET = re.compile(ur'^\|?[\w\s]+\|?$', re.I | re.UNICODE)
  
  def setup(self, s):
    if s.startswith('date:'):
      self.priority = 1
      return (None, rdatefeats(s[5:].split(',')), [], [])
    if s.startswith('title:'):
      s = s[6:]
      self.pos_filter = 'lambda pos: pos == 0'
    if self.ALL_ALPHABET.match(s):
      pat = '('+r'\W*'.join( c for (c,t) in splitchars(s) if t )+')'
    else:
      pat = '('+r'\s*'.join( re.escape(c) for (c,t) in splitchars(s) if not c.isspace() )+')'
    (r0,r1,r2) = rsplit(s)
    return (pat,
            [ encodew(w) for w in r0 ],
            [ encodew(w) for w in r1 ],
            [ encodew(w) for w in r2 ])


##  EMailPredicate
##
class EMailPredicate(Predicate):

  HEADER_PAT = re.compile(r'(subject|from|to|cc|rcpt|addr|message-id|references):(.*)', re.I|re.S)
  HEADER_MAP = { 'rcpt':'(?:to|cc)', 'addr':'(?:from|to|cc)' }
  MSGID_PAT = re.compile(r'<([^>]+)>')

  def setup(self, s):
    if s.startswith('date:'):
      self.priority = 1
      return (None, rdatefeats(s[5:].split(',')), [], [])
    m = self.HEADER_PAT.match(s)
    if m:
      (h,s) = m.groups()
      h = h.lower()
      self.pos_filter = 'lambda pos: pos < 100'
      if h == 'message-id':
        r = []
        for m in self.MSGID_PAT.finditer(s):
          r.append('\x10'+m.group(1))
          break
        return (None, [], r, [])
      elif h == 'references':
        r = []
        for m in self.MSGID_PAT.finditer(s):
          r.append('\x10'+m.group(1))
          r.append('\x11'+m.group(1))
        return (None, r, [], [])
      else:
        h = self.HEADER_MAP.get(h, h)
        pat = ('^%s:.*' % h) + '('+r'\s*'.join( c for (c,t) in splitchars(s) if not c.isspace() )+')'
    else:
      pat = '('+r'\W*'.join( c for (c,t) in splitchars(s) if t )+')'
    (r0,r1,r2) = rsplit(s)
    return (pat,
            [ encodew(w) for w in r0 ],
            [ encodew(w) for w in r1 ],
            [ encodew(w) for w in r2 ])


##  Selection
##
class SearchTimeout(RuntimeError): pass
class Selection:

  def __init__(self, corpus, term_preds, doc_preds=None,
               safe=True, start_loc=None, end_loc=None,
               disjunctive=False):
    self._corpus = corpus

    # Predicates:
    # term_preds = [ positive ] + [ negative ]
    self.pos_preds = sorted(( pred for pred in term_preds if not pred.neg ),
                            key=lambda pred: pred.priority, reverse=True)
    self.neg_preds = sorted(( pred for pred in term_preds if pred.neg ),
                            key=lambda pred: pred.priority, reverse=True)
    self.doc_preds = doc_preds or []
    self.safe = safe
    self.disjunctive = disjunctive
    
    # Starting position:
    if start_loc:
      (self.start_idx, self.start_docid) = corpus.loc_indexed(start_loc)
      self.start_docid += 1
    else:
      (self.start_idx, self.start_docid) = (0, sys.maxint)
    # Ending position:
    if end_loc:
      (self.end_idx, self.end_docid) = corpus.loc_indexed(end_loc)
    else:
      (self.end_idx, self.end_docid) = (sys.maxint, 0)
    
    # Number of docs in the current index file.
    self.idx_docs = 0
    # Number of docs in the indices that are already searched.
    self.finished_docs = 0
    
    # Found documents:
    # (We don't store Document objects to avoid having them pickled!)
    self.found_locs = []                # [loc, ...]
    self.contexts = {}                  # { loc:[pos, ...], ... }
    return

  def __repr__(self):
    return '<Selection: corpus=%r, term_preds=%r, doc_preds=%r, start_idx=%r, start_docid=%d, found_locs=%r>' % \
           (self._corpus, self.pos_preds+self.neg_preds, self.doc_preds,
            self.start_idx, self.start_docid, self.found_locs)

  def __setstate__(self, dict):
    self.__dict__.update(dict)
    self._corpus = self._corpus._unpickle()
    return

  def __len__(self):
    return len(self.found_locs)

  def __getitem__(self, i):
    return self.get(i)

  def __iter__(self):
    return self.iter()

  def get_corpus(self):
    return self._corpus

  def get_preds(self):
    return (self.pos_preds + self.neg_preds)

  def get_context(self, loc):
    return self.contexts.get(loc, [])

  def matched_range(self, s):
    r = []
    for pred in self.pos_preds:
      pat = pred.reg_pat
      if not pat: continue
      for m in pat.finditer(s):
        (p0,p1) = (m.start(1), m.end(1))
        if p0 < p1:
          r.append((p0,1))
          r.append((p1,-1))
    if not r:
      return [(False, s)]
    r.sort()
    x = []
    (state,p0) = (False, 0)
    for (p1,i) in r:
      x.append((state, s[p0:p1]))
      state += i
      p0 = p1
    assert state == 0
    x.append((False, s[p1:]))
    return x

  def get(self, i, timeout=0):
    if len(self.found_locs) <= i:
      j = None
      for (j,doc) in self.iter_start(timeout):
        if i <= j: break
      if i == j:
        return doc
    # might cause KeyError
    return self._corpus.get_doc(self.found_locs[i])
  
  def iter(self, start=0, timeout=0):
    if len(self.found_locs) < start:
      raise ValueError('invalid start index: %d' % start)
    for i in xrange(start, len(self.found_locs)):
      yield (i, self.get(i))
    for x in self.iter_start(timeout):
      yield x
    return
    
  def status(self):
    # Get the number of all documents.
    found_docs = len(self.found_locs)
    total_docs = self._corpus.total_docs()
    if self.finished_docs == total_docs:
      return (True, found_docs)
    else:
      # Estimate the number of searched documents,
      # assuming (start_docid == the number of unscanned docs in the current idx).
      searched_docs = max(1, self.finished_docs + self.idx_docs - self.start_docid)
      # rate = (# of found documents) / (# of searched documents)
      estimated = (found_docs * (total_docs - searched_docs) / searched_docs)
      return (False, found_docs+estimated)

  def get_docids(self, idx):
    if self.pos_preds:
      docs = {}
      conj = False
    else:
      # no positive predicate.
      docs = dict( (docid,[]) for docid in xrange(min(self.start_docid-1, self.idx_docs-1),-1,-1) )
      conj = True
    for pred in (self.pos_preds + self.neg_preds):
      try:
        m0 = [ decode_array(idx[w]) for w in pred.r0 if idx.has_key(w) ]
        if pred.r0 and not m0: raise KeyError
        m2 = [ decode_array(idx[w]) for w in pred.r2 if idx.has_key(w) ]
        if pred.r2 and not m2: raise KeyError
        if pred.r1:
          refs = union(intersect( decode_array(idx[w]) for w in pred.r1 ),
                       [ m for m in (m0,m2) if m ])
        elif not pred.r2:
          refs = merge(m0)
        else:
          refs = union(merge(m0), [m2])
      except KeyError:
        if pred.neg:
          continue
        elif self.disjunctive:
          refs = []
        else:
          docs.clear()
          break
      # refs = [ docid1,pos1, docid2,pos2, ... ]
      #print 'refs:', pred, refs
      # sort refs by docid
      pos_filter = pred.pos_filter_func
      start_docid = self.start_docid
      end_docid = 0
      if self.start_idx == self.end_idx:
        end_docid = self.end_docid
      if self.disjunctive:
        # disjunctive (or) search
        docs1 = {}
        for i in xrange(0, len(refs), 2):
          (docid,pos) = (refs[i], refs[i+1])
          if start_docid <= docid: continue
          if docid < end_docid: break
          if pos_filter and not pos_filter(pos): continue
          if docid not in docs1:
            context = array('i')
            docs1[docid] = context
          else:
            context = docs1[docid]
          context.append(pos)
        # conjunction with the previous docs.
        for (docid,context) in docs1.iteritems():
          if docid not in docs:
            r = []
            docs[docid] = r
          else:
            r = docs[docid]
          r.append((context, pred.reg_pat))
      elif pred.neg:
        # negative conjunctive (-and) search
        for i in xrange(0, len(refs), 2):
          (docid,pos) = (refs[i], refs[i+1])
          if start_docid <= docid: continue
          if docid < end_docid: break
          if pos_filter and not pos_filter(pos): continue
          if docid in docs:
            del docs[docid]
      else:
        # positive conjunctive (+and) search
        docs1 = {}
        for i in xrange(0, len(refs), 2):
          (docid,pos) = (refs[i], refs[i+1])
          if conj and (docid not in docs): continue
          if start_docid <= docid: continue
          if docid < end_docid: break
          if pos_filter and not pos_filter(pos): continue
          if docid not in docs1:
            context = array('i')
            docs1[docid] = context
          else:
            context = docs1[docid]
          context.append(pos)
        # conj: conjunction with the previous docs.
        if conj:
          # intersect
          for (docid,context) in docs1.iteritems():
            r = docs[docid]
            r.append((context, pred.reg_pat))
            docs1[docid] = r
          docs = docs1
        else:
          docs = dict( (docid,[(a, pred.reg_pat)]) for (docid,a) in docs1.iteritems() )
          conj = True
    return docs
  
  def iter_start(self, timeout=0):
    limit_time = 0
    if timeout:
      limit_time = time.time() + timeout
    # Try each idx file...
    for (idxid,idx) in self._corpus.iteridxs(self.start_idx):
      if self.end_idx < idxid: break
      (self.idx_docs, _) = unpack('>ii', idx[''])
      # docs: { docid:[pos, ...], ... } for each index file.
      docs = self.get_docids(idx)
      #print docs
      # load up candidate documents, check if it really matches.
      for (docid,contexts) in sorted(docs.iteritems(), reverse=True):
        try:
          loc = idx['\x00'+pack('>i',docid)]
        except KeyError:
          continue
        # Avoid duplication.
        if loc in self.contexts: continue
        # Skip if the document does not exist.
        if not self._corpus.loc_exists(loc): continue
        # Document predicates.
        x = 0
        for pred in self.doc_preds:
          x = pred(loc, self._corpus)
          if x: break
        if x < 0: continue
        doc = self._corpus.get_doc(loc)
        # Skip if the document is newer than the index.
        if self.safe and self._corpus.mtime < doc.get_mtime(): continue
        filtered = doc.filter_context(contexts, self.disjunctive)
        if len(filtered) == len(contexts) or (self.disjunctive and filtered):
          x = 1
          self.contexts[loc] = filtered
        if x:
          self.found_locs.append(loc)
          self.start_docid = docid
          yield (len(self.found_locs)-1, doc)
        if limit_time and limit_time < time.time(): raise SearchTimeout(self)
      self.finished_docs += self.idx_docs
      self.start_idx = idxid+1
      self.start_docid = sys.maxint
    return


##  SelectionWithContinuation
##
class SelectionWithContinuation(Selection):
  
  def __iter__(self):
    raise TypeError('Use iter_start() instead.')
  
  def iter(self, start=0, timeout=0):
    raise TypeError('Use iter_start() instead.')
    
  def save_continuation(self):
    from base64 import b64encode
    return b64encode(pack('>HiH',
                          self.start_idx,
                          self.start_docid,
                          len(self.found_locs)))

  def load_continuation(self, x):
    from base64 import b64decode
    try:
      (self.start_idx,
       self.start_docid,
       found_docs) = unpack('>HiH', b64decode(x))
    except:
      return
    # put dummy locs (max. 65535)
    self.found_locs = [None] * found_docs
    for (idxid,idx) in self._corpus.iteridxs():
      (self.idx_docs, _) = unpack('>ii', idx[''])
      if idxid == self.start_idx: break
      self.finished_docs += self.idx_docs
    return


##  DummySelection
##
class DummySelection:
  
  def __init__(self, corpus, locs):
    self._corpus = corpus
    self.locs = locs
    return
  
  def __repr__(self):
    return '<DummySelection: corpus=%r, locs=%r>' % (self._corpus, self.locs)
  
  def __len__(self):
    return len(self.locs)

  def __getitem__(self, i):
    return self.get(i)

  def __setstate__(self, dict):
    self.__dict__.update(dict)
    self._corpus = self._corpus._unpickle()
    return

  def __iter__(self):
    return self.iter()

  def get_corpus(self):
    return self._corpus

  def get_preds(self):
    return []

  def get_context(self, _):
    return []

  def matched_range(self, s):
    return [(False, s)]

  def get(self, i):
    return self._corpus.get_doc(self.locs[i])

  def iter(self, i=0, timeout=0):
    while i < len(self.locs):
      yield (i, self.get(i))
      i += 1
    return

  def status(self):
    return (True, len(self.locs))


# parse_preds
QUERY_PAT = re.compile(r'"[^"]+"|\S+', re.UNICODE)
def parse_preds(query, max_preds=10, predtype=Predicate):
  preds = []
  for m in QUERY_PAT.finditer(query):
    s = m.group(0)
    if s[0] == '"' and s[-1] == '"':
      preds.append(predtype(s[1:-1]))
    else:
      preds.append(predtype(s))
    if max_preds <= len(preds): break
  return preds


##  search
##
def show_results(selection, n, encoding, timeout=0):
  def e(s): return s.encode(encoding, 'replace')
  window = []
  for (found,doc) in selection.iter(timeout=timeout):
    s = doc.get_snippet(selection, highlight=lambda x: '\033[31m%s\033[m' % x, maxchars=200, maxcontext=100)
    print '%d: [%s] %s' % (found+1, e(doc.get_title()), e(s))
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
  import getopt, locale
  import document
  from corpus import FilesystemCorpus
  def usage():
    print 'usage: %s [-d] [-T timeout] [-s] [-S] [-D] [-c savefile] [-b basedir] [-p prefix] [-t doctype] [-e encoding] [-n results] idxdir [keyword ...]' % argv[0]
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(argv[1:], 'dT:sSDc:b:p:t:e:n:')
  except getopt.GetoptError:
    usage()
  debug = 0
  timeout = 0
  safe = True
  disjunctive = False
  savefile = ''
  basedir = ''
  prefix = ''
  doctype = document.PlainTextDocument
  predtype = Predicate
  encoding = locale.getdefaultlocale()[1] or 'euc-jp'
  n = 10
  for (k, v) in opts:
    if k == '-d': debug += 1
    elif k == '-T': timeout = int(v)
    elif k == '-S': safe = False
    elif k == '-D': disjunctive = True
    elif k == '-s': predtype = StrictPredicate
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
    corpus = FilesystemCorpus(basedir, idxdir, prefix, doctype, encoding)
    corpus.open()
    preds = [ predtype(unicode(kw, encoding)) for kw in keywords ]
    selection = Selection(corpus, preds, safe=safe, disjunctive=disjunctive)
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

  if timeout:
    print '%.2f sec.' % (time.time()-t0)
  return

# main
if __name__ == '__main__':
  search(sys.argv)
  #import profile
  #profile.run('search(sys.argv)')
