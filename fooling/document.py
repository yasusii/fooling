#!/usr/bin/env python
# -*- coding: euc-jp -*-

import sys, re, codecs
from util import idatefeats
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO


__all__ = [ 'Document', 'PlainTextDocument', 'SourceCodeDocument',
            'EMailDocument', 'HTMLDocument' ]


##  Document (abstract)
##
##  A Document represents a indexable document.
##  It does not necessarily contain actual data, but must be
##  able to return all the sentences and terms contained.
##  It has a reference to the Corpus which it belongs.
##  A subclass must at least implement get_sents() method.
##
class Document(object):

  # Document.__init__ must immediately return!
  def __init__(self, corpus, loc):
    self.corpus = corpus
    self.loc = loc
    return

  def get_fp(self):
    return self.corpus.loc_fp(self.loc)
  def get_encoding(self):
    return self.corpus.loc_encoding(self.loc)
  def get_title(self):
    return self.corpus.loc_title(self.loc)

  # (overridable)
  # Returns
  def get_mtime(self):
    return self.corpus.loc_mtime(self.loc)
  
  # (overridable)
  # Returns a list (or generator) of document-specific features.
  def get_feats(self):
    return idatefeats(self.get_mtime())

  def get_subdocs(self):
    return []

  # (overridable)
  # Returns a list (or generator) of all sentences.
  def get_sents(self):
    raise NotImplementedError
  

##  PlainTextDocument
##
EOS_PAT = re.compile(ur'[。．！？!?]|[^- ,\w]\n', re.UNICODE)
class PlainTextDocument(Document):

  def __repr__(self):
    return '<PlainTextDocument: %r>' % self.loc

  def get_sents(self):
    decoder = codecs.getdecoder(self.get_encoding())
    # split sentences
    buf = u''
    pos = 0
    for line in self.get_fp():
      buf += decoder(line, 'replace')[0]
      while 1:
        m = EOS_PAT.search(buf, pos)
        if not m: break
        yield buf[pos:m.end(0)]
        pos = m.end(0)
    yield buf[pos:]
    return
  
  
##  SourceCodeDocument
##
class SourceCodeDocument(Document):

  def __repr__(self):
    return '<SourceCodeDocument: %r>' % self.loc

  def get_sents(self):
    decoder = codecs.getdecoder(self.get_encoding())
    for line in self.get_fp():
      yield decoder(line, 'replace')[0]
    return
  
  
##  HTMLDocument
##
class HTMLDocument(Document):

  def __repr__(self):
    return '<HTMLDocument: %r>' % self.loc

  def get_sents(self):
    from htmlripper import HTMLRipper
    return HTMLRipper().feedfile(self.get_fp(), self.get_encoding())


##  EMailDocument
##
def decode_header(s):
  from email import Header
  def d(s,c):
    try:
      return s.decode(c or 'latin1', 'ignore')
    except LookupError:
      return s.decode('latin1', 'ignore')
  try:
    s = u' '.join( d(s1,t1) for (s1,t1) in Header.decode_header(s) )
  except Header.HeaderParseError:
    s = s.decode('latin1', 'ignore')
  return s

class EMailPartMixin(object):
  
  DEFAULT_CHARSET = 'iso-2022-jp'
  INDEX_HEADERS = set(( 'from', 'subject', 'to', 'cc', 'bcc', 'date' ))

  def __init__(self, msg, mtime):
    self.msg = msg
    self.mtime = mtime
    self.init_headers()
    return

  def get_fp(self):
    assert not self.msg.is_multipart()
    return StringIO(self.msg.get_payload(decode=True))

  def init_headers(self):
    from email import Header, Errors, Utils
    self.headers = []
    self.title = None
    for h in self.msg.keys():
      for s in (self.msg.get_all(h) or []):
        if not s: continue
        v = decode_header(s)
        self.headers.append((h, v))
        if h.lower() == 'date':
          self.mtime = int(Utils.mktime_tz(Utils.parsedate_tz(v)))
        elif h.lower() == 'subject':
          self.title = v
    if not self.title:
      fname = self.msg.get_filename()
      if fname:
        self.title = decode_header(fname)
    return
  
  def get_mtime(self):
    return self.mtime
  
  def get_title(self):
    return self.title

  def get_headers(self):
    for (h,v) in self.headers:
      if h.lower() in self.INDEX_HEADERS:
        yield '%s: %s' % (h, v)
    return
  
  def get_encoding(self):
    return self.msg.get_content_charset() or self.DEFAULT_CHARSET

class EMailMessageMixin(object):
  
  MSGID_HEADERS = { 'message-id':'\x80', 'in-reply-to':'\x81', 'references':'\x81' }
  MSGID_PAT = re.compile(r'<([^>]+)>')
  
  def __init__(self): raise NotImplementedError

  def get_feats(self):
    if self.mtime:
      for x in idatefeats(self.mtime):
        yield x
    for (h,s) in self.headers:
      try:
        prop = self.MSGID_HEADERS[h.lower()]
        for m in self.MSGID_PAT.finditer(s):
          yield prop+m.group(1).encode('utf-8')
      except KeyError:
        pass
    return

  def get_subdocs(self):
    subdocs = []
    if self.msg.is_multipart():
      for (i,submsg) in enumerate(self.msg.walk()):
        if submsg.is_multipart(): continue
        subloc = self.corpus.get_subloc(self.loc, i)
        content_type = submsg.get_content_type()
        encoding = submsg.get_content_charset()
        if content_type == 'text/plain':
          subdocs.append( EMailTextDocument(self.corpus, subloc, submsg, self.mtime) )
        elif content_type == 'text/html':
          subdocs.append( EMailHTMLDocument(self.corpus, subloc, submsg, self.mtime) )
        elif content_type.startswith('message/'):
          subdocs.append( EMailMessageDocument(self.corpus, subloc, submsg, self.mtime) )
    return subdocs

class EMailTextDocument(EMailPartMixin, PlainTextDocument):
  
  def __init__(self, corpus, loc, msg, mtime):
    PlainTextDocument.__init__(self, corpus, loc)
    EMailPartMixin.__init__(self, msg, mtime)
    return
  
  def __repr__(self):
    return '<EmailTextDocument: %r>' % self.loc
  
  def get_sents(self):
    for x in EMailPartMixin.get_headers(self):
      yield x
    for x in PlainTextDocument.get_sents(self):
      yield x
    return
  
class EMailHTMLDocument(EMailPartMixin, HTMLDocument):
  
  def __init__(self, corpus, loc, msg, mtime):
    HTMLDocument.__init__(self, corpus, loc)
    EMailPartMixin.__init__(self, msg, mtime)
    return
  
  def __repr__(self):
    return '<EmailHTMLDocument: %r>' % self.loc
  
  def get_sents(self):
    for x in EMailPartMixin.get_headers(self):
      yield x
    for x in HTMLDocument.get_sents(self):
      yield x
    return
  
class EMailMessageDocument(EMailPartMixin, EMailMessageMixin, PlainTextDocument):
  
  def __init__(self, corpus, loc, msg, mtime):
    PlainTextDocument.__init__(self, corpus, loc)
    EMailPartMixin.__init__(self, msg, mtime)
    return
  
  def __repr__(self):
    return '<EmailMessageDocument: %r>' % self.loc

  def get_sents(self):
    for x in EMailPartMixin.get_headers(self):
      yield x
    if not self.msg.is_multipart():
      for x in PlainTextDocument.get_sents(self):
        yield x
    return

class EMailDocument(EMailMessageDocument):

  MAX_MESSAGE_SIZE = 1000000

  def __init__(self, corpus, loc):
    from email.Parser import FeedParser
    p = FeedParser()
    fp = corpus.loc_fp(loc)
    p.feed(fp.read(self.MAX_MESSAGE_SIZE))
    fp.close()
    EMailMessageDocument.__init__(self, corpus, loc, p.close(), corpus.loc_mtime(loc))
    return
  
  def __repr__(self):
    return '<EmailDocument: %r>' % self.loc


# get_doctype
DOCTYPES = {
  'T': PlainTextDocument,
  'PlainText': PlainTextDocument,
  'PlainTextDocument': PlainTextDocument,
  'C': SourceCodeDocument,
  'SourceCode': SourceCodeDocument,
  'SourceCodeDocument': SourceCodeDocument,
  'H': HTMLDocument,
  'HTML': HTMLDocument,
  'HTMLDocument': HTMLDocument,
  'E': EMailDocument,
  'EMail': EMailDocument,
  'EMailDocument': EMailDocument,
  }
def get_doctype(doctype):
  return DOCTYPES[doctype]


# test
if __name__ == '__main__':
  class DummyCorpus(object):
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
