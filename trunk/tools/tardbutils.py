#!/usr/bin/env python
import sys
from tarfile import TarInfo
from fooling.tardb import TarDB

def main(argv):
  import getopt
  def usage():
    print 'usage: %s basedir {create,ls,get,add,getinfo,setinfo} [args]' % argv[0]
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(argv[1:], 'v')
  except getopt.GetoptError:
    usage()
  if len(args) < 2: return usage()
  verbose = 1
  for (k, v) in opts:
    if k == '-d': verbose += 1
  db = TarDB(args.pop(0))
  cmd = args.pop(0)
  
  if cmd == 'create':                   # create
    db.create()
    
  elif cmd == 'ls':                     # ls
    db.open()
    for (i,info) in enumerate(db):
      print i,info
      
  elif cmd == 'get':                    # get(recno)
    
    recno = int(args.pop(0))
    db.open()
    data = db.get_record(recno)
    sys.stdout.write(data)
    db.close()
    
  elif cmd == 'add':                    # add(recno, filename)
    db.open(mode='w')
    name = args.pop(0)
    data = open(args.pop(0), 'rb').read()
    db.add_record(TarInfo(name), data)
    db.close()
    
  elif cmd == 'getinfo':                # getinfo(recno)
    recno = int(args.pop(0))
    db.open()
    info = db.get_info(recno)
    print info
    db.close()
    
  elif cmd == 'setinfo':
    recno = int(args.pop(0))            # setinfo(recno, name)
    db.open()
    info = db.get_info(recno)
    info.name = args.pop(0)
    db.set_info(recno, info)
    print info, name
    db.close()
    
  elif cmd == 'recover':                # recover
    db.recover_catalog()

  elif cmd == 'validate':               # validate
    db.validate_catalog()
  return

if __name__ == '__main__': sys.exit(main(sys.argv))
