#!/bin/sh

# Automated indexing script
# ex.
#   33 * * * *      cd /cgi/host/fooling.tabesugi.net && nice ./index_new.sh >> index.log

# Index the files under $DOCDIR that match $FILEPAT 
# and have been changed within $DAYS days.
. ./index.rc || exit 1
( cd "$DOCDIR" && find . -name "$DOCPAT" -type f -mtime -"$DAYS" ) | 
  "$FOOLINGDIR"/sortbymtime.py -b "$DOCDIR" |
  "$FOOLINGDIR"/indexer.py -R $INDEXOPTS -b "$DOCDIR" -p bbb "$DBDIR"
