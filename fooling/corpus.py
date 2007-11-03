#!/usr/bin/env python
import sys, os, os.path, stat, re
import pycdb as cdb
from struct import pack, unpack
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO
stderr = sys.stderr


__all__ = [ 'Corpus', 'FilesystemCorpus', 'BerkeleyDBCorpus',
            'CDBCorpus', 'SQLiteCorpus' ]

DEFAULT_ENCODING = 'euc-jp'


##  Corpus (abstract)
##
##  A Corpus is an object that contains documents and their indices.
##  A child class must at least override the loc_fp() method to
##  obtain access for actual Documents.
##
class Corpus:

  # Index filename pattern: "xxxNNNNN.cdb"
  IDX_PAT = re.compile(r'^...\d{5}\.cdb$')
  
  def __init__(self, idxdir, prefix='', doctype=None, encoding=DEFAULT_ENCODING):
    self.idxdir = idxdir
    self.prefix = prefix
    # doctype and encoding can depend on a location,
    # but if not, the default type and encoding are used.
    self.default_doctype = doctype
    self.default_encoding = encoding
    # mtime: index modification time.
    self.mtime = 0
    # cdb object cache. Should not be pickled.
    self._idxcache = {}
    # All index filenames are grobbed and sorted initially.
    self.refresh()
    return

  def __repr__(self):
    return '<Corpus: idxdir=%r, prefix=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.idxdir, self.prefix, self.default_doctype, self.default_encoding)

  # When you want to share only one Corpus object,
  # unpickling two Selection objects might end up with
  # two distinct Corpus objects. To prevent this, when
  # a Corpus object is unpickled, this method is called
  # on a "stub" Corpus object and it returns the "real"
  # singleton Corpus object.
  def _unpickle(self):
    return self

  def __getstate__(self):
    # Avoid pickling cdb objects.
    odict = self.__dict__.copy()
    del odict['_idxcache']
    return odict

  def __setstate__(self, dict):
    self.__dict__.update(dict)
    self._idxcache = {}
    return

  def open(self, mode='r'):
    return
  
  def close(self):
    return

  # (Internal) Returns a new index file name.
  def gen_idx_fname(self, idxid):
    assert len(self.prefix) == 3
    fname = os.path.join(self.idxdir, '%s%05d.cdb' % (self.prefix, idxid))
    return fname

  # (Internal) Returns an iterator for the index files.
  def iteridxs(self, start=0, end=sys.maxint-1):
    for idxid in xrange(start, min(end+1, len(self.idxs))):
      fname = self.idxs[idxid]
      if fname in self._idxcache:
        idx = self._idxcache[fname]
      else:
        idx = cdb.init(os.path.join(self.idxdir, fname))
        self._idxcache[fname] = idx
      yield (idxid, idx)
    return

  # (Internal) Grab all the index filenames.
  def refresh(self):
    # Reversed lexical order: the latest comes first.
    self.idxs = sorted(( fname for fname in os.listdir(self.idxdir)
                         if fname.startswith(self.prefix) and self.IDX_PAT.match(fname) ),
                         reverse=True)
    if self.idxs:
      self.mtime = os.stat(os.path.join(self.idxdir, self.idxs[0]))[stat.ST_MTIME]
    self._idxcache.clear()
    return

  # Resets the internal list and ignore all the existing index files.
  def reset(self):
    self.idxs = []
    self._idxcache.clear()
    return

  # Returns the modification time of the indices.
  def index_mtime(self):
    return self.mtime

  # Returns the last location indexed.
  def index_lastloc(self):
    lastloc = None
    for (_,idx) in self.iteridxs():
      (ndocs,_) = unpack('>ii', idx[''])
      lastloc = idx['\x00'+pack('>i',ndocs-1)]
      break
    return lastloc

  # Returns the total number of documents indexed.
  def total_docs(self):
    total = 0
    for (_,idx) in self.iteridxs():
      (ndocs,_) = unpack('>ii', idx[''])
      total += ndocs
    return total

  # (overridable)
  # Returns a Document object for the location.
  def get_doc(self, loc):
    return self.default_doctype(self, loc)

  # Returns (i,docid) if the location is already indexed.
  def loc_indexed(self, loc):
    k = '\xff'+loc
    for (idxid,idx) in self.iteridxs():
      try:
        return (idxid, unpack('>i', idx[k])[0])
      except KeyError:
        pass
    return None

  # (overridable)
  # Returns a default Document title.
  def loc_default_title(self, loc):
    return u'(title unknown)'

  # (overridable)
  # Returns if the given document exists.
  def loc_exists(self, loc):
    raise NotImplementedError

  # (overridable)
  # Returns a codec name of the document.
  def loc_encoding(self, loc):
    return self.default_encoding

  # (overridable)
  # Returns a file-like object for the location.
  def loc_fp(self, loc):
    raise NotImplementedError

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

  def __init__(self, basedir, idxdir, prefix='', doctype=None, encoding=DEFAULT_ENCODING):
    Corpus.__init__(self, idxdir, prefix, doctype, encoding)
    self.basedir = basedir
    return

  def __repr__(self):
    return '<FilesystemCorpus: basedir=%r, idxdir=%r, prefix=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.basedir, self.idxdir, self.prefix, self.default_doctype, self.default_encoding)

  def loc_default_title(self, loc):
    return os.path.basename(loc)
  
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


##  BerkeleyDBCorpus
##
##  A Corpus that uses a single bsddb file.
##  The key for a Document is used as a location.
##
class BerkeleyDBCorpus(Corpus):
  
  def __init__(self, dbfile, idxdir, prefix='', doctype=None, encoding=DEFAULT_ENCODING):
    Corpus.__init__(self, idxdir, prefix, doctype, encoding)
    self.dbfile = dbfile
    return

  def __repr__(self):
    return '<BerkeleyDBCorpus: dbfile=%r, idxdir=%r, prefix=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.dbfile, self.idxdir, self.prefix, self.default_doctype, self.default_encoding)

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
  
  def __init__(self, dbfile, idxdir, prefix='', doctype=None, encoding=DEFAULT_ENCODING):
    Corpus.__init__(self, idxdir, prefix, doctype, encoding)
    self.dbfile = dbfile
    return

  def __repr__(self):
    return '<CDBCorpus: dbfile=%r, idxdir=%r, prefix=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.dbfile, self.idxdir, self.prefix, self.default_doctype, self.default_encoding)

  def __getstate__(self):
    odict = Corpus.__getstate__(self)
    del odict['_db']
    return odict

  def __setstate__(self, dict):
    Corpus.__setstate__(self, dict)
    return

  def open(self, mode='r'):
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
  
  def __init__(self, dbfile, idxdir, prefix='', doctype=None, encoding=DEFAULT_ENCODING,
               table='documents', key='docid', text='doctext', mtime='mtime'):
    Corpus.__init__(self, idxdir, prefix, doctype, encoding)
    self.dbfile = dbfile
    # The field must be a string.
    self.sql_getdoc = 'select %s from %s where %s=?' % (text, table, key)
    # The field must be an integer.
    self.sql_getmtime = 'select %s from %s where %s=?' % (mtime, table, key)
    return

  def __repr__(self):
    return '<SQLiteCorpus: dbfile=%r, idxdir=%r, prefix=%r, default_doctype=%r, default_encoding=%r>' % \
           (self.dbfile, self.idxdir, self.prefix, self.default_doctype, self.default_encoding)

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

