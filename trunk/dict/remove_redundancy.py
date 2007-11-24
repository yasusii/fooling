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


##  read_dict
##  Read the file and construct an in-memory tree.
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

##  equiv_yomi
##  a version of grep yomi.
##
def equiv_yomi(yomi, sent):
  match = [ [(i,0)] for i in xrange(len(sent)+1) ]
  e = len(sent)
  end = e-1
  pos = 0

  while pos < e:
    c = ord(sent[pos])
    t = CHARTYPE.get(c)
    if t == 1:                          ### KANA
      if c < 0x30a0:
        cur = chr(c - 0x2fa0)           # hirakana
      else:
        cur = chr(c - 0x3000)           # katakana
      r = match[pos+1]
      for (i0,b) in match[pos]:
        if b < len(yomi) and cur == yomi[b]:
          r.append((i0, b+1))
    elif t == 2:                        ### KANJI
      try:
        p = YOMI_DICT
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
  for (e,r) in enumerate(match):
    for (b,n) in r:
      if b == 0 and n == len(yomi):
        return True
  return False


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
      if not equiv_yomi(y, s):
        real_yomi.append(yomi)
    if real_yomi:
      print ('%s %s' % (s, ' '.join(real_yomi))).encode(encoding)
    else:
      print '#', s.encode(encoding)
      removed += 1
  return (removed == 0)

if __name__ == '__main__': sys.exit(main(sys.argv))
