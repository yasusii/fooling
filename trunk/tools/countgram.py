#!/usr/bin/env python
import sys
from struct import pack, unpack


##  countgram
##
def countgram(dic, cdbname):
  fp = file(cdbname, "rb")
  (eor,) = unpack("<L", fp.read(4))
  fp.seek(2048)
  pos = 2048
  while pos < eor:
    (klen, vlen) = unpack("<LL", fp.read(8))
    k = fp.read(klen)
    v = fp.read(vlen)
    pos += 4+4+klen+vlen
    if not k: continue
    if k[0] not in '\x01\x02\x03\x04\x05': continue
    if k not in dic: dic[k] = 0
    (n,) = unpack('>l', v[:4])
    dic[k] += n
  fp.close()
  print >>sys.stderr, cdbname
  return


if __name__ == "__main__":
  dic = {}
  for fname in sys.argv[1:]:
    countgram(dic, fname)
  for (k,v) in dic.iteritems():
    print repr(k), v
