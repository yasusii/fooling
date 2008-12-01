#!/usr/bin/env python
# -*- coding: euc-jp -*-
import re, sys
from util import zen2han, rsplit, encodew, encodey
from util import splitchars, rdatefeats, lowerbound
from util import intersect, merge, union, decode_array, idx_sent, idx_sents, idx_info, idx_docid2info
from struct import pack, unpack
from array import array

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


##  Predicate
##
class Predicate(object):

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


class IsZeroPos(object):
  def __call__(self, pos):
    return pos == 0

class KeywordPredicate(Predicate):

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
      self.pos_filter = IsZeroPos()
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
class IsHeaderPos(object):
  def __call__(self, pos):
    return pos < 100

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

  def setup(self, s):
    m = self.HEADER_PAT.match(s)
    if not m:
      KeywordPredicate.setup(self, s)
      return
    (h,s) = m.groups()
    h = h.lower()
    self.pos_filter = IsHeaderPos()
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
class YomiMixin(object):
  
  def __str__(self):
    return '{%s}' % self.q

  def setup_keyword(self, s):
    import romm, yomi
    morae = romm.PARSE_DEFAULT.parse(s)
    q = ''.join( unicode(m) for m in morae if isinstance(m, romm.Mora) )
    y = yomi.canonicalize_yomi(yomi.encode_yomi(q))
    self.r1 = [ encodey(c1+c2) for (c1,c2) in zip(y[:-1],y[1:]) ]
    self.extpat = yomi.YomiPattern(y)
    self.checkpat = self.extpat
    return


##  StrictMixin
##
class StrictMixin(object):

  ALL_ALPHABET = re.compile(ur'^\|?[\w\s]+\|?$', re.I | re.UNICODE)

  def __str__(self):
    return '<%s>' % self.q

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
class Selection(object):

  def __init__(self, indexdb, term_preds, doc_preds=None,
               safe=True, start_loc=None, end_loc=None,
               disjunctive=False):
    self._indexdb = indexdb

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
    # (We don't store Document objects to avoid having them pickled!)
    self.narrowed = 0
    self.found_docs = []                # [loc, ...]
    self.snippets = {}                  # { loc:[pos, ...], ... }
    return

  def __repr__(self):
    return ('<Selection: indexdb=%r, term_preds=%r, doc_preds=%r, '
            'start_loc=%r, end_loc=%r, found_docs=%r>') % \
           (self._indexdb, self.pos_preds+self.neg_preds, self.doc_preds,
            self.start_loc, self.end_loc, self.found_docs)

  def __len__(self):
    return len(self.found_docs)

  def __getitem__(self, i):
    return self.get(i)

  def __iter__(self):
    return self.iter()

  def get_preds(self):
    return (self.pos_preds + self.neg_preds)

  def get(self, i, timeout=0):
    if len(self.found_docs) <= i:
      j = None
      for (j,loc) in self.start_search(timeout):
        if i <= j: break
      if i == j:
        return loc
    # might cause IndexError
    return self.found_docs[i]
  
  def iter(self, start=0, timeout=0):
    if len(self.found_docs) < start:
      raise ValueError('invalid start index: %d' % start)
    # Return the existing results first.
    for i in xrange(start, len(self.found_docs)):
      yield (i, self.found_docs[i])
    # Now retrieve new results.
    for x in self.start_search(timeout):
      yield x
    return
    
  def status(self):
    # Get the number of all documents.
    found_docs = len(self.found_docs)
    total_docs = self._indexdb.total_docs()
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
    for (idxid,idx) in self._indexdb.iteridxs(start_idx, end_idx):
      (idx_docs, _) = idx_info(idx)
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
              contexts = array('i')
              docs1[docid] = contexts
            else:
              contexts = docs1[docid]
            contexts.append(pos)
          # combine with the previous docs.
          for (docid,contexts) in docs1.iteritems():
            if docid not in docs:
              r = []
              docs[docid] = r
            else:
              r = docs[docid]
            r.append((contexts, pred.checkpat))

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
              contexts = array('i')
              docs1[docid] = contexts
            else:
              contexts = docs1[docid]
            contexts.append(pos)
          if conj:
            # intersect with the previous docs.
            for (docid,contexts) in docs1.iteritems():
              r = docs[docid]
              r.append((contexts, pred.checkpat))
              docs1[docid] = r
            docs = docs1
          else:
            conj = True
            docs = dict( (docid,[(a, pred.checkpat)]) for (docid,a)
                         in docs1.iteritems() )

      # docs: the candidate documents in the current index file.
      docs = docs.items()
      docs.sort(reverse=True)
      found = set()
      for (docid,contexts) in docs:
        self.start_loc = (idxid, docid)
        self.searched_docs = (searched_docs0, idx_docs-docid)
        # Skip if the document is already in the list.
        if docid in found: continue
        found.add(docid)
        yield (idx,docid,contexts)

      # Finished this index.
      searched_docs0 += idx_docs
      self.searched_docs = (searched_docs0, 0)
    return

  def start_search(self, timeout=0):
    from time import time
    limit_time = 0
    if timeout:
      limit_time = time() + timeout

    for (idx,docid,contexts) in self.get_docids():
      pol = 0
      if self.doc_preds:
        # Apply the document predicates.
        (_,loc) = idx_docid2info(idx, docid)
        for pred in self.doc_preds:
          pol = pred(loc)
          if pol: break
      # pol < 0: rejected immediately.
      # pol > 0: accepted immediately.
      # pol = 0: not decided (further examination required).
      self.narrowed += 1
      if pol == 0:
        # contexts (a list of pos) is stored in descending order in an index file.
        filtered = []
        # Receives a list of pairs of positions and regexp patterns: [([pos],regpat), ...]
        # and returns a position list that actually matches to the patterns.
        # Unless ALL the patterns match, it returns a null.
        for (posseq,pat) in contexts:
          # make the list in ascending order.
          posseq.reverse()
          for pos in posseq:
            try:
              sent = idx_sent(idx, docid, pos)
            except KeyError:
              continue
            if not pat or pat.search(sent):
              filtered.append(pos)
              break
          else:
            if not self.disjunctive:
              pol = -1
              break
        else:
          if filtered:
            pol = 1
            self.snippets[(idx,docid)] = filtered
      if 0 < pol:
        loc = (idx,docid)
        self.found_docs.append(loc)
        yield (len(self.found_docs)-1, loc)
      # Abort if the specified time is passed.
      if limit_time and limit_time < time():
        raise SearchTimeout(self)
    return

  # Receives a Selection object that has a list of position (contexts)
  # of hit words, and returns a snippet string where highlighted parts
  # are processed by "highlight" func. and normal parts by "normal" func.
  def get_snippet(self, loc, 
                  normal=lambda x:x, highlight=lambda x:x,
                  maxsents=3, maxchars=100, maxlr=20, 
                  default_snippet_pos=0):
    # Normally it assumes that self.iter() is already called 
    # so the contexts for this location is not empty. When it is empty,
    # fill out with the default snippet string.
    (idx, docid) = loc
    contexts = self.snippets.get(loc, [default_snippet_pos])
    try:
      title = idx_sent(idx, docid, 0)
    except KeyError:
      title = None
    snippet = u''
    pos0 = None
    for pos in sorted(contexts):
      # Avoid repeating.
      if pos0 == pos: continue
      # For each position, we take maxsents sentences.
      sents = []
      chars = 0
      for s in idx_sents(idx, docid, pos):
        sents.append(s)
        chars += len(s)
        if maxsents <= len(sents) or maxchars <= chars: break
      sents = ' '.join(sents)
      x = self.matched_range(sents)
      if len(x) == 1:
        # No highlight (no pattern specified).
        snippet += normal(sents[:maxchars]) + u'...'
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
      pos0 = pos
    (mtime, loc) = idx_docid2info(idx, docid)
    return (mtime, loc, title, snippet)

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


##  SelectionWithContinuation
##
class SelectionWithContinuation(Selection):
  
  def iter(self, start=0, timeout=0):
    if start != len(self.found_docs):
      raise ValueError('Cannot retrieve previous results.')
    return self.start_search(timeout)
  
  def save_continuation(self):
    from base64 import b64encode
    (idxid, docid) = self.start_loc
    return b64encode(pack('>HiH', idxid, docid, len(self.found_docs)))

  def load_continuation(self, x):
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
      (idx_docs, _) = idx_info(idx)
      searched_docs0 += idx_docs
    self.searched_docs = (searched_docs0, idx_docs-docid0)
    return


##  DummySelection
##
class DummySelection(object):
  
  def __init__(self, locs):
    self.locs = locs
    return
  
  def __repr__(self):
    return '<DummySelection: locs=%r>' % (self.locs)
  
  def __len__(self):
    return len(self.locs)

  def __getitem__(self, i):
    return self.get(i)

  def __iter__(self):
    return self.iter()

  def get_preds(self):
    return []

  def matched_range(self, s):
    return [(False, s)]

  def get(self, i):
    return self.locs[i]

  def iter(self, start=0, timeout=0):
    for i in xrange(start, len(self.locs)):
      yield (i, self.locs[i])
    return

  def status(self):
    return (True, len(self.locs))


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


##  search
##
def show_results(selection, n, encoding, timeout=0):
  def e(s): return s.encode(encoding, 'replace')
  window = []
  for (found,loc) in selection.iter(timeout=timeout):
    (mtime, loc, title, s) = selection.get_snippet(loc,
                                                   highlight=lambda x: '\033[31m%s\033[m' % x,
                                                   maxchars=200, maxlr=100)
    print '%d: [%s] %s' % (found+1, e(title or 'unknown'), e(s))
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
  from corpus import IndexDB
  def usage():
    print ('usage: %s [-d] [-T timeout] [-s|-Y] [-S] [-D] [-a] '
           '[-c savefile] [-b basedir] [-p prefix] [-t doctype] '
           '[-e encoding] [-n results] idxdir [keyword ...]') % argv[0]
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(argv[1:], 'dT:sYSDac:b:p:t:e:n:')
  except getopt.GetoptError:
    usage()
  debug = 0
  timeout = 0
  safe = True
  stat = False
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
    elif k == '-a': stat = True
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
    indexdb = IndexDB(idxdir, prefix)
    preds = [ predtype(unicode(kw, encoding)) for kw in keywords ]
    selection = Selection(indexdb, preds, safe=safe, disjunctive=disjunctive)
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

  if stat:
    print '%.2f sec, %d/%d hit' % (time.time()-t0, len(selection.found_docs), selection.narrowed)
  return

# main
if __name__ == '__main__': search(sys.argv)
