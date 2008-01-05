#!/usr/bin/env python
# -*- encoding: euc-jp -*-
import sys
stdout = sys.stdout
stderr = sys.stderr


HIRA2KATA = dict( (unichr(c),unichr(c+96)) for c in xrange(0x3041,0x3094) )
def tokata(s): return ''.join( HIRA2KATA.get(c,c) for c in s )


##  expand_pubdic
##
def expand_pubdic(args, encoding='euc-jp', verbose=0):
  import re, fileinput
  
  VALID_WORD = re.compile(ur'^[々〆ヵヶ\u4e00-\u9fff][々〆\u3041-\u309f\u4e00-\u9fff]*$')
  RMSP = re.compile(r'\s+')
  POS_EXPAND = {
    u'カ行五段': u'カキクケコ',
    u'ガ行五段': u'ガギグゲゴ',
    u'サ行五段': u'サシスセソ',
    u'タ行五段': u'タトツテトッ',
    u'ナ行五段': u'ナニヌネノン',
    u'マ行五段': u'マミムメモン',
    u'ラ行五段': u'ラリルレロッ',
    u'ワ行五段': u'ワイウエオッ',
    u'バ行五段': u'バビブベボン',
    }

  dic = {}
  pos_freq = {}
  
  fp = fileinput.input(args)
  for line in fp:
    if fp.isfirstline():
      print '# filename=%r' % fp.filename()
    try:
      line = unicode(line.strip(), encoding)
    except UnicodeError:
      print >>stderr, 'UnicodeError: filename=%r, lineno=%d' % \
            (fp.filename(), fp.filelineno())
      continue
    if not line: continue
    
    f = RMSP.sub(' ', line).split(' ')
    if len(f) == 4:
      (yomi,exp,poss,_) = f
    else:
      print >>stderr, 'FormatError: filename=%r, lineno=%d: %r' % \
            (fp.filename(), fp.filelineno(), line)
      continue

    if not VALID_WORD.match(exp) and poss != '-': continue
    yomi = tokata(yomi)
    exp = tokata(exp)
    for pos1 in poss.split('&'):
      r = POS_EXPAND.get(pos1, [''])
      for c in r:
        w = exp+c
        if w not in dic:
          dic[w] = []
        y = yomi+c
        d = dic[w]
        if y not in d:
          d.append(y)
      if pos1 not in pos_freq:
        pos_freq[pos1] = 0
      pos_freq[pos1] += 1
      
  for w in sorted(dic.iterkeys()):
    print ('%s %s' % (w, ' '.join(dic[w]))).encode(encoding)

  if verbose:
    for pos1 in sorted(pos_freq.iterkeys()):
      print >>stderr, '%s: %d' % (pos1, pos_freq[pos1])
  return


# main
def main(argv):
  import getopt
  def usage():
    print 'usage: %s [file ...]' % argv[0]
    return 100
  try:
    (opts, args) = getopt.getopt(argv[1:], '')
  except getopt.GetoptError:
    return usage()
  return expand_pubdic(args)

if __name__ == '__main__': sys.exit(main(sys.argv))
