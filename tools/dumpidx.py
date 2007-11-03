#!/usr/bin/env python
import sys, os
from struct import pack, unpack
from zlib import decompress
from array import array

COMPRESS_THRESHOLD = 4
SWAP_ENDIAN = (pack('=i',1) == pack('>i',1)) # True if this is big endian.
ENCODING = 'euc-jp'

##  dumpidx
##
def dumpidx(cdbname):
  fp = file(cdbname, "rb")
  (eor,) = unpack("<L", fp.read(4))
  fp.seek(2048)
  pos = 2048
  while pos < eor:
    (klen, vlen) = unpack("<LL", fp.read(8))
    k = fp.read(klen)
    v = fp.read(vlen)
    pos += 4+4+klen+vlen
    if not k:
      (ndocs,nterms) = unpack('>ll', v)
      print 'ndocs=%d, nterms=%d' % (ndocs,nterms)
    elif k[0] == '\x00':
      (docid,) = unpack('>l', k[1:])
      print 'docid:%d -> loc:%r' % (docid, v)
    elif k[0] == '\xff':
      (docid,) = unpack('>l', v)
      print 'loc:%r -> docid:%d' % (k[1:], docid)
    else:
      (c,k) = (k[0], k[1:])
      if '\x01' <= c and c <= '\x04':
        w = unicode(k, 'utf-8').encode(ENCODING)
      elif c == '\x20':
        if len(k) == 2:
          w = '%04d' % unpack('>h', k)
        elif len(k) == 3:
          w = '%04d/%02d' % unpack('>hb', k)
        elif len(k) == 4:
          w = '%04d/%02d/%02d' % unpack('>hbb', k)
        else:
          w = repr(k)
      else:
        w = repr(k)
      (n,) = unpack('>l', v[:4])
      a = array('l')
      if COMPRESS_THRESHOLD <= n:
        a.fromstring(decompress(v[4:]))
      else:
        a.fromstring(v[4:])
      if SWAP_ENDIAN:
        a.byteswap()
      print 'term(%d):%s -> (%d) %s' % (ord(c), w, len(a)/2,
                                        ', '.join('%d:%d' % (a[i], a[i+1]) for i in xrange(0, len(a), 2)))
  fp.close()
  return


if __name__ == "__main__":
  for fname in sys.argv[1:]:
    dumpidx(fname)
