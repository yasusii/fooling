# Makefile

PACKAGE=fooling
PYTHON=python -E
VERSION=`$(PYTHON) fooling/__init__.py`
BUILD_DICT=$(PYTHON) ./tools/build_tcdb_dict.py
TAR=tar
SVN=svn

WORKDIR=..
DISTNAME=$(PACKAGE)-dist-$(VERSION)
DISTFILE=$(DISTNAME).tar.gz

all: dict

clean:
	-cd fooling; rm *.pyc *.pyo *~
	-cd tools; rm *.pyc *.pyo *~
	-rm fooling/yomidict.tcdb
	cd test; make clean
	cd dict; make clean


# Dictionary

dict: fooling/yomidict.tcdb

fooling/yomidict.tcdb: dict/pubdic.txt
	$(BUILD_DICT) -o $@ $<
dict/pubdic.txt:
	cd dict; make pubdic.txt


# Automated testing:

test: unittest searchtest

unittest:
	python -m fooling.unittests

searchtest: dict
	cd test; make test


# Maintainance:

pack: clean
	$(SVN) cleanup
	$(SVN) export . $(WORKDIR)/$(DISTNAME)
	$(TAR) c -z -C$(WORKDIR) -f $(WORKDIR)/$(DISTFILE) $(DISTNAME) --dereference --numeric-owner
	rm -rf $(WORKDIR)/$(DISTNAME)

publish: pack
	mv $(WORKDIR)/$(DISTFILE) ~/public_html/python/fooling/
	cp docs/*.html ~/public_html/python/fooling/

pychecker:
	-pychecker --limit=0 fooling/*.py
	-pychecker --limit=0 tools/*.py
	-pychecker --limit=0 examples/*.py

commit: clean
	$(SVN) commit
