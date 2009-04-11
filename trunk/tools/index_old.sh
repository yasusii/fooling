#!/bin/sh

# Automated indexing script
# ex.
#   3 4 * * *       cd /cgi/host/fooling.tabesugi.net && nice ./index_old.sh >> index.log

# Index the files under $DOCDIR that match $FILEPAT 
# and haven't been changed within $DAYS days.
. ./index.rc || exit 1
( cd "$DOCDIR" && find . -name "$DOCPAT" -type f -mtime +"$DAYS" ) |
  "$FOOLINGDIR"/sortbymtime.py -b "$DOCDIR" |
  "$FOOLINGDIR"/indexer.py $INDEXOPTS -b "$DOCDIR" -p aaa "$DBDIR"
# Merge with the older indices.
"$FOOLINGDIR"/merger.py -p aaa "$DBDIR"
