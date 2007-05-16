# Makefile

PACKAGE=fooling
PYTHON=python2.4 -E
VERSION=`$(PYTHON) fooling/__init__.py`

INDEX=$(PYTHON) ./fooling/indexer.py
SEARCH=$(PYTHON) ./fooling/selection.py
MERGE=$(PYTHON) ./fooling/merger.py
DUMPIDX=$(PYTHON) ./tools/dumpidx.py

all:

clean: testclean
	-cd fooling; rm *.pyc *.pyo *~
	-cd tools; rm *.pyc *.pyo *~


# Packaging:

pack: clean
	ln -s $(PACKAGE) ../$(PACKAGE)-dist-$(VERSION)
	gtar c -z -C.. -f ../$(PACKAGE)-dist-$(VERSION).tar.gz $(PACKAGE)-dist-$(VERSION) \
		--dereference --numeric-owner --exclude '.*'
	rm ../$(PACKAGE)-dist-$(VERSION)

publish: pack
	mv ../$(PACKAGE)-dist-$(VERSION).tar.gz ~/public_html/python/fooling/
	cp docs/*.html ~/public_html/python/fooling/

push: clean
	rs ./ access:work/m/fooling/


# Pychecker:

pychecker:
	pychecker fooling/*.py
	pychecker tools/*.py
	pychecker examples/*.py


# Automated tests:

test: unittest searchplaintest searchhtmltest searchmailtest

testclean:
	-cd test; rm *.cdb *.dump *.cdb.bak *.result

unittest:
	cd fooling; ./unittests.py

indexplaintest: testclean
	$(INDEX) -F -tPlainTextDocument test/ ./test/plain1.txt
	$(DUMPIDX) test/idx00000.cdb > test/idx00000.dump
	cmp test/idx00000.dump test/idx00000.dump.src

searchplaintest: indexplaintest
	$(SEARCH) -tPlainTextDocument test/ れれれ > test/plain1.result
	cmp test/plain1.result test/plain1.result.src

indexhtmltest: testclean
	$(INDEX) -F -tHTMLDocument -paaa test/ ./test/foo.html
	$(DUMPIDX) test/aaa00000.cdb | fgrep -v 'term(32):' > test/aaa00000.dump
	cmp test/aaa00000.dump test/aaa00000.dump.src
	$(INDEX) -F -tHTMLDocument -paaa test/ ./test/bar.html
	$(DUMPIDX) test/aaa00001.cdb | fgrep -v 'term(32):' > test/aaa00001.dump
	cmp test/aaa00001.dump test/aaa00001.dump.src
	$(MERGE) -paaa test/
	$(DUMPIDX) test/aaa00000.cdb | fgrep -v 'term(32):' > test/aaa00000.merged.dump
	cmp test/aaa00000.merged.dump test/aaa00000.merged.dump.src
	$(INDEX) -F -tHTMLDocument -pbbb test/ ./test/baz.html
	$(DUMPIDX) test/bbb00000.cdb | fgrep -v 'term(32):' > test/bbb00000.dump
	cmp test/bbb00000.dump test/bbb00000.dump.src

searchhtmltest: indexhtmltest
	$(SEARCH) -tHTMLDocument test/ test > test/test.result
	cmp test/test.result test/test.result.src
	$(SEARCH) -tHTMLDocument test/ ほんと > test/honto.result
	cmp test/honto.result test/honto.result.src
	$(SEARCH) -tHTMLDocument -paaa test/ ほんと > test/limit.result
	cmp test/limit.result test/limit.result.src
	$(SEARCH) -tHTMLDocument test/ pre1 pre2 > test/and.result
	cmp test/and.result test/and.result.src
	$(SEARCH) -tHTMLDocument -D test/ pre1 pre4 > test/disjunctive.result
	cmp test/disjunctive.result test/disjunctive.result.src
	$(SEARCH) -tHTMLDocument test/ "pre1 pre2" > test/cons.result
	cmp test/cons.result test/cons.result.src
	$(SEARCH) -tHTMLDocument test/ "pre1 pre2 pre3" > test/notfound.result
	cmp test/notfound.result test/notfound.result.src
	$(SEARCH) -tHTMLDocument test/ title:ふう > test/title1.result
	cmp test/title1.result test/title1.result.src
	$(SEARCH) -tHTMLDocument test/ title:ドー > test/title2.result
	cmp test/title2.result test/title2.result.src

indexmailtest: testclean
	$(INDEX) -F -tEMailDocument -pccc test/ ./test/mail1.txt ./test/mail2.txt ./test/mail3.txt
	$(DUMPIDX) test/ccc00000.cdb > test/ccc00000.dump
	cmp test/ccc00000.dump test/ccc00000.dump.src

searchmailtest: indexmailtest
	$(SEARCH) -tEMailDocument -pccc test/ date:2006 > test/date2006.result
	cmp test/date2006.result test/date2006.result.src
	$(SEARCH) -tEMailDocument -pccc test/ date:2006/08 > test/date200608.result
	cmp test/date200608.result test/date200608.result.src
	$(SEARCH) -tEMailDocument -pccc test/ 焼肉 > test/content.result
	cmp test/content.result test/content.result.src
	$(SEARCH) -tEMailDocument -pccc test/ any@one > test/header.result
	cmp test/header.result test/header.result.src
	$(SEARCH) -tEMailDocument -pccc test/ to:デス > test/subject.result
	cmp test/subject.result test/subject.result.src
	$(SEARCH) -tEMailDocument -D -pccc test/ to:デス from:デス > test/disjunctive2.result
	cmp test/disjunctive2.result test/disjunctive2.result.src
	$(SEARCH) -tEMailDocument -pccc test/ "this is a test" > test/html.result
	cmp test/html.result test/html.result.src
	$(SEARCH) -tEMailDocument -pccc test/ "a.html" > test/attach.result
	cmp test/attach.result test/attach.result.src
	$(SEARCH) -tEMailDocument -pccc test/ 我田引水 > test/iso2022.result
	cmp test/iso2022.result test/iso2022.result.src
