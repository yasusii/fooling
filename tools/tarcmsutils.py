#!/usr/bin/env python
import sys
from fooling import document
from fooling.tarcms import TarCMS
from fooling.selection import KeywordPredicate, AlwaysTruePredicate

def main(argv):
  import getopt
  def usage():
    print 'usage: %s basedir {create,ls,la,get,add,modify,find} [args]' % argv[0]
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(argv[1:], 'v')
  except getopt.GetoptError:
    usage()
  if len(args) < 2: return usage()
  verbose = 1
  doctype = document.get_doctype('EMailDocument')
  for (k, v) in opts:
    if k == '-d': verbose += 1
  cms = TarCMS(args.pop(0), doctype)
  cmd = args.pop(0)
  
  if cmd == 'create':                   # create
    cms.create()
    
  elif cmd == 'la':                     # list article
    cms.open()
    for (i,aid) in enumerate(cms.list_articles()):
      print i,aid
      
  elif cmd == 'ls':                     # list article
    cms.open()
    for (i,tid) in enumerate(cms.list_snapshots()):
      print i,tid
      
  elif cmd == 'get':                    # get(tid)
    tid = args.pop(0)
    cms.open()
    data = cms.get_data(tid)
    sys.stdout.write(data)
    
  elif cmd == 'add':                    # add(filename)
    path = args.pop(0)
    cms.open(mode='w')
    data = open(path, 'rb').read()
    aid = cms.create_article(data)
    cms.close()
    print aid
    
  elif cmd == 'modify':                 # modify(aid, filename)
    aid = args.pop(0)
    path = args.pop(0)
    cms.open(mode='w')
    data = open(path, 'rb').read()
    cms.modify_article(aid, data)
    cms.close()

  elif cmd == 'find':                    # find(preds)
    preds = [ KeywordPredicate(k) for k in args ]
    cms.open()
    for (loc,mtime,title,snippet) in cms.find_articles(preds):
      print (loc,mtime,title,snippet)
    
  elif cmd == 'recover':                # recover
    cmsrecover()

  elif cmd == 'validate':               # validate
    cms.validate()
    
  return

if __name__ == '__main__': sys.exit(main(sys.argv))
