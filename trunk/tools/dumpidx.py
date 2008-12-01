#!/usr/bin/env python
import sys
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
    if k[0] == '\x00':
      (docid,sentid) = unpack('>xll', k)
      v = unicode(v, 'utf-8')
      print 'sent(%d,%d) -> %s' % (docid,sentid,v.encode(ENCODING, 'ignore'))
    elif k[0] == '\xfd':
      if len(k) == 5:
        (docid,) = unpack('>xl', k)
        (mtime,) = unpack('>i', v[:4])
        loc = v[4:]
        print 'docid:%d -> mtime:%d, loc:%r' % (docid, mtime, loc)
    elif k[0] == '\xfe':
      (docid,) = unpack('>l', v)
      print 'loc:%r -> docid:%d' % (k[1:], docid)
    elif k == '\xff':
      (ndocs,nterms) = unpack('>ll', v)
      print 'ndocs=%d, nterms=%d' % (ndocs,nterms)
    else:
      (c,k) = (k[0], k[1:])
      if '\x10' <= c and c <= '\x13':
        w = unicode(k, 'utf-8').encode(ENCODING, 'ignore')
      elif c == '\x20':
        w = u''.join( unichr(0x3000+ord(c)) for c in k ).encode(ENCODING, 'ignore')
      elif c == '\xf0':
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
      print 'term(0x%02x):%s -> (%d) %s' % (ord(c), w, len(a)/2,
                                            ', '.join('%d:%d' % (a[i], a[i+1]) for i in xrange(0, len(a), 2)))
  fp.close()
  return


if __name__ == "__main__":
  for fname in sys.argv[1:]:
    dumpidx(fname)
