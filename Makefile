# Makefile

PACKAGE=fooling
PYTHON=python2.4 -E
VERSION=`$(PYTHON) fooling/__init__.py`
BUILD_DICT=$(PYTHON) ./tools/build_tcdb_dict.py
TAR=tar

all: dict

clean:
	-cd fooling; rm *.pyc *.pyo *~
	-cd tools; rm *.pyc *.pyo *~
	-rm fooling/yomidict.tcdb
	cd test; make clean

dict: fooling/yomidict.tcdb

fooling/yomidict.tcdb: dict/pubdic.txt
	$(BUILD_DICT) -o $@ $<

# Packaging:

pack: clean
	ln -s $(PACKAGE) ../$(PACKAGE)-dist-$(VERSION)
	$(TAR) c -z -C.. -f ../$(PACKAGE)-dist-$(VERSION).tar.gz $(PACKAGE)-dist-$(VERSION) \
		--dereference --numeric-owner --exclude '.*'
	rm ../$(PACKAGE)-dist-$(VERSION)

publish: pack
	mv ../$(PACKAGE)-dist-$(VERSION).tar.gz ~/public_html/python/fooling/
	cp docs/*.html ~/public_html/python/fooling/


# Pychecker:

pychecker:
	pychecker fooling/*.py
	pychecker tools/*.py
	pychecker examples/*.py


# Automated tests:

test: unittest searchtest

unittest:
	cd fooling; ./unittests.py

searchtest:
	cd test; make test
