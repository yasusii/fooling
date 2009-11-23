# Makefile

PACKAGE=fooling
PREFIX=/usr/local

PYTHON=python -E
TAR=tar
SVN=svn
RM=rm -f
CP=cp -f

VERSION=`$(PYTHON) fooling/__init__.py`
BUILD_DICT=$(PYTHON) ./tools/build_tcdb_dict.py
DISTFILE=$(PACKAGE)-$(VERSION).tar.gz

all: dict

clean:
	-$(PYTHON) setup.py clean
	-$(RM) -r build dist
	-cd $(PACKAGE) && $(MAKE) clean
	-cd tools && $(MAKE) clean
	-cd test && $(MAKE) clean
	-cd dict && $(MAKE) clean

install: dict
	$(PYTHON) setup.py install --prefix=$(PREFIX)

# Dictionary

dict: fooling/yomidict.tcdb

fooling/yomidict.tcdb: dict/pubdic.txt
	$(BUILD_DICT) -o $@ $<
dict/pubdic.txt:
	cd dict; make pubdic.txt


# Maintainance:

check: unittest searchtest

unittest:
	python fooling/unittests.py

searchtest: dict
	cd test; make test

cmstest: cmsclean
	$(PYTHON) fooling/tarcms.py
cmsclean:
	-rm -rf ./test.__*

commit: clean
	$(SVN) commit

dist: clean
	$(PYTHON) setup.py sdist

WEBDIR=$$HOME/Site/unixuser.org/python/$(PACKAGE)
publish: pack
	$(CP) dist/$(DISTFILE) $(WEBDIR)
	$(CP) docs/*.html $(WEBDIR)/index.html
