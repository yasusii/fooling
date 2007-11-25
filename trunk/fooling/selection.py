#!/usr/bin/env python
# -*- encoding: euc-jp -*-
import re, sys
from util import zen2han, rsplit, encodew
from util import splitchars
from util import intersect, merge, union, decode_array
from struct import pack, unpack
from array import array

upperbound = min
lowerbound = max

__all__ = [
  'Predicate',
  'KeywordPredicate',
  'EMailPredicate',
  'YomiMixin',
  'StrictMixin',
  'YomiKeywordPredicate',
  'StrictKeywordPredicate',
  'YomiEMailPredicate',
  'StrictEMailPredicate',
  'Selection',
  'SelectionWithContinuation',
  'DummySelection',
  'parse_preds'
  ]


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

  def __init__(self):
    self.priority = 0
    self.neg = False
    self.checkpat = None
    self.extpat = None
    return

  def narrow(self, _):
    """
    Returns a list of candidate docs within the given idx.
    """
    return []


class KeywordPredicate(Predicate):

  class IsZeroPos:
    def __call__(self, pos):
      return pos == 0

  def __init__(self, s):
    Predicate.__init__(self)
    self.pos_filter = None
    s = zen2han(s)
    self.q = s
    if s.startswith('-') or s.startswith('!'):
      s = s[1:]
      self.neg = True
    self.r0 = self.r1 = self.r2 = []
    self.setup(s)
    #print (self.checkpat, self.extpat, self.r0, self.r1, self.r2)
    return

  def __repr__(self):
    return '<KeywordPredicate: %r>' % self.q

  def __str__(self):
    return self.q

  def setup(self, s):
    if s.startswith('date:'):
      self.priority = 1
      self.r0 = rdatefeats(s[5:].split(','))
      return
    if s.startswith('title:'):
      s = s[6:]
      self.pos_filter = KeywordPredicate.IsZeroPos()
    self.setup_keyword(s)
    return

  def setup_keyword(self, s):
    (r0,r1,r2) = rsplit(s)
    self.r0 = [ encodew(w) for w in r0 ]
    self.r1 = [ encodew(w) for w in r1 ]
    self.r2 = [ encodew(w) for w in r2 ]
    self.extpat = re.compile(
      r'\W*'.join( c for (c,t) in splitchars(s) if t ),
      re.I | re.UNICODE)
    self.checkpat = self.extpat
    return

  def narrow(self, idx):
    m0 = [ decode_array(idx[w]) for w in self.r0 if idx.has_key(w) ]
    if self.r0 and not m0:
      return []
    m2 = [ decode_array(idx[w]) for w in self.r2 if idx.has_key(w) ]
    if self.r2 and not m2:
      return []
    if self.r1:
      try:
        refs = intersect( decode_array(idx[w]) for w in self.r1 )
      except KeyError:
        return []
      refs = union(refs, [ m for m in (m0,m2) if m ])
    elif not self.r2:
      refs = merge(m0)
    else:
      refs = union(merge(m0), [m2])
    # Now: refs = [ docid1,pos1, docid2,pos2, ... ]
    locs = [ (refs[i], refs[i+1]) for i in xrange(0, len(refs), 2) ]
    if self.pos_filter:
      locs = [ (docid,pos) for (docid,pos) in locs
               if self.pos_filter(pos) ]
    return locs


##  EMailPredicate
##
class EMailPredicate(KeywordPredicate):

  def __repr__(self):
    return '<EMailPredicate: %r>' % self.q

  class IsHeaderPos:
    def __call__(self, pos):
      return pos < 100

  HEADER_PAT = re.compile(
    # does not include "Date:" because it's treated specially.
    r'(title|subject|from|to|cc|rcpt|addr|message-id|references):(.*)',
    re.I|re.S)
  HEADER_MAP = { 'rcpt':'(?:to|cc)',
                 'addr':'(?:from|to|cc)',
                 'title':'subject' }
  MSGID_PAT = re.compile(r'<([^>]+)>')

  def setup(self, s):
    m = self.HEADER_PAT.match(s)
    if not m:
      KeywordPredicate.setup(self, s)
      return
    (h,s) = m.groups()
    h = h.lower()
    self.pos_filter = EMailPredicate.IsHeaderPos()
    if h == 'message-id':  # searching Messsage-ID.
      for m in self.MSGID_PAT.finditer(s):
        self.r1.append('\x10'+m.group(1))
        break
      return
    if h == 'references':  # searching References.
      for m in self.MSGID_PAT.finditer(s):
        self.r0.append('\x10'+m.group(1))
        self.r0.append('\x11'+m.group(1))
      return
    # searching other headers.
    h = self.HEADER_MAP.get(h, h)
    self.setup_keyword(s)
    self.checkpat = re.compile(r'^%s:' % h, re.I) # XXX loose!
    return


##  YomiMixin
##
class YomiMixin:
  
  def setup_keyword(self, s):
    import romm, yomi
    morae = romm.PARSE_DEFAULT.parse(s)
    y = yomi.encode_yomi(''.join( unicode(m) for m in morae
                                  if isinstance(m, romm.Mora) ))
    self.r1 = [ '\x05'+c1+c2 for (c1,c2) in zip(y[:-1],y[1:]) ]
    self.extpat = yomi.YomiPattern(y)
    self.checkpat = self.extpat
    return


##  StrictMixin
##
class StrictMixin:

  ALL_ALPHABET = re.compile(ur'^\|?[\w\s]+\|?$', re.I | re.UNICODE)

  def setup_keyword(self, s):
    (r0,r1,r2) = rsplit(s)
    self.r0 = [ encodew(w) for w in r0 ]
    self.r1 = [ encodew(w) for w in r1 ]
    self.r2 = [ encodew(w) for w in r2 ]
    self.extpat = re.compile(
      r'\W*'.join( c for (c,t) in splitchars(s) if t ),
      re.I | re.UNICODE)
    self.checkpat = self.extpat
    if not self.ALL_ALPHABET.match(s):
      self.checkpat = re.compile(
        r'\s*'.join( re.escape(c) for (c,t) in splitchars(s)
                     if not c.isspace() ),
        re.UNICODE)
    return

class YomiKeywordPredicate(YomiMixin, KeywordPredicate): pass
class StrictKeywordPredicate(StrictMixin, KeywordPredicate): pass
class YomiEMailPredicate(YomiMixin, EMailPredicate): pass
class StrictEMailPredicate(StrictMixin, EMailPredicate): pass


##  Selection
##
class SearchTimeout(Exception): pass
class Selection:

  def __init__(self, corpus, term_preds, doc_preds=None,
               safe=True, start_loc=None, end_loc=None,
               disjunctive=False):
    self._corpus = corpus

    # Predicates: term_preds = [ positive ] + [ negative ]
    self.pos_preds = sorted(( pred for pred in term_preds if not pred.neg ),
                            key=lambda pred: pred.priority, reverse=True)
    self.neg_preds = sorted(( pred for pred in term_preds if pred.neg ),
                            key=lambda pred: pred.priority, reverse=True)
    self.doc_preds = doc_preds or []
    self.safe = safe
    self.disjunctive = disjunctive
    
    # Starting position:
    if start_loc:
      self.start_loc = corpus.loc_indexed(start_loc)
    else:
      self.start_loc = (0, sys.maxint)
    # Ending position:
    if end_loc:
      self.end_loc = corpus.loc_indexed(end_loc)
    else:
      self.end_loc = (sys.maxint-1, 0)
    
    # Number of docs that are already searched.
    self.searched_docs = (0, 0)
    
    # Found documents:
    # (We don't store Document objects to avoid having them pickled!)
    self.found_locs = []                # [loc, ...]
    self.contexts = {}                  # { loc:[pos, ...], ... }
    return

  def __repr__(self):
    return ('<Selection: corpus=%r, term_preds=%r, doc_preds=%r, '
            'start_loc=%r, end_loc=%r, found_locs=%r>') % \
           (self._corpus, self.pos_preds+self.neg_preds, self.doc_preds,
            self.start_loc, self.end_loc, self.found_locs)

  def __setstate__(self, dict):
    self.__dict__.update(dict)
    self._corpus = self._corpus._get_singleton()
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
      pat = pred.extpat
      if not pat: continue
      for m in pat.finditer(s):
        if isinstance(m, tuple):
          (p0,p1) = m
        else:
          (p0,p1) = (m.start(0), m.end(0))
        if p0 < p1:
          r.append((p0,1))
          r.append((p1,-1))
    if not r:
      return [(0, s)]
    r.sort()
    x = []
    (state,p0) = (0, 0)
    for (p1,i) in r:
      x.append((state, s[p0:p1]))
      p0 = p1
      state += i
    assert state == 0
    x.append((0, s[p1:]))
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
    # Return the existing results first.
    for i in xrange(start, len(self.found_locs)):
      yield (i, self.get(i))
    # Now retrieve new results.
    for x in self.iter_start(timeout):
      yield x
    return
    
  def status(self):
    # Get the number of all documents.
    found_docs = len(self.found_locs)
    total_docs = self._corpus.total_docs()
    (searched_docs0, searched_docs1) = self.searched_docs
    searched_docs = searched_docs0 + searched_docs1
    if searched_docs == total_docs:
      return (True, found_docs)
    else:
      # Estimate the number of searched documents,
      # assuming (start_docid ==
      #           the number of unscanned docs in the current idx).
      (_,docid) = self.start_loc
      # rate = (# of found documents) / (# of searched documents)
      estimated = found_docs * (total_docs-searched_docs) / lowerbound(searched_docs, 1)
      return (False, found_docs+estimated)

  def get_docids(self):
    """
    Returns a list of DocIDs that might meet the query.
    """
    (start_idx, start_docid0) = self.start_loc
    (end_idx, end_docid0) = self.end_loc
    # We maintain the number of docs that have been searched so far.
    # But this is separeted into two parts:
    #  "all the docs included up to the previous index" + 
    #  "the number of docs that have been searched within the current index"
    # This way we can compute the number of searched docs deterministicly
    # without any cumulative counting within iterators
    # (no worry for double counting!).
    (searched_docs0, _) = self.searched_docs

    #  start_idx <= idxid <= end_idx.
    #  start_docid-1 >= docid >= end_docid.
    for (idxid,idx) in self._corpus.iteridxs(start_idx, end_idx):
      (idx_docs, _) = unpack('>ii', idx[''])
      if idxid == start_idx:
        start_docid = min(start_docid0, idx_docs)
      else:
        start_docid = idx_docs
      if idxid == end_idx:
        end_docid = end_docid0
      else:
        end_docid = 0
      
      if self.pos_preds:
        conj = False
        docs = {}
      else:
        # no positive predicate.
        conj = True
        docs = dict( (docid,[]) for docid in xrange(start_docid-1,-1,-1) )
      
      # Obtain a set of candidate documents for each predicate.
      for pred in (self.pos_preds + self.neg_preds):
        locs = pred.narrow(idx)
        locs = [ (docid,pos) for (docid,pos) in locs
                 if start_docid > docid and docid >= end_docid ]
        if not locs:
          if pred.neg:
            continue
          elif not self.disjunctive:
            docs.clear()
            break

        if self.disjunctive:
          # disjunctive (OR) search.
          docs1 = {}
          for (docid,pos) in locs:
            if docid not in docs1:
              context = array('i')
              docs1[docid] = context
            else:
              context = docs1[docid]
            context.append(pos)
          # combine with the previous docs.
          for (docid,context) in docs1.iteritems():
            if docid not in docs:
              r = []
              docs[docid] = r
            else:
              r = docs[docid]
            r.append((context, pred.checkpat))

        elif pred.neg:
          # negative conjunctive (-AND) search.
          for (docid,pos) in locs:
            if docid in docs:
              del docs[docid]

        else:
          # positive conjunctive (+AND) search.
          docs1 = {}
          for (docid,pos) in locs:
            if conj and (docid not in docs): continue
            if docid not in docs1:
              context = array('i')
              docs1[docid] = context
            else:
              context = docs1[docid]
            context.append(pos)
          if conj:
            # intersect with the previous docs.
            for (docid,context) in docs1.iteritems():
              r = docs[docid]
              r.append((context, pred.checkpat))
              docs1[docid] = r
            docs = docs1
          else:
            conj = True
            docs = dict( (docid,[(a, pred.checkpat)]) for (docid,a)
                         in docs1.iteritems() )

      # docs: the candidate documents in the current index file.
      docs = docs.items()
      docs.sort(reverse=True)
      for (docid,contexts) in docs:
        self.start_loc = (idxid, docid)
        self.searched_docs = (searched_docs0, idx_docs-docid)
        try:
          loc = idx['\x00'+pack('>i',docid)]
        except KeyError:
          continue
        # Skip if the document is already in the cache.
        if loc in self.contexts: continue
        # Skip if the document does not exist.
        if not self._corpus.loc_exists(loc): continue
        # Apply the document predicates.
        pol = 0
        for pred in self.doc_preds:
          pol = pred(loc, self._corpus)
          if pol: break
        # pol < 0: rejected immediately.
        # pol > 0: accepted immediately.
        # pol = 0: not decided (further examination required).
        if 0 <= pol:
          yield (pol,loc,contexts)

      # Finished this index.
      searched_docs0 += idx_docs
      self.searched_docs = (searched_docs0, 0)
    return
    
  def iter_start(self, timeout=0):
    from time import time
    limit_time = 0
    if timeout:
      limit_time = time() + timeout
    
    for (pol,loc,contexts) in self.get_docids():
      # open each candidate document.
      doc = self._corpus.get_doc(loc)
      # Skip if the document is newer than the index.
      if self.safe and self._corpus.mtime < doc.get_mtime(): continue
      if not pol:
        filtered = doc.filter_context(contexts, self.disjunctive)
        if len(filtered) == len(contexts) or (self.disjunctive and filtered):
          pol = 1
          self.contexts[loc] = filtered
      if 0 < pol:
        self.found_locs.append(loc)
        yield (len(self.found_locs)-1, doc)
      # Abort if the specified time is passed.
      if limit_time and limit_time < time():
        raise SearchTimeout(self)
    return


##  SelectionWithContinuation
##
class SelectionWithContinuation(Selection):
  
  def iter(self, start=0, timeout=0):
    if start != len(self.found_locs):
      raise ValueError('Cannot retrieve previous results.')
    return self.iter_start(timeout)
  
  def save_continuation(self):
    from base64 import b64encode
    (idxid, docid) = self.start_loc
    return b64encode(pack('>HiH', idxid, docid, len(self.found_locs)))

  def load_continuation(self, x):
    from base64 import b64decode
    try:
      (idxid0, docid0, found_docs) = unpack('>HiH', b64decode(x))
    except:
      return
    # put dummy locs (max. 65535)
    self.start_loc = (idxid0, docid0)
    self.found_locs = [None] * found_docs
    searched_docs0 = 0
    for (idxid,idx) in self._corpus.iteridxs(end=idxid0-1):
      (idx_docs, _) = unpack('>ii', idx[''])
      searched_docs0 += idx_docs
    self.searched_docs = (searched_docs0, idx_docs-docid0)
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
    self._corpus = self._corpus._get_singleton()
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


# Returns True if the given string can be yomi-keyword.
def canbe_yomi(s):
  import romm
  for m in romm.PARSE_DEFAULT.parse(s):
    if not isinstance(m, romm.Mora): return False
  return True

# parse_preds
QUERY_PAT = re.compile(r'"[^"]+"|\S+', re.UNICODE)
def parse_preds(query, max_preds=10, predtype=KeywordPredicate):
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
    s = doc.get_snippet(selection,
                        highlight=lambda x: '\033[31m%s\033[m' % x,
                        maxchars=200, maxcontext=100)
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
  import getopt, locale, time
  import document
  from corpus import FilesystemCorpus
  def usage():
    print ('usage: %s [-d] [-T timeout] [-s|-Y] [-S] [-D] '
           '[-c savefile] [-b basedir] [-p prefix] [-t doctype] '
           '[-e encoding] [-n results] idxdir [keyword ...]') % argv[0]
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(argv[1:], 'dT:sYSDc:b:p:t:e:n:')
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
  predtype = KeywordPredicate
  encoding = locale.getdefaultlocale()[1] or 'euc-jp'
  n = 10
  for (k, v) in opts:
    if k == '-d': debug += 1
    elif k == '-T': timeout = int(v)
    elif k == '-S': safe = False
    elif k == '-D': disjunctive = True
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
if __name__ == '__main__': search(sys.argv)
