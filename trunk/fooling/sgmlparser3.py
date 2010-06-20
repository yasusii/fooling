#!/usr/bin/env python
#
# sgmlparser3.py
#
#  Copyright (c) 2005-2007  Yusuke Shinyama <yusuke at cs dot nyu dot edu>
#  
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, including without limitation the rights to use,
#  copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following
#  conditions:
#  
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#  
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
#  KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#  WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
#  PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import sys, re
from htmlentitydefs import name2codepoint

__all__ = [ 'SGMLParser3' ]

START_NAME = re.compile(r'[^\s]')
START_VALUE = re.compile(r'[^\s]')
END_PCDATA = re.compile(r'[<&]')
END_ENTITYREF = re.compile(r'[^a-zA-Z0-9#]')
END_TAGNAME = re.compile(r'[\s<>/\?!=\"\']')
END_VALUE_OTHERS = re.compile(r'[\s<>&]')
END_VALUE_DQ = re.compile(r'[\"&]')
END_VALUE_SQ = re.compile(r'[\'&]')


##  SGMLParser3
##
class SGMLParser3(object):
  """
  Robust feed based SGML parser.
  Mainly for instantiating HTMLParser3.
  """

  def __init__(self):
    """
    Create and initialize a parser object.
    """
    # state1: current state:
    #   parse_pcdata, parse_cdata, parse_cdata_end, 
    #   parse_entityref_0, parse_entityref_1,
    #   parse_tag_0, parse_tag_1, parse_tag_attr_0, parse_tag_attr_1,
    #   parse_tag_attrvalue_0, parse_tag_attrvalue_1,
    #   parse_decl_0, parse_decl_1,
    #   parse_comment_0, parse_comment_1, parse_comment_2,
    self.state1 = self.parse_pcdata
    # state0: previous state
    self.state0 = None
    # charpos:
    self.charpos = 0
    return

  def feed(self, x):
    """
    Feed a string to the parser.
    """
    i = 0
    while 0 <= i and i < len(x):
      i = self.state1(x, i)
    return self
  feed_unicode = feed

  def close(self):
    """
    Finish parsing and discard all uncomplete tags and entities.
    """
    return

  def start_cdata(self, endname):
    """
    Begin CDATA mode.
    
    This needs be called manually by a handler routine.
    """
    self.cdata_endstr = '</'+endname
    self.state1 = self.parse_cdata
    return

  # You should inherit the following methods.

  def handle_start_tag(self, name, attrs):
    raise NotImplementedError
  
  def handle_end_tag(self, name, attrs):
    raise NotImplementedError
  
  def handle_decl(self, name):
    raise NotImplementedError
  
  def handle_directive(self, name, attrs):
    raise NotImplementedError
  
  def handle_characters(self, data):
    raise NotImplementedError

  
  # Internal methods.

  def lookup_entity(self, name):
    """
    Convert an HTML entity name to one or more unicode character(s).
    """
    name = name.lower()
    if name in name2codepoint:
      # entityref
      return unichr(name2codepoint[name])
    else:
      # charref
      if name.startswith('#x'):
        try:
          return unichr( int(name[2:], 16) )
        except ValueError:
          # not a hex number, or not valid unichr number.
          pass
      elif name.startswith('#'):
        try:
          return unichr( int(name[1:]) )
        except ValueError:
          # not a int number, or not valid unichr number.
          pass
      return None

  def parse_pcdata(self, x, i0):
    """
    Consume them until it meets either a tag or entityref.
    """
    m = END_PCDATA.search(x, i0)
    self.charpos = i0
    if not m:
      assert i0 < len(x)
      self.handle_characters(x[i0:])
      return -1
    # special character found
    i1 = m.start(0)
    if i0 < i1:
      self.handle_characters(x[i0:i1])
    c = x[i1]
    if c == '&':                      # meet: '&'
      self.feed_entity = self.handle_characters
      self.state0 = self.parse_pcdata
      self.state1 = self.parse_entityref_0
    else:                             # meet: '<'
      self.state1 = self.parse_tag_0
    self.charpos = i1
    return i1

  def parse_cdata(self, x, i0):
    """
    Consume them until it meets the end tag.
    """
    i1 = x.find('<', i0)
    if i1 == -1:
      assert i0 < len(x)
      self.handle_characters(x[i0:])
      return -1
    if i0 < i1:
      self.handle_characters(x[i0:i1])
    self.cdata_endcheck = '<'
    self.state1 = self.parse_cdata_end
    return i1+1
    
  def parse_cdata_end(self, x, i0):
    """
    Check if it's the end tag.
    """
    need = len(self.cdata_endstr) - len(self.cdata_endcheck)
    assert 0 < need
    left = len(x) - i0
    if left < need:
      self.cdata_endcheck += x[i0:]
      return -1
    i1 = i0+need
    self.cdata_endcheck += x[i0:i1]
    # now sufficient chars are available, check it.
    if self.cdata_endcheck.lower() == self.cdata_endstr:
      assert self.cdata_endstr.startswith('</')
      # ending tag
      self.cdata_endstr = ''
      self.attr_name = self.cdata_endstr[2:]
      self.tag_attrs = []
      self.handle_tag = self.handle_end_tag
      self.state1 = self.parse_tag_attr_0
    else:
      # cdata still continues...
      # partial scan (for handling nasty "</scr</script>" case)
      i = self.cdata_endcheck.find('<', 1)
      if i == -1:
        self.handle_characters(self.cdata_endcheck)
        self.state1 = self.parse_cdata
      else:
        self.handle_characters(self.cdata_endcheck[:i])
        self.cdata_endcheck = self.cdata_endcheck[i:]
    return i1

  def parse_entityref_0(self, x, i0):
    assert x[i0] == '&'
    self.state1 = self.parse_entityref_1
    self.entity_name = ''
    return i0+1
  
  def parse_entityref_1(self, x, i0):
    m = END_ENTITYREF.search(x, i0)
    if not m:
      self.entity_name += x[i0:]
      return -1        
    # end of entity name
    i1 = m.start(0)
    self.entity_name += x[i0:i1]
    # "return" to the previous state.
    self.state1 = self.state0
    s = self.lookup_entity(self.entity_name)
    if s:
      self.feed_entity(s)
      c = x[i1]
      if c == ';':
        i1 += 1
    else:
      self.feed_entity('&'+self.entity_name)
    return i1
    
  # Parse start/end tags.
  
  def parse_tag_0(self, x, i0):
    assert x[i0] == '<'
    self.state1 = self.parse_tag_1
    self.tag_name = ''
    self.tag_attrs = []
    return i0+1

  def parse_tag_1(self, x, i0):
    c = x[i0]
    if c == '!':
      self.decl_string = ''
      self.state1 = self.parse_decl_0
      i0 += 1
    elif c == '?':
      self.attr_name = ''
      self.handle_tag = self.handle_directive
      self.state1 = self.parse_tag_attr_0
      i0 += 1
    elif c == '/':
      self.attr_name = ''
      self.handle_tag = self.handle_end_tag
      self.state1 = self.parse_tag_attr_0
      i0 += 1
    else:
      self.attr_name = ''
      self.handle_tag = self.handle_start_tag
      self.state1 = self.parse_tag_attr_0
    return i0

  # Parse tag attributes.
  
  def parse_tag_attr_0(self, x, i0):
    # looking for a tagname/attrvalue...
    m = START_NAME.search(x, i0)
    if not m:
      # ignore intermediate characters.
      return -1
    i1 = m.start(0)
    c = x[i1]
    if c == '=':
      # attr value starting...
      self.state1 = self.parse_tag_attrvalue_0
      return i1+1
    # tagname/attrname/endoftag found...
    if self.attr_name:
      # fix attr if any.
      self.tag_attrs.append((self.attr_name, self.attr_name))
    self.attr_name = ''
    if c == '<':
      # meet: '<...<'
      self.state1 = self.parse_tag_0
      self.handle_tag(self.tag_name, self.tag_attrs) # this may change self.state1 (CDATA).
    elif c == '>':
      # meet: '<...>'
      self.state1 = self.parse_pcdata
      self.handle_tag(self.tag_name, self.tag_attrs) # this may change self.state1 (CDATA).
      # eat this character.
      i1 += 1
    else:
      if c in '/?!\"\'':
        i1 += 1
      # attrname starting...
      self.state1 = self.parse_tag_attr_1
    return i1
  
  def parse_tag_attr_1(self, x, i0):
    # eating characters for a name...
    m = END_TAGNAME.search(x, i0)
    if not m:
      self.attr_name += x[i0:]
      return -1
    # tagname/attrname now complete, what's next?
    i1 = m.start(0)
    self.attr_name += x[i0:i1]
    self.attr_name = self.attr_name.lower()
    if not self.tag_name:
      self.tag_name = self.attr_name
      self.attr_name = ''
    self.state1 = self.parse_tag_attr_0
    return i1

  def parse_tag_attrvalue_0(self, x, i0):
    # looking for an attrvalue...
    m = START_VALUE.search(x, i0)
    if not m:
      return -1
    i1 = m.start(0)
    c = x[i1]
    self.attr_value = ''
    if c == '<' or c == '>':
      # value end
      self.state1 = self.parse_tag_attr_0
    elif c == '"':
      self.end_attrvalue = END_VALUE_DQ
      self.state1 = self.parse_tag_attrvalue_1
      i1 += 1
    elif c == "'":
      self.end_attrvalue = END_VALUE_SQ
      self.state1 = self.parse_tag_attrvalue_1
      i1 += 1
    else:
      self.end_attrvalue = END_VALUE_OTHERS
      self.state1 = self.parse_tag_attrvalue_1
    return i1

  def parse_tag_attrvalue_1(self, x, i0):
    # eating characters for a value...
    m = self.end_attrvalue.search(x, i0)
    if not m:
      assert i0 < len(x)
      self.attr_value += x[i0:]
      return -1
    i1 = m.start(0)
    self.attr_value += x[i0:i1]
    c = x[i1]
    if c == '&':
      # "call" the entityref parser.
      def feed_entity(s):
        self.attr_value += s
        return
      self.feed_entity = feed_entity
      self.state0 = self.parse_tag_attrvalue_1
      self.state1 = self.parse_entityref_0
      return i1
    # end of value.
    if self.attr_name:
      self.tag_attrs.append((self.attr_name, self.attr_value))
      self.attr_name = ''
    self.state1 = self.parse_tag_attr_0
    if c == "'" or c == '"':
      i1 += 1
    return i1

  # Parse SGML declarations or comments.
  def parse_decl_0(self, x, i0):
    if x[i0] == '-':
      self.state1 = self.parse_comment_0
      return i0+1
    self.state1 = self.parse_decl_1
    return i0
  
  def parse_decl_1(self, x, i0):
    i1 = x.find('>', i0)
    if i1 == -1:
      self.decl_string += x[i0:]
    else:
      self.decl_string += x[i0:i1]
      self.handle_decl(self.decl_string)
      self.state1 = self.parse_pcdata
      i1 += 1
    return i1

  # beginning '-'
  def parse_comment_0(self, x, i0):
    if x[i0] == '-':
      return i0+1
    elif x[i0] == '>':
      self.state1 = self.parse_comment_2
    else:
      self.handle_start_tag('comment', [])
      self.state1 = self.parse_comment_1
    return i0
  
  def parse_comment_1(self, x, i0):
    i1 = x.find('-', i0)
    if i1 == -1:
      assert i0 < len(x)
      self.handle_characters(x[i0:])
    else:
      if i0 < i1:
        self.handle_characters(x[i0:i1])
      self.state1 = self.parse_comment_2
      self.comment_dashes = 1
      i1 += 1
    return i1
  
  # trailing '-'
  def parse_comment_2(self, x, i0):
    c = x[i0]
    if c == '>':
      self.handle_end_tag('comment', [])
      self.state1 = self.parse_pcdata
      return i0+1
    elif c == '-':
      self.comment_dashes += 1
      return i0+1
    self.handle_characters(u'-' * self.comment_dashes)
    self.state1 = self.parse_comment_1
    return i0


##  Test suite
##
def test(argv):
  import unittest

  class TestSGMLParser3(unittest.TestCase):

    class TestParser(SGMLParser3):
      def __init__(self):
        self.r = []
        SGMLParser3.__init__(self)
        return
      def handle_start_tag(self, name, attrs):
        self.r.append((name, attrs))
        if name == 'script': self.start_cdata('script')
        return
      def handle_end_tag(self, name, attrs):
        self.r.append(('/'+name, attrs))
        return
      def handle_decl(self, name):
        self.r.append(('!'+name, []))
        return
      def handle_directive(self, name, attrs):
        self.r.append(('?'+name, attrs))
        return
      def handle_characters(self, data):
        if self.r and isinstance(self.r[-1], basestring):
          self.r[-1] += data
        else:
          self.r.append(data)
        return

    def assertParseOK(self, sgml, results):
      # feed them at once.
      parser = self.TestParser()
      parser.feed(sgml)
      self.assertEqual(parser.r, results)
      # feed them char-by-char.
      parser = self.TestParser()
      for c in sgml:
        parser.feed(c)
      self.assertEqual(parser.r, results)
      return

    def test_00_basic(self):
      self.assertParseOK('<foo>baa</foo>zzz',
                         [('foo',[]), 'baa', ('/foo',[]), 'zzz'])
      return

    def test_00_xmlish(self):
      self.assertParseOK('<foo><br/></foo>',
                         [('foo',[]), ('br',[]), ('/foo',[])])
      return

    def test_01_entity(self):
      self.assertParseOK('<foo>baa&amp;&gt goo</foo>',
                         [('foo',[]), 'baa&> goo', ('/foo',[])])
      return

    def test_01_entity_not(self):
      self.assertParseOK('<foo>baa&xzcv;goo</foo>',
                         [('foo',[]), 'baa&xzcv;goo', ('/foo',[])])
      return

    def test_02_attrs(self):
      self.assertParseOK('<foo attr=value ATTR2=value2>baa</foo x=y>',
                         [('foo',[('attr','value'), ('attr2','value2')]),
                          'baa', ('/foo',[('x','y')])])
      return

    def test_02_attrs_entity(self):
      self.assertParseOK('<foo attr=value&amp;>baa</foo>',
                         [('foo',[('attr','value&')]), 'baa', ('/foo',[])])
      return

    def test_02_attrs_dq(self):
      self.assertParseOK('<foo attr="value">baa</foo>',
                         [('foo',[('attr','value')]), 'baa', ('/foo',[])])
      return

    def test_02_attrs_sq(self):
      self.assertParseOK("<foo attr='value'>baa</foo>",
                         [('foo',[('attr','value')]), 'baa', ('/foo',[])])
      return

    def test_03_cdata(self):
      self.assertParseOK('<script lang=javascript>te&st<script></scr</script>',
                         [('script',[('lang','javascript')]),
                          'te&st<script></scr',
                          ('/script',[])])
      return

    def test_04_decl(self):
      self.assertParseOK('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">zzz',
                         [('!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"',[]), 'zzz'])
      return

    def test_05_directive(self):
      self.assertParseOK('<?xml lang="ja">zzz',
                         [('?xml',[('lang','ja')]), 'zzz'])
      return

    def test_06_comment(self):
      self.assertParseOK('gaa<!-- goo!> ---->gee',
                         ['gaa',
                          ('comment',[]), ' goo!> ', ('/comment',[]),
                          'gee'])
      return

    def test_07_nasty_tag1(self):
      self.assertParseOK('<foo <baa>baz',
                         [('foo',[]), ('baa',[]), 'baz'])

      return

    def test_07_nasty_attr1(self):
      self.assertParseOK('<foo x=y"z>baz',
                         [('foo',[('x','y"z')]), 'baz'])

      return

  
  suite = unittest.TestSuite()
  suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestSGMLParser3))
  return not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()

if __name__ == '__main__': sys.exit(test(sys.argv))
