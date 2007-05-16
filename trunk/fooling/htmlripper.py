#!/usr/bin/env python
# -*- encoding: euc_jp -*-

import sys, re, codecs
from sgmlparser3 import SGMLParser3


__all__ = [ 'HTMLRipper' ]


##  HTMLRipper
##
class HTMLRipper(SGMLParser3):

  BR_TAGS = set('br p div li dd dt td th h1 h2 h3 h4 h5 h6 title pre blockquote address'.split(' '))
  IGNORE_TAGS = set('comment script style'.split(' '))
  EOS_PAT_HTML = re.compile(ur'[。．！？!?]')
  EOS_PAT_PRE = re.compile(ur'[。．！？!?\n]', re.UNICODE)
  
  def __init__(self):
    SGMLParser3.__init__(self)
    self.eos_pat = HTMLRipper.EOS_PAT_HTML
    self.text = u''
    self.para = []
    self.pos0 = 0
    self.ignore = False
    self.uniline = u''
    return
  
  def handle_start_tag(self, tag, attrs):
    if tag in self.IGNORE_TAGS:
      self.start_cdata(tag)
      self.ignore = True
      return
    if tag in self.BR_TAGS:
      self.flush()
    if tag == 'pre':
      self.eos_pat = HTMLRipper.EOS_PAT_PRE
    elif tag == 'img':
      attrs = dict(attrs)
      if attrs.get('alt'):
        self.text += '[%s]' % (attrs['alt'])
    return
  
  def handle_end_tag(self, tag, _):
    if tag in self.IGNORE_TAGS:
      self.ignore = False
      return
    if tag in self.BR_TAGS:
      self.flush()
    if tag == 'pre':
      self.eos_pat = HTMLRipper.EOS_PAT_HTML
    return
  
  def handle_decl(self, name):
    return
  
  def handle_directive(self, name, attrs):
    return
  
  def finish(self):
    self.flush()
    return
  
  def flush(self, i=0):
    self.para.append((self.pos0, self.text))
    self.pos0 = self.linepos + self.bytepos(self.charpos+i)
    self.text = u''
    return
  
  def handle_characters(self, data):
    if self.ignore: return
    i = 0
    while 1:
      m = self.eos_pat.search(data, i)
      if not m:
        self.text += data[i:]
        break
      self.text += data[i:m.end(0)]
      self.flush(m.end(0))
      i = m.end(0)
    return
  
  def feedfile(self, fp, encoding, pos=0):
    fp.seek(pos)
    encoder = codecs.getencoder(encoding)
    decoder = codecs.getdecoder(encoding)
    self.bytepos = (lambda i: len(encoder(self.uniline[:i], 'replace')[0]))
    self.linepos = pos
    self.pos0 = pos
    for line in fp:
      self.para = []
      self.uniline = decoder(line, 'replace')[0]
      self.feed(self.uniline)
      for x in self.para:
        yield x
      self.linepos += len(line)
    self.finish()
    for x in self.para:
      yield x
    return
  
  def feedunicode(self, s, pos=0):
    self.linepos = pos
    self.bytepos = (lambda i: i)
    self.pos0 = pos
    self.para = []
    self.feed(s[pos:])
    self.finish()
    return self.para

# test
if __name__ == '__main__':
  for fname in sys.argv[1:]:
    fp = file(fname)
    for (pos,sent) in HTMLRipper().feedfile(fp, 'euc-jp'):
      print pos, sent.strip().encode('euc-jp', 'replace')
    fp.close()
