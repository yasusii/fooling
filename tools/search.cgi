#!/usr/bin/env python
# -*- encoding: euc-jp -*-
# -*- python -*-

import cgitb; cgitb.enable()
import sys, os, re, cgi, random, os.path, time, codecs
from fooling.document import HTMLDocument, SourceCodeDocument
from fooling.corpus import FilesystemCorpus
from fooling.selection import parse_preds, SelectionWithContinuation, SearchTimeout
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


##  SearchApp
##
class SearchApp:

  TITLE = u'Fooling Demo'
  
  CORPUS = {
    'p': (u'PyDoc日本語', 'python', HTMLDocument, 'http://www.python.jp/doc/release/'),
    'j': (u'JavaDoc日本語', 'java', HTMLDocument, 'http://java.sun.com/j2se/1.5.0/ja/docs/'),
    'l': (u'Linuxソース', 'linux', SourceCodeDocument, 'file:///usr/src/linux/'),
    't': (u'たべすぎ', 'tabesugi', HTMLDocument, 'http://tabesugi.net/'),
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
    # HTTP header
    if self.server.startswith('cgi-httpd'):
      self.out('HTTP/1.0 200 OK\n')       # required for cgi-httpd
    self.out('Content-type: text/html; charset=euc-jp\n',
             'Connection: close\n',
             '\n')
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
        self.outfp.write(e(arg1))
      else:
        self.outfp.write(str(arg1))
    self.outfp.flush()
    return

  QUERY_PAT = re.compile(r'"[^"]+"|\S+', re.UNICODE)
  def search(self, query, cname, start):
    (name, dirname, doctype, baseurl) = self.CORPUS[cname]
    if not os.path.exists(dirname): return
    corpus = FilesystemCorpus(os.path.join(dirname, 'doc'),
                              os.path.join(dirname, 'idx'), doctype=doctype)
    preds = parse_preds(query, max_preds=self.MAX_QUERY_PREDS)
    selection = SelectionWithContinuation(corpus, preds)
    try:
      if len(start) == 12:
        selection.load_continuation(start)
    except:
      pass

    self.out(u'<hr noshade><p><q>',
             [' '.join( pred.q for pred in preds )],
             u'</q> の検索結果でございますが…',
             u'<dl>\n')
    window = []
    try:
      for (found,doc) in selection.iter_start(timeout=self.TIMEOUT):
        s = doc.get_snippet(selection,
                            normal=q, highlight=lambda x: u'<b>%s</b>' % q(x),
                            maxchars=200, maxcontext=50)
        self.out(u'<dt><small><i>',
                 [found+1],
                 u'.</i></small> <a href="',
                 [urljoin(baseurl, doc.loc)],
                 u'">',
                 [doc.get_title()],
                 u'</a> &nbsp; <small class=t>\n',
                 [tm(doc.get_mtime())],
                 u'</small><dd><small>',
                 s,
                 u'</small>\n')
        window.append(found)
        if len(window) == 10: break
      self.out(u'</dl><div align=right>\n')
    except SearchTimeout:
      self.out(u'</dl><center>(',
               [self.TIMEOUT],
               u'秒で検索を打ち切りました)</center><div align=right>\n')
    (finished, estimated) = selection.status()
    if not window:
      self.out(u'なかったですよ。')
    else:
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
                 [url('?', q=query, c=cname, s=cont)],
                 u'">つぎ? &gt;&gt;</a>')
    self.out(u'<br><small>総文書数: ',
             [corpus.total_docs()],
             u' (',
             [time.strftime('%Y/%m/%d', time.localtime(corpus.mtime))],
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
             #u'<meta name="robots" content="noindex,nofollow">\n',
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
             u'<strong>検索条件:</strong>\n',
             u'<small>(例: <q><code>フレーズ</code></q>, <q><code>title:タイトル検索</code></q>, <q><code>-含まれないもの</code></q>, <q><code>|フレーズ|</code></q>)</small><br>\n',
             u'<input name="q" size="50" value="',
             [query],
             u'">',
             u'<input type="submit" value="検索"><br>\n',
             u'<small>')
    for (k,(name,_,_,_)) in self.CORPUS.iteritems():
      sw = ''
      if k == cname:
        sw = 'checked'
      self.out(u'<label><input type="radio" name="c" value="%s" %s>' % (k,sw),
               [name],
               u'</label>\n')
    self.out(u'</small></form>')
    return

  def footer(self):
    self.out(u'<hr noshade>\n',
             u'<address>Powered by <a href="http://www.unixuser.org/~euske/python/fooling/index.html#help">Fooling</a></address>\n',
             u'</body></html>\n')
    return

  def run(self):
    if self.method == 'HEAD': return
    if self.path_info != '/': return
    query = d(self.form.getvalue('q') or '')[:self.MAX_QUERY_CHARS]
    cname = self.form.getvalue('c') or 'p'
    start = self.form.getvalue('s') or ''
    self.header(query)
    self.body(query, cname)
    if query and (cname in self.CORPUS):
      t = time.time()
      self.search(query, cname, start)
      self.log("fooling: q='%s', c=%r, start=%r (%.2f sec)" % (query, cname, start, time.time()-t))
    self.footer()
    return


def main():
  SearchApp().run()
  
if __name__ == "__main__": main()
