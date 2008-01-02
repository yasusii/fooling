#!/usr/bin/env python
# -*- encoding: euc-jp -*-
import sys, re
sys.path.append('.')
stdout = sys.stdout
stderr = sys.stderr


# encode the yomigana.
def encode_yomi(s):
  def f(n):
    if n == 0x30fc:
      # chou-on kigou
      return chr(0xfc)
    elif 0x3040 <= n and n <= 0x3093:
      # hiragana
      return chr(n-0x2fa0)
    raise ValueError(n)
  try:
    return chr(len(s))+''.join( f(ord(c)) for c in s )
  except ValueError:
    raise ValueError(s)

TRANS_TABLE = dict( (chr(ord(k)-0x3000), chr(ord(v)-0x3000)) for (k,v) in
  [
  (u'ヂ', u'ジ'),  # ヂ → ジ
  (u'ヅ', u'ズ'),  # ヅ → ズ
  #(u'ヲ', u'オ'),  # ヲ → オ
  #(u'ヴ', u'ブ'),  # ヴ → ブ
  ] )
CAN1 = ''.join( chr(ord(c)-0x3000) for c in
                u'ウオクコグゴスソズゾツトヅドヌノフホブボプポムモユヨルロュョ' )
CAN2 = ''.join( chr(ord(c)-0x3000) for c in
                u'ウオ' )
CAN_TRANS = ''.join( TRANS_TABLE.get(chr(c),chr(c)) for c in xrange(256) )
CAN_PAT = re.compile('(['+CAN1+'])['+CAN2+']')
def canonicalize_yomi(y):
  return CAN_PAT.sub('\\1\xfc', y.translate(CAN_TRANS))


##  build_dict
##
def build_dict(output, files):
  import fileinput
  from fooling.pycdb import tcdbmake
  
  def e(s):
    return s.encode('utf-8')

  # find the length of the common prefix of s1 and s2.
  def common_prefix(s1, s2):
    s = zip(s1, s2)
    for (i,(c1,c2)) in enumerate(s):
      if c1 != c2: break
    else:
      i = len(s)
    return i

  maker = tcdbmake(output, output+'.tmp')
  w0 = ''
  stderr.write('Writing %r...' % output)
  stderr.flush()
  for line in fileinput.input(files):
    line = line.strip()
    if not line or line.startswith('#'): continue
    f = unicode(line, 'euc-jp').split(' ')
    w = f[0]
    n = common_prefix(w0, w)
    i = n+1
    #print w, xs
    for c in w[n:-1]:
      maker.put(i, e(c), '')
      i += 1
    v = ''.join( canonicalize_yomi(encode_yomi(y)) for y in f[1:] )
    maker.put(i, e(w[-1]), v)
    w0 = w
  maker.finish()
  stderr.write('finished.\n')
  return


# main
def main(argv):
  import getopt
  def usage():
    print 'usage: %s [-o output] [file ...]' % argv[0]
    return 100
  try:
    (opts, args) = getopt.getopt(argv[1:], 'o:')
  except getopt.GetoptError:
    return usage()
  output = 'yomidict.tcdb'
  for (k, v) in opts:
    if k == '-o': output = v
  return build_dict(output, args)

if __name__ == '__main__': sys.exit(main(sys.argv))
