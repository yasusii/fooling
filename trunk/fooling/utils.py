#!/usr/bin/env python
# -*- coding: euc-jp -*-

import sys, re
from array import array
from struct import pack, unpack

PROP_WORD  = 0x10
PROP_SENT  = '\x00'
PROP_YOMI  = '\x20'
PROP_EMAIL_MSGID = '\x80'
PROP_EMAIL_REPLY = '\x81'
PROP_EMAIL_REF = '\x82'
PROP_DATE  = '\xf0'
PROP_LABEL = '\xf1'
PROP_DOCID = '\xfd'
PROP_LOC   = '\xfe'
PROP_IDXINFO  = '\xff'

EOS_PAT_PLAIN = re.compile(ur'[。．！？!?]|[^- ,\w]\n', re.UNICODE)
EOS_PAT_HTML = re.compile(ur'[。．！？!?]', re.UNICODE)
EOS_PAT_PRE = re.compile(ur'[。．！？!?\n]', re.UNICODE)


##  Kinsoku
##
WORD_PAT = re.compile(r'''
        [\[{(\'`"‘“〈《「『【〔（［｛]* # open paren
        ([a-zA-Z0-9_\xa0]+|\w)          # core
        [-=:;,.!?ぁぃぅぇぉゃゅょっァィゥェォャュョッ々ゝゞ・…、。：；，．！？\]})\'`"’”〉》」』】〕）］｝]* |
        \S |                            # other chars
        \s+                             # space
        ''', re.VERBOSE | re.UNICODE)


# Detect the endian.
# We always follow the little endian, so if the machine is the big endian, we swap bytes.
SWAP_ENDIAN = (pack('=i',1) == pack('>i',1)) # True if this is the big endian.

##  zenkaku -> hankaku converter
##
FULLWIDTH = u"　！”＃＄％＆’（）＊＋，−．／０１２３４５６７８９：；＜＝＞？" \
            u"＠ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ［＼］＾＿" \
            u"‘ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ｛｜｝〜"

HALFWIDTH = u" !\"#$%&'()*+,-./0123456789:;<=>?" \
            u"@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_" \
            u"`abcdefghijklmnopqrstuvwxyz{|}~"

assert len(FULLWIDTH) == len(HALFWIDTH)
Z2HMAP = dict( (ord(zc), ord(hc)) for (zc,hc) in zip(FULLWIDTH, HALFWIDTH) )

def zen2han(s):
  return unicode(s).translate(Z2HMAP)

# remove redundant blanks
RMSP_PAT = re.compile(r'\s+', re.UNICODE)
def rmsp(s):
  return RMSP_PAT.sub(' ', s.strip())


##  Basic tokenization
##
TOKEN_PAT = re.compile(ur'[a-z0-9_\xc0-\xff]+|.', re.I)
CHARTYPE = array('b', '\x00'*65536)
for (i,cr) in (
  (1,u'az'),                            # alphabet
  (1,u'__'),                            # alphabet 
  (1,u'\xc0\xff'),                      # alphabet ext
  (1,u'09'),                            # numbers
  # Japanese characters.
  (8,u'ぁゞ'),                          # hirakana
  (9,u'ァヴ'),                          # katakana
  (9,u'ーー'),                          # katakana-
  (9,u'\uff66\uff9f'),                  # hankaku kana (unsupported)
  (10,u'\u4e00\u9fff'),                 # kanji
  (10,u'々〆'),                         # kanji ext
  ):
  for c in xrange(ord(cr[0]),ord(cr[1])+1):
    CHARTYPE[c] = i
del i,c

# split characters into roman words or CJK letters
def splitchars(s):
  s = s.strip().lower()
  for m in TOKEN_PAT.finditer(s):
    c = m.group(0)
    try:
      t = CHARTYPE[ord(c[0])]
    except IndexError:
      t = 0
    yield (c,t)
  return

# utilities for tokens
def dispw(r):
  for (b,w) in r:
    yield ('-|'[b >> 1])+w+('-|'[b & 1])
  return

def encodew((b,w), encoding='utf-8'):
  return chr(b | PROP_WORD) + w.encode(encoding)
def encodey(w):
  return PROP_YOMI + w


##  isplit: Tokenization for indexing
##  Sorry, this is awful...
##
def isplit(s):
  # (t3,t2,t1): chartype at s[i-3], s[i-2] and s[i-1].
  (t3, t2, t1) = (0, 0, 0)
  # (c2,c1): character at s[i-2] and s[i-1].
  (c2, c1) = ('', '')
  # sab: separation between s[i-a] and s[i-b]
  (s32, s21, s10) = (0, 0, 1)

  i = 0
  for (c0,t0) in splitchars(s):
    # (c0,t0): char and chartype at s[i].
    #print "-,%d -[%s]- %s,%d -[%s]- %s,%d -[%s]- %s,%d" % \
    #      (t3,s32,c2,t2,s21,c1,t1,s10,c0,t0)
    if t0 == 0:
      # s[i-2]   s[i-1] | s[i-0]
      s10 = 1
      continue
    # (c2,t2)-s21-(c1,t1)-s10-(c0,t0)
    if c1:
      if (t1 != t0) or (t0 & 8) == 0:
        s10 = 1
      # | (c1,t1) |
      # - (c1,t1) |
      # | (c1,t1) -
      # t1==10: kanji
      if (s21 and s10) or (t1 == 10 and (s21 or s10)):
        yield (3, c1)
    if 2 <= i:                          # (c2,t2) is filled
      # (,t3)-s32-(c2,t2)-s21-(c1,t1)-s10-(c0,t0)
      k = c2+c1
      if (t2 | t1) & 8:
        yield (s32 << 1 | s10, k)
      if (t2 & t1 & 8):
        if s32 and t3 == t2:
          yield (s10, k)
        if s10 and t1 == t0:
          yield (s32 << 1, k)
        if s32 and s10 and t3 == t2 and t1 == t0:
          yield (0, k)
    # shift the buffer by one character.
    (c2, c1) = (c1, c0)
    (t3, t2, t1) = (t2, t1, t0)
    (s32, s21, s10) = (s21, s10, 0)
    i += 1

  # last one
  # (,t3)-s32-(c2,t2)-s21-(c1,t1)
  # t1==10: kanji
  if c1 and (s21 or t1 == 10):
    yield (3, c1)
  if 2 <= i:
    k = c2+c1
    if (t2 | t1) & 8:
      yield (s32 << 1 | 1, k)
    if (t2 & 8) and s32 and t3 == t2:
      yield (1, k)
  return


##  rsplit: Tokenization for searching
##
def rsplit(s):
  # (t2,t1): chartype at s[i-2] and s[i-1].
  (t2, t1) = (0, 0)
  # (c2,c1): character at s[i-2] and s[i-1].
  (c2, c1) = ('', '')
  # sab: separation between s[i-a] and s[i-b]
  (s32, s21, s10) = (0, 0, 0)
  # (head, center, tail)
  (r0, r1, r2) = ([], [], [])
  
  i = 0
  for (c0,t0) in splitchars(s):
    # (c0,t0): char and chartype at s[i].
    #print "[%s] %s,%d [%s] %s,%d [%s] %s,%d" % \
    # (s32, c2.encode('euc-jp'),t2, s21, c1.encode('euc-jp'),t1, s10, c0.encode('euc-jp'),t0)
    if t0 == 0:
      # s[i-2]   s[i-1] | s[i-0]
      s10 = 1
      continue
    # (c1,t1)-s10-(c0,t0)
    if i and (t1 != t0) or (t0 & 8) == 0:
      s10 = 1
    if 2 <= i:
      # s32-(c2,t2)-s21-(c1,t1)-s10
      if (t2 | t1) & 8:            # (c2,t2) is filled
        k = c2+c1
        if i == 2 and (t2 & 8):
          # (c2,t1) is the first one and on the boundery.
          assert not r1
          r0.append((2 | s10, k))
          if not s32:
            r0.append((s10, k))
        else:
          r1.append((s32 << 1 | s10, k))
      else:
        # both c2 and c1 is non-japanese.
        r1.append((3, c2))
    (c2,c1) = (c1,c0)
    (t2,t1) = (t1,t0)
    (s32, s21, s10) = (s21, s10, 0)
    i += 1
  # the stream ended -- process the remaining chars.
  if i == 1:
    r1.append((3, c1))
  elif 2 <= i:
    # s32-(c2,t2)-s21-(c1,t1)-s10
    k = c2+c1
    if i == 2 and ((t2 | t1) & 8):
      # only 2 characters.
      assert not r1
      # | c2+c1 |
      r0.append((3, k))
      if not s32 and (t2 & 8):
        # - c2+c1 |
        r0.append((1, k))
      if (t1 & 8) and not s10:
        # | c2+c1 -
        r0.append((2, k))
      if (t2 & t1 & 8) and (not (s32 or s10)):
        # - c2+c1 -
        r0.append((0, k))
    elif t1 & 8:
      # the last one is japanese (on the boundery).
      r2.append((s32 << 1 | 1, k))
      if not s10:
        r2.append((s32 << 1, k))
    elif t2 & 8:
      # c2 is japanese, but c1 is non-japanese.
      r1.append((s32 << 1 | 1, k))
    else:
      # both are non-japanese.
      r1.append((3, c2))
      r1.append((3, c1))
  if len(r0) == 1:
    r1.extend(r0)
    r0 = []
  if len(r2) == 1:
    r1.extend(r2)
    r2 = []
  return (r0, r1, r2)


##  intersect docid sets
##
def intersect(refs0):
  refs = sorted(refs0, key=len)
  ref0 = refs.pop(0)
  poss = [ 0 for r in refs ]
  
  def seek(k):
    j = 0
    for p0 in poss:
      r = refs[j]
      p1 = len(r)-2
      # start=r[p0], end=r[p1]
      #print 'search: k=%r from %r, start=%d, end=%d' % \
      # (unpack('>ll',k), [ unpack('>ll', r[q:q+8]) for q in xrange(0, len(r), 8) ], p0, p1)
      while 1:
        if p1 < p0: break
        p = ((p0+p1) >> 2) << 1
        # p0 <= p <= p1
        m = (r[p], r[p+1])              # m:median
        #print '  p0=%d,p=%d,p1=%d: m=%r' % (p0,p,p1, unpack('>ll', m))
        if k == m:
          # found
          poss[j] = p+2
          break
        if k < m:
          # k < m : [ m, ..., k ] : go right
          poss[j] = p+2
          p0 = p+2
          #print '  right: p0=%d,p=%d,p1=%d' % (p0,p,p1)
        else:
          # m < k : [ k, ..., m ] : go left
          p1 = p-2
          #print '  left: p0=%d,p=%d,p1=%d' % (p0,p,p1)
      if p1 < p0: return False
      j += 1
    #print 'found: k=%r' % k
    return True
  
  a = array('i')
  for i in xrange(0, len(ref0), 2):
    k = (ref0[i], ref0[i+1])
    if seek(k):
      a.extend(k)
  return a


##  union docid sets
##
def union(ref0, refsets):
  unioners = [ (refs, [ 0 for r in refs ]) for refs in sorted(refsets, key=len) ]
  def seek(refs, poss, k):
    j = 0
    for p0 in poss:
      r = refs[j]
      p1 = len(r)-2
      # start=r[p0], end=r[p1]
      #print 'search: k=%r from %r, start=%d, end=%d' % \
      # (k, [ (r[i],r[i+1]) for i in xrange(0,len(r),2) ], p0, p1)
      while 1:
        if p1 < p0: break
        p = ((p0+p1) >> 2) << 1
        # p0 <= p <= p1
        m = (r[p], r[p+1])              # m:median
        #print '  p0=%d,p=%d,p1=%d: m=%r' % (p0,p,p1,m)
        if k == m:
          # found
          poss[j] = p+2
          return True
        if k < m:
          # k < m : [ m, ..., k ] : go right
          poss[j] = p+2
          p0 = p+2
          #print '  right: p0=%d,p=%d,p1=%d' % (p0,p,p1)
        else:
          # m < k : [ k, ..., m ] : go left
          p1 = p-2
          #print '  left: p0=%d,p=%d,p1=%d' % (p0,p,p1)
      j += 1
    #print 'found: k=%r' % k
    return False

  a = array('i')
  for i in xrange(0, len(ref0), 2):
    k = (ref0[i], ref0[i+1])
    for (refs,poss) in unioners:
      if not seek(refs, poss, k): break
    else:
      a.extend(k)
  return a


##  merge docid sets
##
def merge(seqs):
  poss = [ ((r[0],r[1]),r,0) for r in seqs if r ]
  a = array('i')
  v0 = None
  while poss:
    poss.sort()
    (v,r,p) = poss.pop()
    if v != v0:
      a.extend(v)
      v0 = v
    p += 2
    if p < len(r):
      poss.append(((r[p],r[p+1]), r, p))
  return a


##  index file operations
##
COMPRESS_THRESHOLD = 4
def encode_array(n,a):
  from zlib import compress
  if SWAP_ENDIAN:
    a.byteswap()
  if COMPRESS_THRESHOLD <= n:
    bits = compress(a.tostring())
  else:
    bits = a.tostring()
  return pack('>i', n) + bits

def decode_array(bits):
  from zlib import decompress
  (n,) = unpack('>i', bits[:4])
  a = array('i')
  if COMPRESS_THRESHOLD <= n:
    a.fromstring(decompress(bits[4:]))
  else:
    a.fromstring(bits[4:])
  if SWAP_ENDIAN:
    a.byteswap()
  return a

# date features for indexing
def idatefeats(t):
  import time
  assert t != None
  (yy,mm,dd,_,_,_,_,_,_) = time.localtime(t)
  return (pack('>cH',PROP_DATE,yy),
          pack('>cHB',PROP_DATE,yy,mm),
          pack('>cHBB',PROP_DATE,yy,mm,dd))

# retrieval date features
DATE_PAT = re.compile(r'(\d+)(/\d+)?(/\d+)?')
upperbound = min
lowerbound = max
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
      r.extend( pack('>cHBB', PROP_DATE, ya, ma, d) for d in xrange(da,db+1) )
    elif ma and mb:
      r.extend( pack('>cHB', PROP_DATE, ya, m) for m in xrange(ma,mb+1) )
    elif ya and yb:
      r.extend( pack('>cH', PROP_DATE, y) for y in xrange(ya,yb+1) )
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

def idx_sent(idx, docid, sentid):
  return unicode(idx[pack('>cii', PROP_SENT, docid, sentid)], 'utf-8')

def idx_sents(idx, docid, sentid):
  startkey = pack('>cii', PROP_SENT, docid, sentid)
  prefix = pack('>ci', PROP_SENT, docid)
  for (k,s) in idx.iteritems(startkey):
    if not k.startswith(prefix): break
    yield unicode(s, 'utf-8')
  return

def idx_docid2info(idx, docid):
  v = idx[pack('>ci', PROP_DOCID, docid)]
  (mtime,) = unpack('>i', v[:4])
  loc = v[4:]
  return (loc, mtime)

def idx_docids(idx):
  (ndocs, _) = idx_info(idx)
  return xrange(1, ndocs+1)

def idx_loc2docid(idx, loc):
  return unpack('>i', idx[PROP_LOC+loc])[0]

def idx_info(idx):
  return unpack('>ii', idx[PROP_IDXINFO])


# test
def test(argv):
  import unittest
  
  # zen2han
  class TestZen2Han(unittest.TestCase):
    def test_zh1(self):
      self.assertEqual(zen2han(u'abcあいう'), u'abcあいう')
      return
    def test_zh2(self):
      self.assertEqual(zen2han(u'ABCＡＢＣ１２３'), u'ABCABC123')
      return


  # isplit
  class TestISplit(unittest.TestCase):
    def assertTokens(self, x, y):
      print '====', x.encode('euc-jp')
      r = list(dispw(isplit(x)))
      print ' '.join(sorted(y.split(' '))).encode('euc-jp')
      print ' '.join(sorted(r)).encode('euc-jp')
      self.assertEqual(' '.join(sorted(r)), ' '.join(sorted(y.split(' '))))
    def test1a(self):
      self.assertTokens(u'a b cde f',
                        u'|a| |b| |cde| |f|')
      return
    def test1b(self):
      self.assertTokens(u'@a-b:cde (4e)',
                        u'|a| |b| |cde| |4e|')
      return
    def test2a(self):
      self.assertTokens(u'あいうえお',
                        u'|あい- -いう- -うえ- -えお|')
      return
    def test2b(self):
      self.assertTokens(u'アとイエ',
                        u'|ア| |と| |アと| |とイ- |イエ|')
      return
    def test2c(self):
      self.assertTokens(u'アとイ エ',
                        u'|ア| |と| |アと| |イ| |とイ| |とイ- |イエ| |エ|')
      return
    def test3a(self):
      self.assertTokens(u'日本海です',
                        u'|日本- -本海| -海で- |です| |日| |海|')
      return
    def test3b(self):
      self.assertTokens(u'日 本海です',
                        u'|日本- -本海| |本海| -海で- |です| |日| |本| |海|')
      return
    def test3c(self):
      self.assertTokens(u'日本-海溝ですよ',
                        u'|日| |本| |海| |溝| |日本| |日本- -本海- -海溝| |海溝| -溝で- |です- -すよ|')
      return
    def test4a(self):
      self.assertTokens(u'あ亜アjiア',
                        u'|あ| |あ亜| |亜| |亜ア| |ア| |アji| |ji| |jiア| |ア|')
      return
    def test4b(self):
      self.assertTokens(u'あい uえおか',
                        u'|あい| -いu| |u| |uえ- |えお- -おか|')
      return
    def test4c(self):
      self.assertTokens(u'あい uえお か',
                        u'|あい| -いu| |u| |uえ- |えお| |えお- -おか| |か|')
      return
    def test4d(self):
      self.assertTokens(u'プロファイルの木',
                        u'|プロ- -ロフ- -ファ- -ァイ- -イル| -ルの| |の| |の木| |木|')
      return
    def test4e(self):
      self.assertTokens(u'あuお',
                        u'|あu| |uお| |あ| |お| |u|')
      return
    def test5a(self):
      self.assertTokens(u'そう思います',
                        u'|そう| -う思| |思| |思い- |いま- -ます|')
      return
    def test5b(self):
      self.assertTokens(u'私は思う',
                        u'|私| |私は| |は| |は思| |思| |思う| |う|')
      return
    def test5c(self):
      self.assertTokens(u'私は旅立つ',
                        u'|私| |私は| |は| |は旅- |旅立| -立つ| |つ| |旅| |立|')
      return
    def test6a(self):
      self.assertTokens(u'東',
                        u'|東|')
      return
    def test6b(self):
      self.assertTokens(u'東・海・道・線',
                        u'|東| |海| |道| |線| |東海| |東海- |海道| -海道- -海道| |海道- |道線| -道線|')
      return


  # rsplit
  class TestRSplit(unittest.TestCase):
    def assertTokens(self, s, x0, x1, x2):
      def sp(x):
        if not x:
          return ''
        else:
          return ' '.join(sorted(x.split(' ')))
      print '====', s.encode('euc-jp')
      (r0,r1,r2) = [ list(dispw(r)) for r in rsplit(s) ]
      print 'r0:', sp(x0).encode('euc-jp')
      print 'r0:', ' '.join(sorted(r0)).encode('euc-jp')
      print 'r1:', sp(x1).encode('euc-jp')
      print 'r1:', ' '.join(sorted(r1)).encode('euc-jp')
      print 'r2:', sp(x2).encode('euc-jp')
      print 'r2:', ' '.join(sorted(r2)).encode('euc-jp')
      self.assertEqual(' '.join(sorted(r0)), sp(x0))
      self.assertEqual(' '.join(sorted(r1)), sp(x1))
      self.assertEqual(' '.join(sorted(r2)), sp(x2))
    def test1a(self):
      self.assertTokens(u'abc',
                        u'',
                        u'|abc|',
                        u'')
      return
    def test1b(self):
      self.assertTokens(u'a-b',
                        u'',
                        u'|a| |b|',
                        u'')
      return
    def test1c(self):
      self.assertTokens(u'a-b-c',
                        u'',
                        u'|a| |b| |c|',
                        u'')
      return
    def test1d(self):
      self.assertTokens(u'@a-b:cde(4e)',
                        u'',
                        u'|a| |b| |cde| |4e|',
                        u'')
      return
    def test2a(self):
      self.assertTokens(u'あいうえお',
                        u'|あい- -あい-',
                        u'-いう- -うえ-',
                        u'-えお| -えお-')
      return
    def test2b(self):
      self.assertTokens(u'アとイエ',
                        u'|アと| -アと|',
                        u'|とイ-',
                        u'|イエ| |イエ-')
      return
    def test2c(self):
      self.assertTokens(u'日本',
                        u'|日本- -日本- -日本| |日本|',
                        u'',
                        u'')
      return
    def test3a(self):
      self.assertTokens(u'日本海です',
                        u'|日本- -日本-',
                        u'-本海| -海で-',
                        u'|です| |です-')
      return
    def test3b(self):
      self.assertTokens(u'日本海',
                        u'|日本- -日本-',
                        u'',
                        u'-本海| -本海-')
      return
    def test4a(self):
      self.assertTokens(u'あ亜アjiアu',
                        u'|あ亜| -あ亜|',
                        u'|亜ア| |アji| |jiア| |アu|',
                        u'')
      return
    def test4b(self):
      self.assertTokens(u'uえおか',
                        u'',
                        u'|uえ- |えお-',
                        u'-おか| -おか-')
      return
    def test4c(self):
      self.assertTokens(u'あ',
                        u'',
                        u'|あ|',
                        u'')
      return
    def test4d(self):
      self.assertTokens(u'あu',
                        u'-あu| |あu|',
                        u'',
                        u'')
      return
    def test4e(self):
      self.assertTokens(u'uあ',
                        u'|uあ- |uあ|',
                        u'',
                        u'')
      return
    def test5a(self):
      self.assertTokens(u'そう思います',
                        u'|そう| -そう|',
                        u'-う思| |思い- |いま-',
                        u'-ます| -ます-')
      return
    def test5b(self):
      self.assertTokens(u'私は思う',
                        u'|私は| -私は|',
                        u'|は思|',
                        u'|思う| |思う-')
      return
    def test5c(self):
      self.assertTokens(u'私は入門る',
                        u'|私は| -私は|',
                        u'|は入- |入門|',
                        u'-門る| -門る-')
      return
    def test5d(self):
      self.assertTokens(u'私は',
                        u'|私は- -私は- -私は| |私は|',
                        u'',
                        u'')
      return
    def test6a(self):
      self.assertTokens(u'東',
                        u'',
                        u'|東|',
                        u'')
      return
    def test6b(self):
      self.assertTokens(u'東海道線',
                        u'|東海- -東海-',
                        u'-海道-',
                        u'-道線| -道線-')
      return
    def test7a(self):
      self.assertTokens(u'ああ、そう',
                        u'|ああ| -ああ|',
                        u'-あそ-',
                        u'|そう| |そう-')
      return
    def test7b(self):
      self.assertTokens(u'あ、そう',
                        u'|あそ- -あそ-',
                        u'',
                        u'|そう| |そう-')
      return
    def test7c(self):
      self.assertTokens(u'へえ|',
                        u'-へえ| |へえ|',
                        u'',
                        u'')
      return
    def test7d(self):
      self.assertTokens(u'|へえ',
                        u'|へえ- |へえ|',
                        u'',
                        u'')
      return
    def test7e(self):
      self.assertTokens(u'|へええ|',
                        u'',
                        u'|へえ- -ええ|',
                        u'')
      return
    def test7f(self):
      self.assertTokens(u'|へえええ|',
                        u'',
                        u'|へえ- -ええ- -ええ|',
                        u'')
      return


  # intersect
  class TestIntersect(unittest.TestCase):
    def assertSeq(self, x, y):
      self.assertEqual(list(intersect(x)), y)
    def test_01(self):
      self.assertSeq([ [1,2], ], [1,2])
    def test_02(self):
      self.assertSeq([ [3,4], [3,4], ], [3,4])
    def test_03(self):
      self.assertSeq([ [3,5, 1,2], [3,4], ], [])
    def test_04(self):
      self.assertSeq([ [3,4, 1,2], [3,4], ], [3,4])
    def test_05(self):
      self.assertSeq([ [3,4, 1,2], [5,6, 3,4, 1,2], ], [3,4, 1,2])
    def test_06(self):
      self.assertSeq([ [3,4], [3,4, 1,2], ], [3,4])
    def test_07(self):
      self.assertSeq([ [3,4, 1,2], [5,6, 3,4], ], [3,4])
    def test_08(self):
      self.assertSeq([ [5,6, 3,4, 1,2], [5,6, 1,2], ], [5,6, 1,2])
    def test_09(self):
      self.assertSeq([ [5,6, 3,4, 1,2], [5,6, 1,2], [5,6], ], [5,6])
    def test_10(self):
      self.assertSeq([ [7,8, 5,6, 3,4, 1,2], [7,8], [1,2], ], [])
    def test_11(self):
      self.assertSeq([ [7,8, 5,6, 3,4, 1,2], [7,8, 5,6], [7,8, 5,6, 1,2], ], [7,8, 5,6])
    def test_12(self):
      self.assertSeq([[1,1357], [1,1357, 1,691, 1,537, 1,167]], [1,1357])


  # union
  class TestUnion(unittest.TestCase):
    def assertSeq(self, x, y, z):
      self.assertEqual(list(union(x, [y])), z)
    def test_01(self):
      self.assertSeq([1,2], [], [])
    def test_02(self):
      self.assertSeq([3,4], [ [], [7,8, 5,6, 3,4],], [3,4])
    def test_03(self):
      self.assertSeq([3,5, 1,2], [ [3,4],], [])
    def test_04(self):
      self.assertSeq([3,4, 1,2], [ [3,4],], [3,4])
    def test_05(self):
      self.assertSeq([5,6, 3,4, 1,2], [ [3,4, 1,2], [5,6, 3,4, 1,2],], [5,6, 3,4, 1,2])
    def test_06(self):
      self.assertSeq([5,6, 3,4], [ [3,4, 1,2], [5,6],], [5,6, 3,4])
    def test_07(self):
      self.assertSeq([3,4, 1,2], [ [5,6, 3,4, 1,2], [1,2],], [3,4, 1,2])
    def test_08(self):
      self.assertSeq([5,6, 3,4, 1,2], [ [5,6, 1,2],], [5,6, 1,2])
    def test_09(self):
      self.assertSeq([5,6, 3,4, 1,2], [ [5,6, 1,2], [5,6],], [5,6, 1,2])
    def test_10(self):
      self.assertSeq([7,8, 5,6, 3,4, 1,2], [ [7,8], [1,2],], [7,8, 1,2])
    def test_11(self):
      self.assertSeq([7,8, 5,6, 3,4, 1,2], [ [7,8, 5,6], [7,8, 5,6, 1,2],], [7,8, 5,6, 1,2])
    def test_12(self):
      self.assertSeq([2,1], [[], [2,1289, 2,954, 2,502, 2,1],], [2,1])


  # merge
  class TestMerge(unittest.TestCase):
    def assertSeq(self, seqs, ref):
      self.assertEqual(list(merge(seqs)), ref)
    def test_00(self):
      self.assertSeq([], [])
    def test_01(self):
      self.assertSeq([[0,1]], [0,1])
    def test_02(self):
      self.assertSeq([[1,3], [1,3]], [1,3])
    def test_03(self):
      self.assertSeq([[1,1], [2,2]], [2,2,1,1])
    def test_04(self):
      self.assertSeq([[2,2,1,1], [1,1]], [2,2,1,1])
    def test_05(self):
      self.assertSeq([[2,2,1,1], [3,1,1,1]], [3,1,2,2,1,1])
    def test_06(self):
      self.assertSeq([[4,4,2,2,1,1], [5,5,3,3]], [5,5,4,4,3,3,2,2,1,1])

  suite = unittest.TestSuite()
  suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestZen2Han))
  suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestISplit))
  suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestRSplit))
  suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestIntersect))
  suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestUnion))
  suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestMerge))
  return not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()

if __name__ == '__main__': sys.exit(test(sys.argv))
