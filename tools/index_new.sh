#!/bin/sh

# Automated indexing script
# ex.
#   33 * * * *      cd /cgi/host/fooling.tabesugi.net && nice ./index_new.sh >> index.log

. ./index.rc || exit 1
( cd "$DOCDIR" && find . -name "$DOCPAT" -type f -mtime -"$DAYS" ) | 
  sortbymtime.py -b "$DOCDIR" | idxmake.py -R $INDEXOPTS -b "$DOCDIR" -p bbb "$DBDIR"
