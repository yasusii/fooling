#!/bin/sh

# Automated indexing script
# ex.
#   3 4 * * *       cd /cgi/host/fooling.tabesugi.net && nice ./index_old.sh >> index.log

. ./index.rc || exit 1
( cd "$DOCDIR" && find . -name "$DOCPAT" -type f -mtime +"$DAYS" ) |
  sortbymtime.py -b "$DOCDIR" | idxmake.py -U $INDEXOPTS -b "$DOCDIR" -p aaa "$DBDIR"
# Merge with the older indices.
idxmerge.py -p aaa "$DBDIR"
