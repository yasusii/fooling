#!/usr/bin/env python
# -*- coding: euc-jp -*-

import sys, unittest
from fooling.util import dispw, zen2han, isplit, rsplit, intersect, union, merge
from fooling.htmlripper import HTMLRipper
stderr = sys.stderr


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


# HTMLRipper
class TestHTMLRipper(unittest.TestCase):
  def assertHTML(self, html, sents):
    self.assertEqual(HTMLRipper().feedunicode(html), sents)
  def test_00(self):
    self.assertHTML(u'<html><body></body></html>', [u''])
    return
  def test_01(self):
    self.assertHTML(u'<html><body>a</body></html>', [u'a'])
    return
  def test_02(self):
    self.assertHTML(u'<html><style>foo</style>a</body></html>', [u'a'])
    return
  def test_03(self):
    self.assertHTML(u'<html>&amp;a</html>', [u'&a'])
    return
  def test_04(self):
    self.assertHTML(u'<body><p>abc<p>def</html>', [u'', u'abc', u'def'])
    return
  def test_05(self):
    self.assertHTML(u'<body>abc\ndef</body>', [u'abc\ndef'])
    return
  def test_06(self):
    self.assertHTML(u'<pre>abc\ndef</pre>', [u'', u'abc\n', u'def', u''])
    return
  def test_07(self):
    self.assertHTML(u'<p>abc\n<img src="foo" alt="baa">', [u'', u'abc\n[baa]'])
    return


#
if __name__ == '__main__': unittest.main()
