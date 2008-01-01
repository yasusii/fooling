#!/usr/bin/env python
# -*- encoding: euc-jp -*-
import sys, re
from os.path import join, dirname
import pycdb
stdout = sys.stdout
stderr = sys.stderr

# open the dictionary
if 'YOMI_DICT' not in globals():
  YOMI_DICT = pycdb.tcdbinit(join(dirname(__file__), 'yomidict.tcdb'))

def encode_yomi(s):
  return ''.join( chr(ord(c)-0x3000) for c in s )
def encode_yomi_hiragana(s):
  return ''.join( chr(ord(c)-0x2fa0) for c in s )
def decode_yomi(s):
  return u''.join( unichr(0x3000+ord(c)) for c in s )

TRANS_TABLE = dict( (chr(ord(k)-0x3000), chr(ord(v)-0x3000)) for (k,v) in
  [
  (u'ヂ', u'ジ'),  # ヂ → ジ
  (u'ヅ', u'ズ'),  # ヅ → ズ
  #(u'ヲ', u'オ'),  # ヲ → オ
  #(u'ヴ', u'ブ'),  # ヴ → ブ
  ] )
CAN1 = ''.join( chr(ord(c)-0x3000) for c in u'オコゴソゾトドノホボポモヨロョ' )
CAN2 = ''.join( chr(ord(c)-0x3000) for c in u'ウオ' )
CAN_TRANS = ''.join( TRANS_TABLE.get(chr(c),chr(c)) for c in xrange(256) )
CAN_PAT = re.compile('(['+CAN1+'])['+CAN2+']')
def canonicalize_yomi(y):
  return CAN_PAT.sub('\\1\xfc', y.translate(CAN_TRANS))


# expand_yomis: split bytes into a list of bytes.
def expand_yomis(s):
  n = 0
  r = ''
  for c in s:
    if not n:
      if r: yield r
      n = ord(c)
      r = ''
    else:
      r += c
      n -= 1
  if r: yield r
  return


##  index_yomi:
##  returns bigrams of yomi-characters.
##
CHARTYPE = {}
for i in xrange(0x3041, 0x3093+1):
  CHARTYPE[i] = 1  # kana
for i in xrange(0x30a1, 0x30f4+1):
  CHARTYPE[i] = 1  # kana
for i in xrange(0x4e00, 0x9fff+1):
  CHARTYPE[i] = 2  # kanji
for c in u'\r\n\t ,.-=()"\'　・、−＝「」『』“”（）':
  CHARTYPE[ord(c)] = 3  # transparent
del i,c
CHARTYPE.update({
  0x3005: 2,  # kanji: "々"
  0x3006: 2,  # kanji: "〆"
  0x306f: 2,  # kanji: "は"
  0x3078: 2,  # kanji: "へ"
  0x30f5: 2,  # kanji: "ヵ"
  0x30f6: 2,  # kanji: "ヶ"
  0x30fc: 1,  # kana: "ー"
  })
  
def index_yomi(sent):
  chars = [ c.encode('utf-8') for c in sent ]
  context = [ set() for _ in sent ]
  e = len(sent)
  i = 0
  c0 = None

  while i < e:
    c = ord(sent[i])
    t = CHARTYPE.get(c)
    if t == 1:                          ### KANA
      if c < 0x30a0:
        cur = chr(c - 0x2fa0)           # hirakana
      else:
        cur = chr(c - 0x3000)           # katakana
      if c0 and (c0 in CAN1) and (cur in CAN2):
        cur = '\xfc'                    # chouon
      cur = TRANS_TABLE.get(cur, cur)
      c0 = cur
      context[i].add(cur)
      if 0 < i:
        for prev in context[i-1]:
          yield prev+cur
    elif t == 2:                        ### KANJI
      c0 = None
      try:
        p = 0L
        j = i
        if 0 < i:
          prevs = context[i-1]
        else:
          prevs = []
        while j < e:
          (v,p) = YOMI_DICT.lookup1(chars[j], p)
          if v:  # reaches the end.
            for w in expand_yomis(v):
              if 0 < j:
                for prev in prevs:
                  yield prev+w[0]
              for k in range(1, len(w)):
                yield w[k-1]+w[k]
              context[j].add(w[-1])
          j += 1
      except KeyError:
        pass
    elif t == 3:                        ### TRANSPARENT
      c0 = None
      context[i] = context[i-1]

    i += 1
  return


##  grep_yomi
##
def grep_yomi(yomi, sent, start=0):
  chars = [ c.encode('utf-8') for c in sent ]
  match = [ [(i,0)] for i in xrange(start, len(sent)+1) ]
  e = len(sent)
  pos = start
  c0 = None

  while pos < e:
    c = ord(sent[pos])
    t = CHARTYPE.get(c)
    if t == 1:                          ### KANA
      if c < 0x30a0:
        cur = chr(c - 0x2fa0)           # hirakana
      else:
        cur = chr(c - 0x3000)           # katakana
      if c0 and (c0 in CAN1) and (cur in CAN2):
        cur = '\xfc'                    # chouon
      cur = TRANS_TABLE.get(cur, cur)
      c0 = cur
      r = match[pos+1]
      for (i0,b) in match[pos]:
        if b < len(yomi) and cur == yomi[b]:
          r.append((i0, b+1))
    elif t == 2:                        ### KANJI
      try:
        p = 0L
        j = pos
        bs = match[pos]
        while j < e:
          (v,p) = YOMI_DICT.lookup1(chars[j], p)
          j += 1
          if v:  # reaches the end.
            r = match[j]
            for w in expand_yomis(v):
              for (i0,b) in bs:
                if yomi[b:b+len(w)] == w:
                  r.append((i0,b+len(w)))
      except KeyError:
        pass
    elif t == 3:                        ### OTHERS
      match[pos+1] = match[pos]

    pos += 1
  for (e,r) in enumerate(match):
    for (b,n) in r:
      if n == len(yomi):
        yield (b,e)
  return


##  Pattern and Match object
##
class YomiPattern:

  class Match:

    def __init__(self, re, string, spans):
      self.re = re
      self.string = string
      self.spans = spans
      return

    def groups(self):
      return [ self.string[b:e] for (b,e) in self.spans ]

    def span(self, i=0):
      return self.spans[i]

    def group(self, i=0):
      (b,e) = self.spans[i]
      return self.string[b:e]

    def start(self, i=0):
      return self.spans[i][0]

    def end(self, i=0):
      return self.spans[i][1]
  
  def __init__(self, s):
    self.yomi = s
    return

  def __repr__(self):
    return '<YomiPattern: %r>' % decode_yomi(self.yomi)
  
  def search(self, s, start=0):
    for (b,e) in grep_yomi(self.yomi, s, start):
      return self.Match(self, s, [(b,e)])
    return None
  
  def finditer(self, s, start=0):
    for (b,e) in grep_yomi(self.yomi, s, start):
      yield self.Match(self, s, [(b,e)])
    return


# test
if __name__ == '__main__':
  import unittest
  # index_yomi
  class TestIndexYomi(unittest.TestCase):

    def assertTokens(self, x, y):
      print '====', x.encode('euc-jp')
      r = set( decode_yomi(w) for w in index_yomi(x) )
      print ' '.join(sorted(y.split(' '))).encode('euc-jp')
      print ' '.join(sorted(r)).encode('euc-jp')
      self.assertEqual(' '.join(sorted(r)), ' '.join(sorted(y.split(' '))))

    def test_00(self):
      self.assertTokens(u'現在',
                        u'ゲン ザイ ンザ')
      return

    def test_01(self):
      self.assertTokens(u'ゲンザイのところ異常なし',
                        u'ゲン ンザ ザイ イノ ノト トコ コロ ロイ '
                        u'イジ ジョ ョー ーナ ナシ ロコ コト トジ '
                        u'トツ ツネ ネナ イツ イト コナ トト')
      return

    def test_02(self):
      self.assertTokens(u'私用でしようがない',
                        u'シヨ ヨー ーデ ワタ タク クシ タシ デシ ーガ ガナ ナイ')
      return

    def test_03(self):
      self.assertTokens(u'はなぢ',
                        u'ハナ ワナ ナジ')
      return


  # grep_yomi
  class TestGrepYomi(unittest.TestCase):

    def assertFound(self, yomi, sent):
      print '"%s" ~= "%s"' % (yomi.encode('euc-jp'), sent.encode('euc-jp'))
      yomi = canonicalize_yomi(encode_yomi(yomi))
      self.assertTrue(list(grep_yomi(yomi, sent)))

    def assertNotFound(self, yomi, sent):
      print '"%s" !~ "%s"' % (yomi.encode('euc-jp'), sent.encode('euc-jp'))
      yomi = canonicalize_yomi(encode_yomi(yomi))
      self.assertFalse(list(grep_yomi(yomi, sent)))

    def test_00(self):
      self.assertFound(u'マモリニハイッテイマス',
                      u'守りに、入っています。')
      return

    def test_01(self):
      self.assertFound(u'ハアリマセン',
                       u'そんなことはアリマセン')
      return

    def test_01a(self):
      self.assertFound(u'ワアリマセン',
                       u'そんなことはアリマセン')
      return

    def test_02(self):
      self.assertFound(u'アシタ',
                       u'明日は雨です')
      return

    def test_03(self):
      self.assertNotFound(u'シタ',
                          u'明日は雨です')
      return

  def main(argv):
    import fileinput
    for line in fileinput.input():
      line = unicode(line.strip(), 'euc-jp')
      print line.encode('euc-jp')
      print ' '.join( decode_yomi(w) for w in index_yomi(line) )
    return 0

  unittest.main()
  #sys.exit(main(sys.argv))
