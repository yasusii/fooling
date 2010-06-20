#!/usr/bin/env python
##
##  corpus.py
##

import sys
import os, os.path, stat
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO
from document import PlainTextDocument
from document import EMailDocument
from document import HTMLDocument
from document import DummyDocument

__all__ = [
  'Corpus', 'FilesystemCorpus', 'BerkeleyDBCorpus',
  'CDBCorpus', 'SQLiteCorpus', 'TarDBCorpus', 'GzipTarDBCorpus'
  ]


##  Corpus (abstract)
##
##  A Corpus is an object that contains documents and their indices.
##  A child class must at least override the loc_fp() method to
##  obtain access for actual Documents.
##
class Corpus(object):

  def __init__(self, default_doctype, default_encoding, default_indexstyle=None):
    # doctype and encoding can depend on a location,
    # but if not, the default type and encoding are used.
    self.default_doctype = default_doctype
    self.default_encoding = default_encoding
    self.default_indexstyle = default_indexstyle
    return

  def __repr__(self):
    return ('<Corpus: default_doctype=%r, default_encoding=%r>' % \
            (self.default_doctype, self.default_encoding))

  # (overridable)
  def open(self, mode='r'):
    return
  
  # (overridable)
  def close(self):
    return

  # (overridable)
  # Returns a Document object for the location.
  def get_doc(self, loc):
    return self.default_doctype(self, loc)
  
  # (overridable)
  # Returns a default Document title.
  def loc_title(self, loc):
    return None

  # (overridable)
  # Returns if the given document exists.
  def loc_exists(self, loc):
    raise NotImplementedError

  # (overridable)
  # Returns the codec name of a document.
  def loc_encoding(self, loc):
    return self.default_encoding

  # (overridable)
  # Returns the index style of a document.
  def loc_indexstyle(self, loc):
    return self.default_indexstyle

  # (overridable)
  # Returns a file-like object for the location.
  def loc_fp(self, loc):
    raise NotImplementedError

  # (overridable)
  # Returns the features for the location.
  def loc_labels(self, loc):
    return []

  # (overridable)
  # Returns the lastmod time (in integer) for the location.
  def loc_mtime(self, loc):
    return 0                            # zero means unknown
  
  # (overridable)
  # Returns the size of the document for the location.
  def loc_size(self, loc):
    return 0                            # zero means unknown


##  FilesystemCorpus
##
##  A Corpus that uses a filesystem for storing document.
##  (Probably this is the most commonly used one.)
##
class FilesystemCorpus(Corpus):

  def __init__(self, basedir, doctype, encoding, indexstyle=None):
    Corpus.__init__(self, doctype, encoding, indexstyle)
    self.basedir = basedir
    return

  def __repr__(self):
    return '<FilesystemCorpus: basedir=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.basedir, self.default_doctype, self.default_encoding)

  # Returns if the given document exists.
  def loc_exists(self, loc):
    return os.path.exists(os.path.join(self.basedir, loc))

  # Returns a file-like object for the location.
  def loc_fp(self, loc):
    return file(os.path.join(self.basedir, loc))

  # Returns the lastmod time (in integer) for the location.
  def loc_mtime(self, loc):
    return os.stat(os.path.join(self.basedir, loc))[stat.ST_MTIME]

  # Returns the size for the location.
  def loc_size(self, loc):
    return os.stat(os.path.join(self.basedir, loc))[stat.ST_SIZE]

class FilesystemCorpusWithDefaultTitle(FilesystemCorpus):

  def loc_title(self, loc):
    return os.path.basename(loc)


##  BerkeleyDBCorpus
##
##  A Corpus that uses a single bsddb file.
##  The key for a Document is used as a location.
##
class BerkeleyDBCorpus(Corpus):
  
  def __init__(self, dbfile, doctype, encoding, indexstyle=None):
    Corpus.__init__(self, doctype, encoding, indexstyle)
    self.dbfile = dbfile
    self._db = None
    return

  def __repr__(self):
    return '<BerkeleyDBCorpus: dbfile=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.dbfile, self.default_doctype, self.default_encoding)

  def open(self, mode='r'):
    from bsddb import hashopen
    self._db = hashopen(self.dbfile, mode)
    return
    
  def close(self):
    self._db.close()
    self._db = None
    return

  def loc_exists(self, loc):
    return self._db.has_key(loc)

  def loc_fp(self, loc):
    return StringIO(self._db[loc])

  def loc_size(self, loc):
    return len(self._db[loc])
  

##  CDBCorpus
##
##  A Corpus that uses a single cdb file.
##  The key for a Document is used as a location.
##
class CDBCorpus(Corpus):
  
  def __init__(self, dbfile, doctype, encoding, indexstyle=None):
    Corpus.__init__(self, doctype, encoding, indexstyle)
    self.dbfile = dbfile
    self._db = None
    return

  def __repr__(self):
    return '<CDBCorpus: dbfile=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.dbfile, self.default_doctype, self.default_encoding)

  def open(self, mode='r'):
    import pycdb as cdb
    self._db = cdb.init(self.dbfile)
    return
    
  def close(self):
    self._db.close()
    self._db = None
    return

  def loc_exists(self, loc):
    return self._db.has_key(loc)

  def loc_fp(self, loc):
    return StringIO(self._db[loc])
  
  def loc_size(self, loc):
    return len(self._db[loc])


##  SQLiteCorpus
##
##  A Corpus that uses a SQLite database. It assumes that
##  the content and modification time of a Document is stored
##  in "doctext" and "mtime" field respectively.
##
class SQLiteCorpus(Corpus):
  
  def __init__(self, dbfile, doctype, encoding, indexstyle=None,
               table='documents', key='docid', text='doctext', mtime='mtime'):
    Corpus.__init__(self, doctype, encoding, indexstyle)
    self.dbfile = dbfile
    # The field must be a string.
    self.sql_getdoc = 'select %s from %s where %s=?' % (text, table, key)
    # The field must be an integer.
    self.sql_getmtime = 'select %s from %s where %s=?' % (mtime, table, key)
    self._conn = None
    self._cur = None
    return

  def __repr__(self):
    return '<SQLiteCorpus: dbfile=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.dbfile, self.default_doctype, self.default_encoding)

  def open(self, mode='r'):
    import pysqlite2.dbapi2 as pysqlite
    self._conn = pysqlite.connect(self.dbfile)
    self._cur = self._conn.cursor()
    return

  def close(self):
    self._conn.close()
    self._conn = None
    self._cur = None
    return

  def loc_exists(self, loc):
    self._cur.execute(self.sql_getdoc, (loc,))
    return bool(self._cur.fetchone())

  def loc_fp(self, loc):
    self._cur.execute(self.sql_getdoc, (loc,))
    return StringIO(self._cur.fetchone()[0])

  def loc_mtime(self, loc):
    self._cur.execute(self.sql_getmtime, (loc,))
    return self._cur.fetchone()[0]
  
  def loc_size(self, loc):
    self._cur.execute(self.sql_getdoc, (loc,))
    return len(self._cur.fetchone()[0])


##  TarDBCorpus
##
class TarDBCorpus(Corpus):
  
  def __init__(self, basedir, doctype, encoding, indexstyle=None):
    Corpus.__init__(self, doctype, encoding, indexstyle)
    self.basedir = basedir
    self._db = None
    return
  
  def __repr__(self):
    return '<TarDBCorpus: basedir=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.basedir, self.default_doctype, self.default_encoding)

  def open(self, mode='r'):
    assert self._db == None, self._db
    import tardb
    self._db = tardb.TarDB(self.basedir)
    self._db.open(mode=mode)
    return

  def close(self):
    assert self._db != None, self._db
    self._db.close()
    self._db = None
    return

  def flush(self):
    self._db.flush()
    return

  def create(self):
    import tardb
    tardb.TarDB(self.basedir).create()
    return

  def loc_exists(self, loc):
    recno = self._get_recno(loc)
    return 0 <= recno and recno < len(self._db)

  def loc_fp(self, loc):
    recno = self._get_recno(loc)
    (_,data) = self._db.get_record(recno)
    return StringIO(data)

  def loc_mtime(self, loc):
    info = self._get_info(loc)
    return info.mtime
  
  def loc_size(self, loc):
    info = self._get_info(loc)
    return info.size

  def validate_catalog(self):
    import tardb
    tardb.TarDB(self.basedir).validate_catalog()
    return
  
  def recover_catalog(self):
    import tardb
    tardb.TarDB(self.basedir).recover_catalog()
    return

  def _get_recno(self, loc):
    assert len(loc) == 8, loc
    return int(loc, 16)
  def _get_loc(self, recno):
    return '%08x' % recno
  def _get_info(self, loc):
    recno = self._get_recno(loc)
    return self._db.get_info(recno)

  def get_info(self, loc):
    info = self._get_info(loc)
    info.name = info.name[8:]
    return info

  def set_info(self, loc, info):
    info.name = loc+info.name
    recno = self._get_recno(loc)
    return self._db.set_info(recno, info)

  def add_data(self, info, data):
    loc = self._get_loc(self._db.nextrecno())
    info.name = loc+info.name
    self._db.add_record(info, data)
    return loc

  def get_data(self, loc):
    fp = self.loc_fp(loc)
    return fp.read()

  def get_all_locs(self):
    for recno in xrange(len(self._db)):
      yield self._get_loc(recno)
    return


##  GzipTarDBCorpus
##
class GzipTarDBCorpus(TarDBCorpus):

  SUFFIX = '.gz'

  def loc_fp(self, loc):
    from gzip import GzipFile
    return GzipFile(fileobj=TarDBCorpus.loc_fp(self, loc))

  def get_info(self, loc):
    info = TarDBCorpus.get_info(self, loc)
    assert info.name.endswith(self.SUFFIX), info.name
    info.name = info.name[:-len(self.SUFFIX)]
    return info

  def set_info(self, loc, info):
    info.name += self.SUFFIX
    recno = self._get_recno(loc)
    return self._db.set_info(recno, info)

  def add_data(self, info, data):
    from gzip import GzipFile
    fp = StringIO()
    gz = GzipFile(mode='w', fileobj=fp)
    gz.write(data)
    gz.close()
    info.name += self.SUFFIX
    return TarDBCorpus.add_data(self, info, fp.getvalue())


# get_corpustype
CORPUSTYPES = {
  'fs': FilesystemCorpus,
  'Filesystem': FilesystemCorpus,
  'tar': TarDBCorpus,
  'TarDBCorpus': TarDBCorpus,
  'tgz': GzipTarDBCorpus,
  'GzipTarDBCorpus': GzipTarDBCorpus,
  }
def get_corpustype(corpustype):
  return CORPUSTYPES[corpustype]
