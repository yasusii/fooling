#!/usr/bin/env python
# -*- coding: euc-jp -*-
##
##  yomi.py
##

import sys, re
from os.path import join, dirname
from fooling import pycdb
stdout = sys.stdout
stderr = sys.stderr

# open the dictionary
try:
  YOMI_DICT
except NameError:
  YOMI_DICT = pycdb.tcdbinit(join(dirname(__file__), 'yomidict.tcdb'))


def encode_yomi(s):
  return ''.join( chr(ord(c)-0x3000) for c in s )
def decode_yomi(s):
  return u''.join( unichr(0x3000+ord(c)) for c in s )

HIRA2KATA = dict( (unichr(c),unichr(c+96)) for c in xrange(0x3041,0x3094) )
def tokata(s):
  return ''.join( HIRA2KATA.get(c,c) for c in s )

TRANS_TABLE = {
  u'ヂ': u'ジ',  # ヂ → ジ
  u'ヅ': u'ズ',  # ヅ → ズ
  #u'ヲ': u'オ',  # ヲ → オ
  #u'ヴ': u'ブ',  # ヴ → ブ
  }
CAN_TRANS = ''.join( chr(ord(TRANS_TABLE.get(unichr(c+0x3000),unichr(c+0x3000)))-0x3000) for c in xrange(256) )
def canonicalize_yomi(y):
  return y.translate(CAN_TRANS)

A = encode_yomi(u'ア')
I = encode_yomi(u'イ')
U = encode_yomi(u'ウ')
E = encode_yomi(u'エ')
O = encode_yomi(u'オ')
C = encode_yomi(u'ー')
EA = encode_yomi(u'アカガサザタダナハバパマヤラワャァ')
EI = encode_yomi(u'イキギシジチヂニヒビピミリィ')
EU = encode_yomi(u'ウクグスズツヅヌフブプムユルュ')
EE = encode_yomi(u'エケゲセゼテデネヘベペメレェ')
EO = encode_yomi(u'オコゴソゾトドノホボポモヨロョォ')
EUPHS = {}
for c in EA:
  EUPHS[c+A] = C  # カア → カー
for c in EI:
  EUPHS[c+I] = C  # キイ → キー
for c in EU:
  EUPHS[c+U] = C  # クウ → クー
for c in EE:
  EUPHS[c+I] = E+C  # ケイ → ケエ, ケー
  EUPHS[c+E] = I+C  # ケエ → ケイ, ケー
for c in EO:
  EUPHS[c+U] = O+C  # コウ → コオ, コー
  EUPHS[c+O] = U+C  # コオ → コウ, コー
EUPH_PAT = re.compile(r'([%s])%s|([%s])%s|([%s])%s|([%s])[%s]|([%s])[%s]' %
                      (EA, A, EI, I, EU, U, EE, I+E, EO, U+O))
def canonicalize_euph(s):
  return EUPH_PAT.sub(lambda m:m.group(0)[0]+C, s)


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
CHARTYPE = {ord(u'ー'): 1}
for i in xrange(0x3041, 0x3093+1):
  CHARTYPE[i] = 0  # hirakana - MUST NOT APPEAR
for i in xrange(0x30a1, 0x30f4+1):
  CHARTYPE[i] = 1  # katakana
for i in xrange(0x4e00, 0x9fff+1):
  CHARTYPE[i] = 2  # kanji
for c in u'々〆ヵヶハヘ':
  CHARTYPE[ord(c)] = 2  # kanji
for c in u'\r\n\t ,.-=()"\'　・、−＝「」『』“”（）':
  CHARTYPE[ord(c)] = 3  # transparent
del i,c
  
def index_yomi(sent):
  sent = tokata(sent)
  chars = [ c.encode('utf-8') for c in sent ]
  context = [ set() for _ in sent ]
  e = len(sent)
  i = 0

  while i < e:
    c = ord(sent[i])
    t = CHARTYPE.get(c)
    if t == 0:
      raise ValueError(sent)
    elif t == 1:                        ### KANA (katakana)
      cur = canonicalize_yomi(chr(c - 0x3000))
      context[i].add(cur)
      if 0 < i:
        for prev in context[i-1]:
          y = prev+cur
          yield y
          if y in EUPHS:
            for x in EUPHS[y]:
              yield prev+x
              context[i].add(x)
    elif t == 2:                        ### KANJI
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
              r = []
              if 0 < j:
                r.extend( prev+w[0] for prev in prevs )
              r.extend( w[k-1]+w[k] for k in range(1, len(w)) )
              for y in r:
                yield y
                if y in EUPHS:
                  for x in EUPHS[y]:
                    yield y[0]+x
              context[j].add(w[-1])
              if r:
                y = r[-1]
                if y in EUPHS:
                  for x in EUPHS[y]:
                    context[j].add(x)
          j += 1
      except KeyError:
        pass
    elif t == 3:                        ### TRANSPARENT
      context[i] = context[i-1].copy()

    i += 1
  return


##  grep_yomi
##
def grep_yomi(yomi, sent, start=0):
  yomi = canonicalize_yomi(yomi)
  sent = tokata(sent)
  chars = [ c.encode('utf-8') for c in sent ]
  match = [ [(i,0)] for i in xrange(start, len(sent)+1) ]
  e = len(sent)
  pos = start
  prev = None

  while pos < e:
    c = ord(sent[pos])
    t = CHARTYPE.get(c)
    if t == 0:
      raise ValueError(sent)
    elif t == 1:                        ### KANA (katakana)
      cur = canonicalize_yomi(chr(c - 0x3000))
      r = match[pos+1]
      for (i0,b) in match[pos]:
        if len(yomi) <= b: continue
        y = yomi[b]
        if (y == cur) or (prev and y in EUPHS.get(prev+cur, '')):
          r.append((i0, b+1))
      prev = cur
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
              w = canonicalize_euph(w)
              for (i0,b) in bs:
                y = yomi[b:b+len(w)]
                if canonicalize_euph(y) == w:
                  r.append((i0,b+len(w)))
      except KeyError:
        pass
      prev = None
    elif t == 3:                        ### OTHERS
      match[pos+1] = match[pos][:]
      prev = None
    pos += 1
  for (e,r) in enumerate(match):
    for (b,n) in r:
      if n == len(yomi):
        yield (b,e)
  return


##  Pattern and Match object
##
class YomiPattern(object):

  class Match(object):

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
                        u'イジ ジョ ョー ョウ ョオ ウナ オナ ーナ ナシ ロコ '
                        u'コト トジ トツ ツネ ネナ イツ イト コナ トト')
      return

    def test_02(self):
      self.assertTokens(u'私用でしようがない',
                        u'シヨ ヨウ ヨオ ヨー ウデ オデ ーデ ワタ タク '
                        u'クシ タシ デシ ウガ オガ ーガ ガナ ナイ')
      return

    def test_03a(self):
      self.assertTokens(u'はなぢ',
                        u'ハナ ワナ ナジ')
      return
    
    def test_03b(self):
      self.assertTokens(u'鼻血',
                        u'ハナ ナジ ビチ ナチ ビケ ケツ ナケ バナ')
      return


  # grep_yomi
  class TestGrepYomi(unittest.TestCase):

    def assertFound(self, yomi, sent):
      print '"%s" ~= "%s"' % (yomi.encode('euc-jp'), sent.encode('euc-jp'))
      self.assertTrue(list(grep_yomi(encode_yomi(yomi), sent)))

    def assertNotFound(self, yomi, sent):
      print '"%s" !~ "%s"' % (yomi.encode('euc-jp'), sent.encode('euc-jp'))
      self.assertFalse(list(grep_yomi(encode_yomi(yomi), sent)))

    def test_00a(self):
      self.assertFound(u'マモリニハイッテイマス',
                      u'守りに、入っています。')
      return

    def test_00b(self):
      self.assertFound(u'オネガイシマス',
                       u'よろしくお願いします。')
      return

    def test_00c(self):
      self.assertFound(u'ヨクオモワナイ',
                       u'良ク思ワナイ。')
      return

    def test_01a(self):
      self.assertFound(u'オトウサンハ',
                       u'おとうさんは元気ですか')
      return

    def test_01b(self):
      self.assertFound(u'オトーサンワ',
                       u'おとうさんは元気ですか')
      return

    def test_01c(self):
      self.assertFound(u'オトウサンハ',
                       u'お父さんは元気ですか')
      return

    def test_01d(self):
      self.assertFound(u'オトーサンワ',
                       u'お父さんは元気ですか')
      return

    def test_02a(self):
      self.assertFound(u'ケイタイ',
                       u'携帯電話')
      return

    def test_02b(self):
      self.assertFound(u'ケータイ',
                       u'携帯電話')
      return

    def test_02c(self):
      self.assertFound(u'ウマイ',
                       u'激しくうまい')
      return

    def test_02d(self):
      self.assertFound(u'クーマイ',
                       u'激しくうまい')
      return

    def test_03a(self):
      self.assertFound(u'アシタ',
                       u'明日は雨です')
      return

    def test_03b(self):
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
