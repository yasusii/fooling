# Makefile for pubdic.txt

# from pubdic+
PUBDIC_DIR=pubdic+
# from pubdic+-sup
PUBDIC_SUP_DIR=pubdic+-sup
# from gerodic
GERODIC_DIR=gerodic

# python
PYTHON=python

PUBDIC_FILES= \
 $(PUBDIC_DIR)/bio.u \
 $(PUBDIC_DIR)/chimei.u \
 $(PUBDIC_DIR)/computer.u \
 $(PUBDIC_DIR)/jinmei.u \
 $(PUBDIC_DIR)/kihon.u \
 $(PUBDIC_DIR)/koyuu.u \
 $(PUBDIC_DIR)/setsuji.u \
 $(PUBDIC_DIR)/tankan.u

PUBDIC_SUP_FILES=$(PUBDIC_SUP_DIR)/supplement.u

GERODIC_FILES=$(GERODIC_DIR)/g-jinmei.u

ALL_DICTS=$(PUBDIC_FILES) $(PUBDIC_SUP_FILES) $(GERODIC_FILES) others.u

EXPAND_PUBDIC=$(PYTHON) expand_pubdic.py

REMOVE_REDUNDANCY=$(PYTHON) remove_redundancy.py

all: pubdic.txt

clean:
	-rm pubdic.txt pubdic.txt.0

pubdic.txt.0: $(ALL_DICTS)
	$(EXPAND_PUBDIC) $(ALL_DICTS) > $@

pubdic.txt: pubdic.txt.0
	$(REMOVE_REDUNDANCY) pubdic.txt.0 > $@
