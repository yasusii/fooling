#!/usr/bin/env python
##
##  corpus.py
##

import sys, os, os.path, stat
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO
from fooling.document import PlainTextDocument, EMailDocument, HTMLDocument, DummyDocument

__all__ = [
  'Corpus', 'FilesystemCorpus', 'BerkeleyDBCorpus',
  'CDBCorpus', 'SQLiteCorpus', 'TarDBCorpus', 'GzipTarDBCorpus'
  ]


DOCTYPE_MAP = {
  '.txt': PlainTextDocument,
  '.msg': EMailDocument,
  '.html': HTMLDocument,
  '.htm': HTMLDocument,
  '.jpeg': DummyDocument,
  '.jpg': DummyDocument,
  '.gif': DummyDocument,
  '.png': DummyDocument,
  '.pdf': DummyDocument,
  }


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
  
  def get_subloc(self, loc, i):
    return '%s:%s' % (loc, i)

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
  def loc_feats(self, loc):
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

  # Returns a Document object for the location.
  def get_doc(self, loc):
    (_, ext) = os.path.splitext(loc)
    if ext in DOCTYPE_MAP:
      return DOCTYPE_MAP[ext](self, loc)
    else:
      return self.default_doctype(self, loc)
  
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
    return

  def __repr__(self):
    return '<BerkeleyDBCorpus: dbfile=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.dbfile, self.default_doctype, self.default_encoding)

  def __getstate__(self):
    odict = Corpus.__getstate__(self)
    del odict['_db']
    return odict

  def __setstate__(self, dict):
    Corpus.__setstate__(self, dict)
    return

  def open(self, mode='r'):
    from bsddb import hashopen
    self._db = hashopen(self.dbfile, mode)
    return
    
  def close(self):
    self._db.close()
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
    return

  def __repr__(self):
    return '<CDBCorpus: dbfile=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.dbfile, self.default_doctype, self.default_encoding)

  def __getstate__(self):
    odict = Corpus.__getstate__(self)
    del odict['_db']
    return odict

  def __setstate__(self, dict):
    Corpus.__setstate__(self, dict)
    return

  def open(self, mode='r'):
    import pycdb as cdb
    self._db = cdb.init(self.dbfile)
    return
    
  def close(self):
    self._db.close()
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
    return

  def __repr__(self):
    return '<SQLiteCorpus: dbfile=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.dbfile, self.default_doctype, self.default_encoding)

  def __getstate__(self):
    odict = Corpus.__getstate__(self)
    del odict['_conn']
    del odict['_cur']
    return odict

  def __setstate__(self, dict):
    Corpus.__setstate__(self, dict)
    return

  def open(self, mode='r'):
    import pysqlite2.dbapi2 as pysqlite
    self._conn = pysqlite.connect(self.dbfile)
    self._cur = self._conn.cursor()
    return

  def close(self):
    self._conn.close()
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

  SMALL_MERGE = 20
  LARGE_MERGE = 2000
  SUFFIX = ''
  
  def __init__(self, basedir, doctype, encoding, indexstyle=None, namelen=0):
    Corpus.__init__(self, doctype, encoding, indexstyle)
    self.basedir = basedir
    self.namelen = namelen
    self._db = None
    return
  
  def __repr__(self):
    return '<TarDBCorpus: basedir=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.basedir, self.default_doctype, self.default_encoding)

  def __getstate__(self):
    odict = Corpus.__getstate__(self)
    del odict['_db']
    return odict

  def __setstate__(self, dict):
    Corpus.__setstate__(self, dict)
    return

  def open(self, mode='r'):
    assert self._db == None
    import tardb
    self._db = tardb.TarDB(self.basedir)
    self._db.open(mode=mode)
    return

  def close(self):
    assert self._db != None
    self._db.close()
    return

  def flush(self):
    self._db.flush()
    return

  def create(self):
    import tardb
    tardb.TarDB(self.basedir).create()
    return

  def get_recno(self, loc):
    return int(loc, 16)
  
  def get_loc_info(self, loc):
    recno = self.get_recno(loc)
    return self._db.get_info(recno)

  def set_loc_info(self, loc, info):
    recno = self.get_recno(loc)
    return self._db.set_info(recno, info)

  def get_loc_name(self, loc):
    return self.get_loc_info(loc).name
  
  def set_loc_name(self, loc, name):
    info = self.get_loc_info(loc)
    info.name = name
    self.set_loc_info(loc, info)
    return

  def loc_exists(self, loc):
    recno = self.get_recno(loc)
    return 0 <= recno and recno < len(self._db)

  def loc_fp(self, loc):
    recno = self.get_recno(loc)
    (_,data) = self._db.get_record(recno)
    return StringIO(data)

  def loc_mtime(self, loc):
    info = self.get_loc_info(loc)
    return info.mtime
  
  def loc_size(self, loc):
    info = self.get_loc_info(loc)
    return info.size

  def get_ext(self, loc):
    return self.get_loc_name(loc)[self.namelen:self.namelen+3]

  def get_name(self, loc):
    return self.get_loc_name(loc)[:self.namelen]

  def get_doc(self, loc):
    ext = self.get_ext(loc)
    try:
      return DOCTYPE_MAP[ext](self, loc)
    except KeyError:
      return self.default_doctype(self, loc)
  
  def add_data(self, data, name, ext, mtime=0, labels=None):
    from tarfile import TarInfo
    assert len(name) == self.namelen
    assert len(ext) == 3
    loc = '%08x' % self._db.nextrecno()
    info = TarInfo(name+ext+loc+self.label2str(labels)+self.SUFFIX)
    info.mtime = mtime
    self._db.add_record(info, data)
    return loc

  def get_data(self, loc):
    fp = self.loc_fp(loc)
    return fp.read()

  def get_labels(self, loc):
    return self.str2label(self.get_loc_name(loc)[self.namelen+11:])

  def set_labels(self, loc, labels):
    name = self.get_loc_name(loc)
    self.set_loc_name(loc, name[:self.namelen+11] + self.label2str(labels))
    return

  def loc_feats(self, loc):
    from fooling.util import PROP_LABEL
    return [ PROP_LABEL+x for x in sorted(self.get_labels(loc)) ]

  @classmethod
  def str2label(klass, x):
    if x:
      return set(x.split('.'))
    else:
      return set()

  @classmethod
  def label2str(klass, labels):
    if labels:
      return '.'.join(sorted(labels))
    else:
      return ''


##  GzipTarDBCorpus
##
class GzipTarDBCorpus(TarDBCorpus):

  SUFFIX = '.gz'
  
  def loc_fp(self, loc):
    from gzip import GzipFile
    return GzipFile(fileobj=TarDBCorpus.loc_fp(self, loc))

  def add_data(self, data, name, ext, mtime=0, labels=None):
    from gzip import GzipFile
    fp = StringIO()
    gz = GzipFile(mode='w', fileobj=fp)
    gz.write(data)
    gz.close()
    return TarDBCorpus.add_data(self, fp.getvalue(), name, ext, mtime=mtime, labels=labels)

  def get_loc_name(self, loc):
    return self.get_loc_info(loc).name[:-3]

  def set_loc_name(self, loc, name):
    info = self.get_loc_info(loc)
    info.name = name+'.gz'
    self.set_loc_info(loc, info)
    return
