#!/usr/bin/env python
# -*- encoding: euc-jp -*-
import sys, fileinput, re
from os.path import join, dirname
stdout = sys.stdout
stderr = sys.stderr

VALID_YOMI = re.compile(ur'^[\u30a1-\u30f4\u30fc]+$')
def encode_yomi(s):
  return ''.join( chr(ord(c)-0x3000) for c in s )
def decode_yomi(s):
  return u''.join( unichr(0x3000+ord(c)) for c in s )

HIRA2KATA = dict( (unichr(c),unichr(c+96)) for c in xrange(0x3041,0x3094) )
def tokata(s): return ''.join( HIRA2KATA.get(c,c) for c in s )


def read_lines(args, encoding):
  for line in fileinput.input(args):
    line = line.strip()
    if not line or line.startswith('#'): continue
    yield unicode(line, encoding)
  return

##  read_dict
##  Read the file and construct an in-memory tree.
def read_dict(lines):
  yomi_dict = {}
  for line in lines:
    f = line.split(' ')
    d = yomi_dict
    w = f[0]
    v = [ encode_yomi(y) for y in f[1:] if VALID_YOMI.match(y) ]
    n = len(w)-1
    for (i,c) in enumerate(w):
      if c in d:
        (v0,d1) = d[c]
        if i == n:
          for x in v:
            if x not in v0:
              v0.append(x)
      else:
        d1 = {}
        if i == n:
          d[c] = (v,d1)
        else:
          d[c] = ([],d1)
      d = d1
  return yomi_dict


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

##  equiv_yomi
##  a version of grep yomi.
##
def equiv_yomi(yomi_dict, yomi, sent):
  match = [ [(i,0)] for i in xrange(len(sent)+1) ]
  e = len(sent)
  end = e-1
  pos = 0

  while pos < e:
    c = ord(sent[pos])
    t = CHARTYPE.get(c)
    if t == 0:
      raise ValueError(sent)
    elif t == 1:                        ### KANA
      cur = chr(c - 0x3000)
      r = match[pos+1]
      for (i0,b) in match[pos]:
        if b < len(yomi) and cur == yomi[b]:
          r.append((i0, b+1))
    elif t == 2:                        ### KANJI
      try:
        p = yomi_dict
        j = pos
        bs = match[pos]
        while j < e:
          (v,p) = p[sent[j]]
          # avoid an entry that exactly contains this string!
          if pos == 0 and j == end: break
          j += 1
          if v:  # reaches the end.
            r = match[j]
            for w in v:
              for (i0,b) in bs:
                if yomi[b:b+len(w)] == w:
                  r.append((i0,b+len(w)))
      except KeyError:
        pass
    elif t == 3:                        ### OTHERS
      match[pos+1] = match[pos]

    pos += 1
  
  for (b,n) in match[-1]:
    if b == 0 and n == len(yomi):
      return True
  return False


# test
def main(argv, encoding='euc-jp'):
  args = argv[1:]
  yomi_dict = read_dict(read_lines(args, encoding))
  removed = 0
  for line in fileinput.input(args):
    line = line.strip()
    if not line or line.startswith('#'):
      print line
      continue
    line = unicode(line, encoding)
    f = line.split(' ')
    s = f[0]
    real_yomi = []
    for yomi in f[1:]:
      if not VALID_YOMI.match(yomi): continue
      y = encode_yomi(yomi)
      if not equiv_yomi(yomi_dict, y, s):
        real_yomi.append(yomi)
    if real_yomi:
      print ('%s %s' % (s, ' '.join(real_yomi))).encode(encoding)
    else:
      print '#', s.encode(encoding)
      removed += 1
  return (removed == 0)

def test():
  d = read_dict([
    u'東京 トウキョウ',
    u'東 トウ ヒガシ',
    u'京 キョウ ミヤコ',
    u'和 ワ カズ',
    u'和泉 イズミ ワセン',
    u'泉 イズミ セン',
    u'願 ガン ネガイ',
    u'願イ ネガイ',
    u'オ願 オネガイ',
    u'オ願イ オネガイ',
    ])
  assert equiv_yomi(d, encode_yomi(u'トウキョウ'), u'東京') == True
  assert equiv_yomi(d, encode_yomi(u'キョウト'), u'東京') == False
  assert equiv_yomi(d, encode_yomi(u'ワイズミ'), u'和泉') == True
  assert equiv_yomi(d, encode_yomi(u'イズミ'), u'和泉') == False
  assert equiv_yomi(d, encode_yomi(u'オネガイ'), u'オ願イ') == True
  assert equiv_yomi(d, encode_yomi(u'オネガイ'), u'オ願') == True
  assert equiv_yomi(d, encode_yomi(u'ネガイ'), u'願イ') == False
  return

#test()
if __name__ == '__main__': sys.exit(main(sys.argv))
