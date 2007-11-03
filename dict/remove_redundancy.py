#!/usr/bin/env python
# -*- encoding: euc-jp -*-
import sys, fileinput, re
from os.path import join, dirname
stdout = sys.stdout
stderr = sys.stderr

VALID_YOMI = re.compile(ur'^[\u3041-\u3093]+$')
def encode_yomi(s):
  return ''.join( chr(ord(c)-0x2fa0) for c in s )
def decode_yomi(s):
  return u''.join( unichr(0x3000+ord(c)) for c in s )


YOMI_DICT = {}
def read_dict(args, encoding):
  for line in fileinput.input(args):
    line = line.strip()
    if not line or line.startswith('#'): continue
    line = unicode(line, encoding)
    f = line.split(' ')
    d = YOMI_DICT
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
  return


##  index_yomi:
##  returns bigrams of yomi-characters.
##
CHARTYPE = {
  0x3005: 2,  # kanji: "noma"
  0x3006: 2,  # kanji: "shime"
  0x30f5: 2,  # kanji: "ka"
  0x30f6: 2,  # kanji: "ke"
  0x30fc: 1,  # kana: "-"
  }
for i in xrange(0x3041, 0x3093+1):
  CHARTYPE[i] = 1  # kana
for i in xrange(0x30a1, 0x30f4+1):
  CHARTYPE[i] = 1  # kana
for i in xrange(0x4e00, 0x9fff+1):
  CHARTYPE[i] = 2  # kanji
for c in u'\r\n\t ,.-=()"\'　・、−＝「」『』“”（）':
  CHARTYPE[ord(c)] = 3  # transparent
del i,c

##  grep_yomi
##
def grep_yomi(yomi, sent):
  match = [ [(i,0)] for i in xrange(len(sent)+1) ]
  e = len(sent)
  e0 = e-1
  i = 0

  while i < e:
    c = ord(sent[i])
    t = CHARTYPE.get(c)
    if t == 1:                          ### KANA
      if c < 0x30a0:
        cur = chr(c - 0x2fa0)           # hirakana
      else:
        cur = chr(c - 0x3000)           # katakana
      r = match[i+1]
      for (i0,b) in match[i]:
        if b < len(yomi) and cur == yomi[b]:
          r.append((i0, b+1))
    elif t == 2:                        ### KANJI
      try:
        p = YOMI_DICT
        j = i
        bs = match[i]
        while j < e:
          (v,p) = p[sent[j]]
          if i == 0 and j == e0: break
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
      match[i+1] = match[i]

    i += 1
  for (e,r) in enumerate(match):
    for (b,n) in r:
      if n == len(yomi):
        yield (b,e)
  return


# test
def main(argv, encoding='euc-jp'):
  args = argv[1:]
  read_dict(args, encoding)
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
      for _ in grep_yomi(y, s):
        break
      else:
        real_yomi.append(yomi)
    if real_yomi:
      print ('%s %s' % (s, ' '.join(real_yomi))).encode(encoding)
    else:
      print '#', s.encode(encoding)
      removed += 1
  return (removed == 0)

if __name__ == '__main__': sys.exit(main(sys.argv))
