#!/bin/cgipython
# -*- python -*- coding: euc-jp -*-
import sys
import cgitb; cgitb.enable()
import os, re, cgi, random, os.path, time, codecs, stat
from fooling.indexdb import IndexDB
from fooling.document import HTMLDocument, SourceCodeDocument
from fooling.selection import SelectionWithContinuation, SearchTimeout, KeywordPredicate, YomiKeywordPredicate, parse_preds
from urlparse import urljoin

ENCODING = 'euc-jp'
(encoder, decoder) = (codecs.getencoder(ENCODING), codecs.getdecoder(ENCODING))

# decode str
def d(s):
  return decoder(s, 'replace')[0]

# quote HTML metacharacters
def q(x):
  return x.replace('&','&amp;').replace('>','&gt;').replace('<','&lt;').replace('"','&quot;')

# encode str (after html quoting)
def e(u):
  return encoder(u, 'xmlcharrefreplace')[0]

# encode time
def tm(t):
  (yy,mm,dd,h,m,s,wd,_,_) = time.localtime(t)
  return u'%d年%d月%d日' % (yy,mm,dd)

# encode parameters as a URL
Q = re.compile(r'[^a-zA-Z0-9_.-=]')
def url(base, **kw):
  r = []
  for (k,v) in kw.iteritems():
    v = Q.sub(lambda m: '%%%02X' % ord(m.group(0)), encoder(q(v), 'replace')[0])
    r.append('%s=%s' % (k, v))
  return base+'&'.join(r)

def forall(pred, seq):
  for x in seq:
    if not pred(x): return False
  return True


##  SearchApp
##
class SearchApp:

  TITLE = u'Fooling Demo'
  
  CORPUS = {
    't': (u'たべすぎ', 'tabesugi', HTMLDocument, 'http://tabesugi.net/memo/'),
    }

  MAX_QUERY_CHARS = 100
  MAX_QUERY_PREDS = 10
  TIMEOUT = 10

  UNITS = [ u'日', u'週間', u'ヵ月', u'年', u'世紀', u'×10<sup>-44</sup>秒' ]
  
  def __init__(self, outfp=sys.stdout, logfp=sys.stderr):
    self.outfp = outfp
    self.logfp = logfp
    self.path_info = os.environ.get('PATH_INFO', '')
    self.method = os.environ.get('REQUEST_METHOD', 'GET')
    self.server = os.environ.get('SERVER_SOFTWARE', '')
    self.form = cgi.FieldStorage()
    self.content_type = 'text/html; charset=%s' % ENCODING
    self.outbuf = ''
    return

  def log(self, s):
    self.logfp.write(e(s)+'\n')
    self.logfp.flush()
    return

  def out(self, *args):
    for arg1 in args:
      if isinstance(arg1, list):
        arg1 = ''.join( q(unicode(s)) for s in arg1 )
      if isinstance(arg1, unicode):
        self.outbuf += e(arg1)
      else:
        self.outbuf += str(arg1)
    return

  QUERY_PAT = re.compile(r'"[^"]+"|\S+', re.UNICODE)
  def search(self, query, cname, start):
    (name, dirname, doctype, baseurl) = self.CORPUS[cname]
    if not os.path.exists(dirname): return
    indexdb = IndexDB(dirname)
    indexdb.open()
    (disj, preds) = parse_preds(query, max_preds=self.MAX_QUERY_PREDS,
                                yomipredtype=YomiKeywordPredicate)
    selection = SelectionWithContinuation(indexdb, preds, disjunctive=disj)
    if len(start) == 12:
      try:
        selection.load_continuation(start)
        start = len(selection.found_docs)
      except:
        start = 0
    else:
      start = 0

    self.out(u'<hr noshade><p><q>',
             [' '.join( pred.q for pred in preds )],
             u'</q> の検索結果でございますが…',
             u'<dl>\n')
    window = []
    try:
      for (found,loc) in selection.iter(start=start, timeout=self.TIMEOUT):
        (mtime, loc, title, s) = selection.get_snippet(loc,
                                                       normal=q, highlight=lambda x: u'<b>%s</b>' % q(x),
                                                       maxchars=200, maxlr=50)
        self.out(u'<dt><small><i>',
                 [found+1],
                 u'.</i></small> <a href="',
                 [urljoin(baseurl, loc)],
                 u'">',
                 [title],
                 u'</a> &nbsp; <small class=t>\n',
                 [tm(mtime)],
                 u'</small><dd><small>',
                 s,
                 u'</small>\n')
        window.append(found)
        if len(window) == 10: break
      self.out(u'</dl>\n')
    except SearchTimeout:
      self.out(u'</dl><center>(',
               [self.TIMEOUT],
               u'秒で検索を打ち切りました)</center>\n')
    (finished, estimated) = selection.status()
    if not window:
      self.out(u'<div>なかったですよ。<p>')
    else:
      self.out(u'<div align=right>')
      if finished:
        self.out([estimated],
                 u'件')
      else:
        self.out(u'おおよそ',
                 [estimated],
                 u'件ぐらい')
      self.out(u'の検索結果のうち、',
               [window[0]+1],
               u'-',
               [window[-1]+1],
               u'件を表示しております。')
      if not finished:
        cont = selection.save_continuation()
        self.out(u'&nbsp; <a href="',
                 [url('?', q=query, s=cont)],
                 u'">つぎ? &gt;&gt;</a>')
    self.out(u'<br><small>総文書数: ',
             [indexdb.total_docs()],
             u' (',
             [time.strftime('%Y/%m/%d', time.localtime(indexdb.index_mtime()))],
             u' 更新), 検索にかかった時間: ',
             [random.randint(1,10)],
             random.choice(self.UNITS),
             u'</small>')
    self.out(u'</div>\n')
    return

  # header
  def header(self, query):
    # html headings
    if query:
      query = ' - '+query
    self.out(u'<html><head><meta http-equiv="Content-Type" content="text/html; charset=euc-jp">\n',
             u'<meta name="robots" content="noindex,nofollow">\n',
             u'<style type="text/css"><!--\n',
             u'body { line-height: 150%; }\n',
             u'b { color: red; }\n',
             u'small.t { color: gray; }\n',
             u'h2 { text-align: left; letter-spacing: 0.2em; padding-bottom: 4pt; ',
             u' border-bottom: 4pt solid darkblue; width: 50%; }\n',
             u'address { text-align: right; font-size: 75% }\n',
             u'--></style><script><!--\n',
             u'function setFocus() { document.forms[0].q.focus(); }\n',
             u'--></script>\n',
             u'<title>%s' % self.TITLE,
             [query],
             u'</title></head><body onload="setFocus();">\n',
             u'<h2>%s' % self.TITLE,
             [query],
             u'</h2>\n')
    return

  def body(self, query, cname):
    self.out(u'<form action="/" method="GET">',
             u'<strong>検索条件:</strong><br>\n',
             u'<input name="q" size="50" value="',
             [query],
             u'">',
             u'<input type="submit" value="検索"><br>\n',
             u'</form><small><p>\n',
             u'ひらがな、またはローマ字で検索文字列を入力すると、漢字を含む読みがなで検索します。<br>',
             u'例:\n',
             u'<a href="%s">asahi</a>、\n' % url('?', q=u'asahi'),
             u'<a href="%s">ユースケ</a>、\n' % url('?', q=u'ユースケ'),
             u'<a href="%s">おおさまのみみわろばのみみ</a>\n' % url('?', q=u'おおさまのみみわろばのみみ'),
             u'</small>\n',
             )
    return

  def footer(self):
    self.out(u'<hr noshade>\n',
             u'<address>Powered by <a href="http://www.unixuser.org/~euske/python/fooling/index.html#help">Fooling</a></address>\n',
             u'</body></html>\n')
    return

  def run(self):
    query = d(self.form.getvalue('q') or '')[:self.MAX_QUERY_CHARS]
    start = self.form.getvalue('s') or ''
    cname = 't'
    self.header(query)
    self.body(query, cname)
    if query and (cname in self.CORPUS):
      t = time.time()
      self.search(query, cname, start)
      self.log("fooling: q='%s', c=%r, start=%r (%.2f sec)" %
               (query, cname, start, time.time()-t))
    self.footer()
    if self.server.startswith('cgi-httpd'):
      # required for cgi-httpd
      self.outfp.write('HTTP/1.0 200 OK\r\n')
    self.outfp.write('Content-type: %s\r\n' % self.content_type)
    self.outfp.write('Connection: close\r\n\r\n')
    self.outfp.write(self.outbuf)
    return


def main():
  SearchApp().run()
  
if __name__ == "__main__": main()
