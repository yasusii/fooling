#!/usr/bin/env python
##
##  selection.py
##

import sys, re
from struct import pack, unpack
from array import array
from utils import zen2han, rsplit, encodew, encodey
from utils import splitchars, rdatefeats, lowerbound
from utils import intersect, merge, union, decode_array
from utils import idx_sent, idx_sents, idx_info, idx_docid2info, idx_docids

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
  'canbe_yomi',
  'parse_preds',
  ]


##  Predicate
##
class Predicate(object):

  def __init__(self):
    self.priority = 0
    self.neg = False
    self.checkpat = None
    self.matchpat = None
    return

  def narrow_docids(self, idx):
    "Returns a list of candidate docs within the given idx."
    raise NotImplementedError

  def check_docid(self, docid):
    raise NotImplementedError

  def check_sentid(self, sentid):
    raise NotImplementedError


class AlwaysFalsePredicate(Predicate):
  def narrow_docids(self, idx):
    return []
  def check_docid(self, docid):
    return False
  def check_sentid(self, sentid):
    return False


class AlwaysTruePredicate(Predicate):
  def narrow_docids(self, idx):
    try:
      return [ (docid,0) for docid in idx_docids(idx) ]
    except KeyError:
      return []
  def check_docid(self, docid):
    return True
  def check_sentid(self, sentid):
    return True


class KeywordPredicate(Predicate):

  def __init__(self, s):
    Predicate.__init__(self)
    s = zen2han(s)
    self.q = s
    if s.startswith('-') or s.startswith('!'):
      s = s[1:]
      self.neg = True
    self.r0 = self.r1 = self.r2 = []
    self.sentid = None
    self.setup_feats(s)
    #print (self.checkpat, self.matchpat, self.r0, self.r1, self.r2)
    return

  def __repr__(self):
    return '<KeywordPredicate: %r>' % self.q

  def __str__(self):
    return self.q

  def setup_feats(self, s):
    if s.startswith('date:'):
      self.priority = 1
      self.r0 = rdatefeats(s[5:].split(','))
      return
    if s.startswith('title:'):
      s = s[6:]
      self.sentid = 0
    self.setup_pats(s)
    return

  def setup_pats(self, s):
    (r0,r1,r2) = rsplit(s)
    self.r0 = [ encodew(w) for w in r0 ]
    self.r1 = [ encodew(w) for w in r1 ]
    self.r2 = [ encodew(w) for w in r2 ]
    self.matchpat = re.compile(
      r'\W*'.join( c for (c,t) in splitchars(s) if t ),
      re.I | re.UNICODE)
    self.checkpat = self.matchpat
    return

  def narrow_docids(self, idx):
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
    # Now: refs = [ docid1,sentid1, docid2,sentid2, ... ]
    locs = [ (refs[i], refs[i+1]) for i in xrange(0, len(refs), 2) ]
    return locs

  def check_docid(self, docid):
    return True
  
  def check_sentid(self, sentid):
    return self.sentid is None or sentid == self.sentid


##  FeatPredicate
##
class FeatPredicate(Predicate):
  
  def __init__(self, feats, neg=False):
    Predicate.__init__(self)
    self.neg = neg
    self.feats = feats
    self.curidx = 0
    return

  def __str__(self):
    return self.q

  def check_docid(self, docid):
    return True
  
  def check_sentid(self, sentid):
    return True
  
  def narrow_docids(self, idx):
    m0 = [ decode_array(idx[feat]) for feat in self.feats if idx.has_key(feat) ]
    if not m0:
      return []
    refs = merge(m0)
    locs = [ (refs[i], refs[i+1]) for i in xrange(0, len(refs), 2) ]
    return locs


##  EMailPredicate
##
class EMailPredicate(KeywordPredicate):

  def __repr__(self):
    return '<EMailPredicate: %r>' % self.q

  HEADER_PAT = re.compile(
    # does not include "Date:" because it's handled specially.
    r'(title|subject|from|to|cc|rcpt|addr|message-id|references):(.*)',
    re.I|re.S)
  HEADER_MAP = { 'rcpt':'(?:to|cc)',
                 'addr':'(?:from|to|cc)',
                 'title':'subject' }
  MSGID_PAT = re.compile(r'<([^>]+)>')

  def setup_feats(self, s):
    m = self.HEADER_PAT.match(s)
    if not m:
      KeywordPredicate.setup_feats(self, s)
      return
    (h,s) = m.groups()
    h = h.lower()
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
    self.setup_pats(s)
    self.checkpat = re.compile(r'^%s:' % h, re.I) # XXX loose!
    return


##  YomiMixin
##
class YomiMixin(object):
  
  def __str__(self):
    return '{%s}' % self.q

  def setup_pats(self, s):
    import romm, yomi
    morae = romm.PARSE_DEFAULT.parse(s)
    q = ''.join( unicode(m) for m in morae if isinstance(m, romm.Mora) )
    y = yomi.canonicalize_yomi(yomi.encode_yomi(q))
    self.r1 = [ encodey(c1+c2) for (c1,c2) in zip(y[:-1],y[1:]) ]
    self.matchpat = yomi.YomiPattern(y)
    self.checkpat = self.matchpat
    return


##  StrictMixin
##
class StrictMixin(object):

  ALL_ALPHABET = re.compile(ur'^\|?[\w\s]+\|?$', re.I | re.UNICODE)

  def __str__(self):
    return '<%s>' % self.q

  def setup_pats(self, s):
    (r0,r1,r2) = rsplit(s)
    self.r0 = [ encodew(w) for w in r0 ]
    self.r1 = [ encodew(w) for w in r1 ]
    self.r2 = [ encodew(w) for w in r2 ]
    self.matchpat = re.compile(
      r'\W*'.join( c for (c,t) in splitchars(s) if t ),
      re.I | re.UNICODE)
    if not self.ALL_ALPHABET.match(s):
      self.checkpat = re.compile(
        r'\s*'.join( re.escape(c) for (c,t) in splitchars(s)
                     if not c.isspace() ),
        re.UNICODE)
    else:
      self.checkpat = self.matchpat
    return


class YomiKeywordPredicate(YomiMixin, KeywordPredicate): pass
class StrictKeywordPredicate(StrictMixin, KeywordPredicate): pass
class YomiEMailPredicate(YomiMixin, EMailPredicate): pass
class StrictEMailPredicate(StrictMixin, EMailPredicate): pass


##  Selection
##
class SearchTimeout(Exception): pass
class Selection(object):

  def __init__(self, indexdb, preds,
               disjunctive=False, timeout=0, 
               start_loc=None, end_loc=None, debug=0):
    self._indexdb = indexdb
    self.debug = 0
    
    # Predicates: term_preds = [ positive ] + [ negative ]
    self.pos_preds = sorted(( pred for pred in preds if not pred.neg ),
                            key=lambda pred: pred.priority, reverse=True)
    self.neg_preds = sorted(( pred for pred in preds if pred.neg ),
                            key=lambda pred: pred.priority, reverse=True)
    self.doc_preds = []
    self.disjunctive = disjunctive
    self.timeout = timeout
    
    # Starting position:
    if start_loc:
      self.start_loc = indexdb.loc_indexed(start_loc)
    else:
      self.start_loc = (0, sys.maxint)
    # Ending position:
    if end_loc:
      self.end_loc = indexdb.loc_indexed(end_loc)
    else:
      self.end_loc = (sys.maxint-1, 0)
    
    # Number of docs that are already searched.
    self.searched_docs = (0, 0)
    
    # Found documents:
    self.narrowed = 0
    self.found_docs = []                # [hit, ...]
    self.snippets = {}                  # { hit:[sentid, ...], ... }
    self.iter = self.start_iter()
    return

  def __repr__(self):
    return ('<Selection: indexdb=%r, preds=%r, '
            'start_loc=%r, end_loc=%r, found_docs=%r>') % \
           (self._indexdb, self.pos_preds+self.neg_preds, 
            self.start_loc, self.end_loc, self.found_docs)

  def __len__(self):
    return len(self.found_docs)

  def __getitem__(self, i):
    try:
      while len(self.found_docs) <= i:
        self.iter.next()
      return self.found_docs[i]
    except StopIteration:
      raise IndexError(i)
  
  def __iter__(self):
    for x in self.found_docs:
      yield x
    try:
      while 1:
        yield self.iter.next()
    except StopIteration:
      pass
    return
    
  def get_preds(self):
    return (self.pos_preds + self.neg_preds)

  def set_timeout(self, timeout):
    self.timeout = timeout
    return

  def get_docids(self):
    "Returns a list of DocIDs that have a given feature."
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
    for (idxid,idx) in self._indexdb.iteridxs(start_idx, end_idx):
      assert isinstance(idxid, int)
      try:
        (ndocs, _) = idx_info(idx)
      except KeyError:
        continue
      if idxid == start_idx:
        start_docid = min(start_docid0, ndocs)
      else:
        start_docid = ndocs
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
      
      # Get a set of narrowed documents for each predicate.
      for pred in (self.pos_preds + self.neg_preds):
        # locs: docids must be in decending order. (ie. start_docid > end_docid)
        locs = [ (docid,sentid) for (docid,sentid) in pred.narrow_docids(idx)
                 if start_docid >= docid and docid > end_docid ]
        locs = [ (docid,sentid) for (docid,sentid) in locs
                 if pred.check_docid(docid) and pred.check_sentid(sentid) ]
        if not locs:
          if pred.neg:
            continue
          elif not self.disjunctive:
            docs.clear()
            break

        if self.disjunctive:
          # disjunctive (OR) search.
          docs1 = {}
          for (docid,sentid) in locs:
            if docid not in docs1:
              sentids = array('i')
              docs1[docid] = sentids
            else:
              sentids = docs1[docid]
            assert isinstance(sentids, array)
            sentids.append(sentid)
          # combine with the previous docs.
          for (docid,sentids) in docs1.iteritems():
            if docid not in docs:
              r = []
              docs[docid] = r
            else:
              r = docs[docid]
            x = (sentids, pred.checkpat)
            r.append(x)

        elif pred.neg:
          # negative conjunctive (-AND) search.
          for (docid,sentid) in locs:
            if docid in docs:
              del docs[docid]

        else:
          # positive conjunctive (+AND) search.
          docs1 = {}
          for (docid,sentid) in locs:
            if conj and (docid not in docs): continue
            if docid not in docs1:
              sentids = array('i')
              docs1[docid] = sentids
            else:
              sentids = docs1[docid]
            assert isinstance(sentids, array)
            sentids.append(sentid)
          if conj:
            # intersect with the previous docs.
            tmp = {}
            for (docid,sentids) in docs1.iteritems():
              r = docs[docid]
              x = (sentids, pred.checkpat)
              r.append(x)
              tmp[docid] = r
            docs = tmp
          else:
            # first positive predicate.
            conj = True
            for (docid,sentids) in docs1.iteritems():
              docs[docid] = [(sentids, pred.checkpat)]

      # docs: the candidate documents in the current index file.
      docs2 = docs.items()
      docs2.sort(reverse=True)
      found = set()
      for (docid,contexts) in docs2:
        self.start_loc = (idxid, docid)
        self.searched_docs = (searched_docs0, ndocs-docid)
        # Skip if the document is already in the list.
        if docid in found: continue
        found.add(docid)
        yield (idx,docid,contexts)

      # Finished this index.
      searched_docs0 += ndocs
      self.searched_docs = (searched_docs0, 0)
    return

  def start_iter(self):
    "Iterates over the search resuts."
    from time import time
    for (idx,docid,contexts) in self.get_docids():
      t0 = 0
      if self.timeout:
        t0 = time()
      pol = 0
      if self.doc_preds:
        # Apply the document predicates.
        try:
          (loc,_) = idx_docid2info(idx, docid)
          for pred in self.doc_preds:
            pol = pred(loc)
            if pol: break
        except KeyError:
          pass
      # pol < 0: rejected immediately.
      # pol > 0: accepted immediately.
      # pol = 0: undecided (further examination required).
      hit = (idx,docid)
      self.narrowed += 1
      if pol == 0:
        # contexts (a list of sentids) is stored in descending order in an index file.
        filtered = []
        # Receives a list of pairs of sentids and regexp patterns: [([sentid],regpat), ...]
        # and returns a sentid list that actually matches to the patterns.
        # Unless ALL the patterns match, it returns a null.
        for (sentids,pat) in contexts:
          # make the list in ascending order.
          sentids.reverse()
          for sentid in sentids:
            try:
              sent = idx_sent(idx, docid, sentid)
            except KeyError:
              continue
            if not pat or pat.search(sent):
              filtered.append(sentid)
              break
          else:
            if not self.disjunctive:
              pol = -1
              break
        else:
          if filtered:
            pol = 1
            self.snippets[hit] = filtered
      if 0 < pol:
        self.found_docs.append(hit)
        yield hit
      # Abort if the specified time is passed.
      if self.timeout and t0+self.timeout <= time():
        raise SearchTimeout(self)
    return

  # Receives a Selection object that has a list of sentid (contexts)
  # of hit words, and returns a snippet string where highlighted parts
  # are processed by "highlight" func. and normal parts by "normal" func.
  def get_snippet(self, hit, 
                  normal=lambda x:x, highlight=lambda x:x,
                  maxsents=3, maxchars=100, maxlr=20, 
                  default_snippet_sentid=0):
    # Normally it assumes that self.iter() is already called 
    # so the contexts for this location is not empty. When it is empty,
    # fill out with the default snippet string.
    (idx, docid) = hit
    try:
      (loc, mtime) = idx_docid2info(idx, docid)
    except KeyError:
      raise
    try:
      title = idx_sent(idx, docid, 0)
    except KeyError:
      title = None
    contexts = self.snippets.get(hit, [default_snippet_sentid])
    snippet = u''
    sentid0 = None
    for sentid in sorted(contexts):
      # Avoid repeating.
      if sentid0 == sentid: continue
      # For each position, we take maxsents sentences.
      text = ''
      try:
        for (i,s) in enumerate(idx_sents(idx, docid, sentid)):
          if text:
            text += ' '
          text += s
          if maxsents <= i+1 or maxchars <= len(text): break
      except KeyError:
        pass
      x = self.matched_range(text)
      if len(x) == 1:
        # No highlight (no pattern specified).
        snippet += normal(text[:maxchars]) + u'...'
      else:
        # Highlight the matched parts.
        assert 3 <= len(x)
        # prepend the leftmost context.
        (state,left) = x[0]
        if not state:
          snippet += u'... ' + normal(left[-maxlr:])
        for (state,s) in x[1:-1]:
          if not s: continue
          if state:
            snippet += highlight(s)
          else:
            snippet += normal(s)
        # append the rightmost context.
        (state,right) = x[-1]
        if not state:
          snippet += normal(right[:maxlr]) + u'...'
      if maxchars-len(snippet) < maxlr: break
      sentid0 = sentid
    return (loc, mtime, title, snippet)

  def matched_range(self, s):
    r = []
    for pred in self.pos_preds:
      pat = pred.matchpat
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

  def get_status(self):
    # Get the number of all documents.
    found_docs = len(self.found_docs)
    total_docs = self._indexdb.total_docs()
    (searched_docs0, searched_docs1) = self.searched_docs
    searched_docs = searched_docs0 + searched_docs1
    if searched_docs != total_docs:
      # Estimate the number of searched documents,
      # assuming (start_docid ==
      #           the number of unscanned docs in the current idx).
      (_,docid) = self.start_loc
      # rate = (# of found documents) / (# of searched documents)
      estimated = found_docs * (total_docs-searched_docs) / lowerbound(searched_docs, 1)
      found_docs += estimated
    return (searched_docs == total_docs, found_docs)

  def save_status(self):
    from base64 import b64encode
    (idxid, docid) = self.start_loc
    return b64encode(pack('>HiH', idxid, docid, len(self.found_docs)))

  def load_status(self, x):
    from base64 import b64decode
    try:
      (idxid0, docid0, found_docs) = unpack('>HiH', b64decode(x))
    except:
      return
    # put dummy locs (max. 65535)
    self.start_loc = (idxid0, docid0)
    self.found_docs = [None] * found_docs
    searched_docs0 = 0
    for (idxid,idx) in self._indexdb.iteridxs(end=idxid0-1):
      (ndocs, _) = idx_info(idx)
      searched_docs0 += ndocs
    self.searched_docs = (searched_docs0, ndocs-docid0)
    return


# Returns True if the given string can be yomi-keyword.
def canbe_yomi(s):
  import romm
  if s.startswith('.'): return False
  for m in romm.PARSE_DEFAULT.parse(s):
    if not isinstance(m, romm.Mora): return False
  return True

# parse_preds
QUERY_PAT = re.compile(r'"[^"]+"|\S+', re.UNICODE)
ALPHA = re.compile(r'^[-a-zA-Z]+$')
def parse_preds(query, max_preds=10,
                predtype=KeywordPredicate,
                yomipredtype=None):
  terms = []
  yomiterms = []
  for m in QUERY_PAT.finditer(query):
    s = m.group(0)
    if s[0] == '"' and s[-1] == '"':
      s = s[1:-1]
    terms.append(s)
    if yomipredtype and canbe_yomi(s):
      yomiterms.append(s)
    if max_preds <= len(terms): break
  if len(yomiterms) == len(terms):
    if len(terms) == 1 and ALPHA.match(terms[0]):
      return (True, [ predtype(terms[0]), yomipredtype(terms[0]) ])
    else:
      return (False, [ yomipredtype(s) for s in terms ])
  return (False, [ predtype(s) for s in terms ])
