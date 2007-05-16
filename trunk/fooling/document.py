#!/usr/bin/env python
# -*- encoding: euc-jp -*-

import sys, re, codecs, time
from array import array
from struct import pack
from util import dispw, encodew, isplit, zen2han


__all__ = [ 'Document', 'PlainTextDocument', 'SourceCodeDocument',
            'EMailDocument', 'HTMLDocument' ]


# date features for indexing
def idatefeats(t):
  (yy,mm,dd,_,_,_,_,_,_) = time.localtime(t)
  return ('\x20'+pack('>h',yy),
          '\x20'+pack('>hb',yy,mm),
          '\x20'+pack('>hbb',yy,mm,dd))

# remove redundant blanks
RMSP_PAT = re.compile(r'\s+', re.UNICODE)
def rmsp(s):
  return RMSP_PAT.sub(' ', s.strip())

# returns True if the string contains non-space characters.
NON_SPACE_PAT = re.compile(r'\S', re.UNICODE)
def nonspace(s):
  return NON_SPACE_PAT.search(s)

# get email body
def get_email_body(mpart, default_charset):
  text = mpart.get_payload(decode=True) or ''
  charset = mpart.get_content_charset(default_charset)
  try:
    return text.decode(charset, 'replace')
  except LookupError:
    return text.decode('latin1', 'replace')

# split sentences
EOS_PAT = re.compile(ur'[。．！？!?]|[^- ,\w]\n', re.UNICODE)
def splitsents(s, pos=0):
  while 1:
    m = EOS_PAT.search(s, pos)
    if not m:
      yield (pos, len(s))
      break
    yield (pos, m.end(0))
    pos = m.end(0)
  return


##  Document (abstract)
##
##  A Document represents a indexable document.
##  It does not necessarily contain actual data, but must be
##  able to return all the sentences and terms contained.
##  It has a reference to a parent Corpus.
##  A subclass must at least implement get_sents() method.
##
class Document:

  default_snippet_pos = 0

  # Document.__init__ must immediately return!
  def __init__(self, corpus, loc):
    self.corpus = corpus
    self.loc = loc
    self.fp = None
    return

  # open: Obtain a file-like object and cache it.
  def open(self):
    if not self.fp:
      self.fp = self.corpus.loc_fp(self.loc)
    return self.fp
  
  # close: Close the file-like object (if any).
  def close(self):
    if self.fp:
      self.fp.close()
    self.fp = None
    return

  # Get document modification time.
  def get_mtime(self):
    return self.corpus.loc_mtime(self.loc)

  # (overridable)
  # Returns a list (or generator) of sentences starting from the given pos.
  #
  # NOTICE: get_sents() may call self.open() inside. So any method that
  # calls get_sents() must call self.close() when it exits the function,
  # otherwise unclosed file objects will linger.
  def get_sents(self, pos):
    return NotImplementedError
  
  # (overridable)
  # Returns a list (or generator) of all terms in the document
  # that appear before maxpos.
  def get_terms(self, maxpos):
    yield (0, idatefeats(self.get_mtime()))
    for (pos,sent) in self.get_sents(0):
      #print pos, ' '.join(dispw(isplit(zen2han(sent)))).encode('euc-jp')
      words = set( encodew(w) for w in isplit(zen2han(sent)) )
      yield (pos, words)
      if maxpos <= pos: break
    self.close()
    return

  # (overridable)
  # Returns the document title (string).
  def get_title(self):
    sent = u''
    for (_,sent) in self.get_sents(0):
      sent = sent.strip()
      if sent: break
    self.close()
    return rmsp(sent)

  # Receives a list of pairs of positions and regexp patterns: [([pos],regpat), ...]
  # and returns a position list that actually matches to the patterns.
  # Unless ALL the patterns match, it returns a null.
  def filter_context(self, pospat, disjunctive=False):
    filtered = []
    try:
      # context (a list of pos) is stored in descending order in an index file.
      for (context,pat) in pospat:
        context.reverse()
        # context is ascending order now
        for pos in context:
          sents = self.get_sents(pos)
          try:
            (_,snip1) = sents.next()
          except StopIteration:
            continue
          if not pat or pat.search(zen2han(snip1)):
            filtered.append(pos)
            break
        else:
          if not disjunctive:
            # if not found for all the pos in the context, return empty.
            return []
      return filtered
    finally:
      # Make sure closing the associated file object.
      self.close()

  # Receives a Selection object that has a list of position (context)
  # of hit words, and returns a snippet string where highlighted parts
  # are processed by "highlight" func. and normal parts are
  # by "normal" func.
  def get_snippet(self, selection,
                  normal=lambda x:x, highlight=lambda x:x,
                  maxsents=3, maxchars=100, maxcontext=20):
    # Normally it assumes that filter_context() is already called for 
    # this document so the context is not empty. But if it is empty,
    # fill out with the default snippet string.
    context = selection.get_context(self.loc) or [self.default_snippet_pos]

    snippet = u''
    # Do not repeat sentences.
    context = set(context)
    for pos in sorted(context):
      # For each position, we take maxsents sentences.
      sents = u''
      for (i,(p,s)) in enumerate(self.get_sents(pos)):
        if (p != pos) and (p in context): break
        sents += u' '+s
        if maxsents <= i+1 or maxchars <= len(sents): break
      self.close()
      sents = rmsp(zen2han(sents))
      x = selection.matched_range(sents)
      if len(x) == 1:
        # No highlight (no pattern specified).
        snippet += normal(sents[:maxchars]) + u'...'
      else:
        # Highlight the matched parts.
        assert 3 <= len(x)
        # prepend the leftmost context.
        (state,left) = x[0]
        if not state:
          snippet += u'... ' + normal(left[-maxcontext:])
        for (state,s) in x[1:-1]:
          if state:
            snippet += highlight(s)
          else:
            snippet += normal(s)
        # append the rightmost context.
        (state,right) = x[-1]
        if not state:
          snippet += normal(right[:maxcontext]) + u'...'
      if maxchars-len(snippet) < maxcontext: break
    return snippet


##  PlainTextDocument
##
class PlainTextDocument(Document):

  def __repr__(self):
    return '<PlainTextDocument: %r>' % self.loc

  def get_sents(self, pos0):
    fp = self.open()
    fp.seek(pos0)
    encoding = self.corpus.loc_encoding(self.loc)
    encoder = codecs.getencoder(encoding)
    decoder = codecs.getdecoder(encoding)
    for line in fp:
      uniline = decoder(line, 'replace')[0]
      for (s,e) in splitsents(uniline):
        sent = uniline[s:e]
        if nonspace(sent):
          yield (pos0 + len(encoder(uniline[:s], 'replace')[0]), sent)
      pos0 += len(line)
    return
  
  
##  SourceCodeDocument
##
class SourceCodeDocument(Document):

  def __repr__(self):
    return '<SourceCodeDocument: %r>' % self.loc

  def get_title(self):
    return self.corpus.loc_default_title(self.loc)

  def get_sents(self, pos):
    fp = self.open()
    fp.seek(pos)
    decoder = codecs.getdecoder(self.corpus.loc_encoding(self.loc))
    for line in fp:
      sent = decoder(line, 'replace')[0]
      if nonspace(sent):
        yield (pos, sent)
      pos += len(line)
    return
  
  
##  EMailDocument
##
class EMailParseError(IOError): pass
class EMailDocument(Document):

  MAX_SIZE = 1000000
  MAX_HEADERS = 100
  MAX_OFFSET = (1<<24)-1
  HEADERS = ['From', 'Subject', 'To', 'Cc', 'Bcc', 'Content-Disposition' ]
  DEFAULT_CHARSET = 'iso-2022-jp'

  SPECIAL_HEADERS = [ ('Message-ID','\x10'), ('In-Reply-To','\x11'), ('References','\x11') ]
  MSGID_PAT = re.compile(r'<([^>]+)>')

  default_snippet_pos = MAX_HEADERS

  def __init__(self, corpus, loc):
    Document.__init__(self, corpus, loc)
    self.msg = None
    self.size = -1
    return

  def __repr__(self):
    return '<EmailDocument: %r>' % self.loc

  def get_msg(self, size=MAX_SIZE):
    size = size or sys.maxint
    if self.size < size:
      from email.Parser import FeedParser
      fp = self.open()
      p = FeedParser()
      if size == sys.maxint:
        p.feed(fp.read())
      else:
        p.feed(fp.read(size))
      self.msg = p.close()
      self.size = size
      self.close()
    return self.msg

  def get_headers(self, msg, headers):
    pos = 0
    from email import Header, Errors
    decode = Header.decode_header
    for h in headers:
      for s in (msg.get_all(h) or []):
        if not s: continue
        try:
          s = rmsp(u' '.join( s1.decode(t1 or self.DEFAULT_CHARSET, 'replace') for (s1,t1) in decode(s) ))
        except LookupError:
          s = rmsp(u' '.join( s1.decode('latin1','replace') for (s1,t1) in decode(s) ))
        except Errors.HeaderParseError:
          s = rmsp(s.decode('latin1', 'replace'))
        yield (pos, h, s)
        pos += 1
        if EMailDocument.MAX_HEADERS <= pos: return
    return

  def get_title(self):
    subject = list(self.get_headers(self.get_msg(), ['Subject']))
    if subject:
      return zen2han(rmsp(subject[0][2]))
    else:
      return ''

  def get_mtime(self):
    from email import Utils
    date = self.get_msg()['date']
    if date:
      try:
        return int(Utils.mktime_tz(Utils.parsedate_tz(date)))
      except:
        pass
    return self.corpus.loc_mtime(self.loc)

  # offset: first 8 bits ... the mime part number.
  #         next 24 bits ... the character offset in *UNICODE*.
  def get_sents(self, pos):
    (partno, offset) = (pos >> 24, pos & EMailDocument.MAX_OFFSET)
    msg = self.get_msg()
    charset = msg.get_content_charset(self.DEFAULT_CHARSET)
    for (p,mpart) in enumerate(msg.walk()):
      if p < partno: continue
      if 255 < partno: break
      baseoffset = (p << 24)
      if offset < EMailDocument.MAX_HEADERS:
        for (pos,h,s) in self.get_headers(mpart, EMailDocument.HEADERS):
          if pos < offset: continue
          yield (baseoffset + pos, '%s: %s' % (h,s))
        offset = EMailDocument.MAX_HEADERS
      maintype = mpart.get_content_maintype()
      if maintype != 'text': continue
      body = get_email_body(mpart, charset)
      subtype = mpart.get_content_subtype()
      baseoffset += offset
      offset -= EMailDocument.MAX_HEADERS
      if subtype == 'html':
        from htmlripper import HTMLRipper
        sents = HTMLRipper().feedunicode(body, offset)
        for (pos,sent) in sents:
          if nonspace(sent):
            yield (baseoffset + pos, sent)
      else:
        sents = splitsents(body, offset)
        for (s,e) in sents:
          sent = body[s:e]
          if nonspace(sent):
            yield (baseoffset + s, sent)
      offset = 0
    return

  def get_terms(self, maxpos):
    msg = self.get_msg()
    yield (0, idatefeats(self.get_mtime()))
    # Handle: Message-ID, Reference, In-Reply-To.
    r = []
    for (h,k) in self.SPECIAL_HEADERS:
      for v in (msg.get_all(h) or []):
        for m in self.MSGID_PAT.finditer(v):
          r.append(k+m.group(1))
    if r:
      yield (0, r)
    for (pos,sent) in self.get_sents(0):
      words = set( encodew(w) for w in isplit(zen2han(sent)) )
      yield (pos, words)
      pos &= EMailDocument.MAX_OFFSET
      if maxpos <= pos: break
    self.close()
    return


##  HTMLDocument
##
class HTMLDocument(Document):

  def __repr__(self):
    return '<HTMLDocument: %r>' % self.loc

  def get_sents(self, pos):
    from htmlripper import HTMLRipper
    encoding = self.corpus.loc_encoding(self.loc)
    sents = HTMLRipper().feedfile(self.open(), encoding, pos)
    if pos == 0:
      # title
      for (_,sent) in sents:
        if nonspace(sent):
          yield (0, sent)
          break
    for (pos,sent) in sents:
      if nonspace(sent):
        yield (pos,sent)
    return


# test
if __name__ == '__main__':
  class DummyCorpus:
    def __init__(self, fname):
      self.fname = fname
      return
    def loc_fp(self, _):
      return file(self.fname)
    def loc_encoding(self, _):
      return 'euc-jp'
  for fname in sys.argv[1:]:
    doc = EMailDocument(DummyCorpus(fname), '')
    for (pos,sent) in doc.get_sents(0):
      print pos, sent.encode('euc-jp').strip()
