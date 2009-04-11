#!/usr/bin/env python
##
##  htmlripper.py
##

import sys, re, codecs
from sgmlparser3 import SGMLParser3
from util import EOS_PAT_HTML, EOS_PAT_PRE


__all__ = [
  'HTMLRipper'
  ]


##  HTMLRipper
##
##  Here we need to give up charset detecting by <meta> tags,
##  because the files might be scanned from the middle so
##  it will miss the headers.
##
BR_TAGS = set('br p div li dd dt td th h1 h2 h3 h4 h5 h6 title pre blockquote address'.split(' '))
IGNORE_TAGS = set('comment script style'.split(' '))
class HTMLRipper(SGMLParser3):

  def __init__(self):
    SGMLParser3.__init__(self)
    self.eos_pat = EOS_PAT_HTML
    self.text = u''
    self.para = []
    self.ignore = False
    return
  
  def handle_start_tag(self, tag, attrs):
    if tag in IGNORE_TAGS:
      self.start_cdata(tag)
      self.ignore = True
      return
    if tag in BR_TAGS:
      self.flush()
    if tag == 'pre':
      self.eos_pat = EOS_PAT_PRE
    elif tag == 'img':
      attrs = dict(attrs)
      if attrs.get('alt'):
        self.text += '[%s]' % (attrs['alt'])
    return
  
  def handle_end_tag(self, tag, _):
    if tag in IGNORE_TAGS:
      self.ignore = False
      return
    if tag in BR_TAGS:
      self.flush()
    if tag == 'pre':
      self.eos_pat = EOS_PAT_HTML
    return
  
  def handle_decl(self, name):
    return
  
  def handle_directive(self, name, attrs):
    return
  
  def finish(self):
    self.flush()
    return
  
  def flush(self, i=0):
    self.para.append(self.text)
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

  def feedfile(self, fp, encoding):
    decoder = codecs.getdecoder(encoding)
    for line in fp:
      self.para = []
      self.feed(decoder(line, 'replace')[0])
      for x in self.para:
        yield x
    self.finish()
    for x in self.para:
      yield x
    return
  
  def feedunicode(self, s):
    self.feed(s)
    self.finish()
    return self.para

# test
if __name__ == '__main__':
  for fname in sys.argv[1:]:
    fp = file(fname)
    for (pos,sent) in HTMLRipper().feedfile(fp, 'euc-jp'):
      print pos, sent.strip().encode('euc-jp', 'replace')
    fp.close()
