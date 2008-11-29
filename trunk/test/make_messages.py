#!/usr/bin/env python
# -*- coding: euc-jp -*-
import sys
from email.Message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.message import MIMEMessage
from email.mime.text import MIMEText
from email.Header import Header, make_header

def main(args):
  msg1 = Message()
  msg1.set_charset('iso-2022-jp')
  msg1['From'] = Header(u'Yusuke Shinyama <yusuke@nonexistent.dom>', 'iso-2022-jp')
  msg1['To'] = Header(u'きょうから明日です <today@tomorrow>', 'iso-2022-jp')
  msg1['Subject'] = Header(u'ムーミン谷のみなさんへ', 'iso-2022-jp')
  msg1['Date'] = 'Thu, 31 Aug 2004 03:06:09 +0900'
  msg1.set_payload(u'その逆だ!'.encode('iso-2022-jp'), 'iso-2022-jp')
  fp = file(args.pop(0), 'wb')
  fp.write(msg1.as_string(0))
  fp.close()

  msg2 = MIMEMultipart()
  msg2.set_charset('utf-8')
  msg2['From'] = Header(u'えうすけ <euske@foo.baa>', 'iso-2022-jp')
  msg2['To'] = Header(u'だれでも <any@one>', 'utf-8')
  msg2['Subject'] = Header(u'何を見てるんだい?', 'iso-2022-jp')
  msg2['Date'] = 'Thu, 29 Feb 2004 19:23:34 +0500'
  text1 = MIMEText(u'ああそうか、\nこれは夢なんだ。'.encode('utf-8'), 'plain', 'utf-8')
  text2 = MIMEText(u'<html><body>\n<strong>HEY!</strong>\n<p>do you wanna feel unconfortably energetic?\n</body></html>', 'html')
  h = Header(u'ふうばあ ばず', 'iso-2022-jp')
  text2.add_header('Content-Disposition', 'attachment', filename=h.encode())
  msg2.set_payload([text1, text2])
  fp = file(args.pop(0), 'wb')
  fp.write(msg2.as_string(0))
  fp.close()

  msg3 = MIMEMultipart()
  msg3['From'] = '=?iso-2022-jp?b?Gy?= \xff\xaa\x88'
  msg3['Subject'] = 'huh?'
  msg3['Date'] = 'Tue, 25 Nov 2008 01:00:09 +0900'
  parts = MIMEMultipart()
  parts.set_payload([MIMEText('part1'), MIMEText('part2')])
  msg4 = Message()
  msg4.set_charset('iso-2022-jp')
  msg4['From'] = Header(u'john doe <johndoe@heaven.gov>', 'iso-2022-jp')
  msg4['To'] = Header(u'どこだって? <where@where>', 'iso-2022-jp')
  msg4['Subject'] = Header(u'その先の日本へ', 'iso-2022-jp')
  msg4['Date'] = 'Sun, 31 Aug 2008 12:20:33 +0900'
  msg4.set_payload(u'ししかばう゛ー'.encode('iso-2022-jp'), 'iso-2022-jp')
  msg3.set_payload([parts, MIMEMessage(msg4)])
  fp = file(args.pop(0), 'wb')
  fp.write(msg3.as_string(0))
  fp.close()

  return

if __name__ == '__main__': main(sys.argv[1:])
