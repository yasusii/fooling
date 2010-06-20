# Makefile

FOOLING=.
PYTHON=PYTHONPATH=$(FOOLING) python
RM=rm -f

all:

clean:
	-$(RM) *.pyc *.pyo *~
	-$(RM) yomidict.tcdb

test:
	$(PYTHON) utils.py
	$(PYTHON) yomi.py
	$(PYTHON) romm.py
	$(PYTHON) sgmlparser3.py
	$(PYTHON) htmlripper.py
	$(PYTHON) tardb.py
	$(PYTHON) tarcms.py
