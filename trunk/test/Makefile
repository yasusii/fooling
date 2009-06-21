# Makefile

FOOLING=..
PYTHON=PYTHONPATH=$(FOOLING) python
CMP=cmp

INDEX=$(PYTHON) -m fooling.indexer -e euc-jp -F
SEARCH=$(PYTHON) -m fooling.selection -e euc-jp
MERGE=$(PYTHON) -m fooling.merger
TARDB=$(PYTHON) -m fooling.tardb
DUMPIDX=$(PYTHON) -m tools.dumpidx

# Automated tests:

test: plaintext html email plainyomi tardb

clean: clean_plaintext clean_html clean_email clean_plainyomi clean_tardb
	-rm *.cdb *.cdb.bak *.cdb.tmp

# Plain text

plaintext: clean_plaintext index_plaintext search_plaintext

idx00000.cdb: plaintext1.txt
	$(INDEX) -tPlainTextDocument -pidx ./ plaintext1.txt
idx00000.dump: idx00000.cdb
	$(DUMPIDX) idx00000.cdb > idx00000.dump
idx00000.test: idx00000.dump idx00000.dump.src
	$(CMP) idx00000.dump idx00000.dump.src

plaintext1.result: idx00000.cdb
	$(SEARCH) -tPlainTextDocument -pidx ./ "れれれ" > plaintext1.result
plaintext1.test: plaintext1.result plaintext1.result.src
	$(CMP) plaintext1.result plaintext1.result.src

clean_plaintext:
	-rm idx00000.cdb idx00000.dump plaintext*.result
index_plaintext: idx00000.test
search_plaintext: plaintext1.test

# HTML text

html: clean_html index_html search_html

aaa00000.cdb: html1.html html4.html
	$(INDEX) -tHTMLDocument -paaa ./ html1.html html4.html
aaa00000.dump: aaa00000.cdb
	$(DUMPIDX) aaa00000.cdb > aaa00000.dump
aaa00000.test: aaa00000.dump aaa00000.dump.src
	$(CMP) aaa00000.dump aaa00000.dump.src
aaa00001.cdb: html2.html html4.html
	$(INDEX) -tHTMLDocument -paaa ./ html2.html html4.html
aaa00001.dump: aaa00001.cdb
	$(DUMPIDX) aaa00001.cdb > aaa00001.dump
aaa00001.test: aaa00001.dump aaa00001.dump.src
	$(CMP) aaa00001.dump aaa00001.dump.src
aaa00000.merged: aaa00000.test aaa00001.test
	$(MERGE) -paaa ./
aaa00000.merged.dump: aaa00000.merged
	$(DUMPIDX) aaa00000.cdb > aaa00000.merged.dump
aaa00000.merged.test: aaa00000.merged.dump aaa00000.merged.dump.src
	$(CMP) aaa00000.merged.dump aaa00000.merged.dump.src

bbb00000.cdb: html3.html
	$(INDEX) -tHTMLDocument -pbbb ./ html3.html
bbb00000.dump: bbb00000.cdb
	$(DUMPIDX) bbb00000.cdb > bbb00000.dump
bbb00000.test: bbb00000.dump bbb00000.dump.src
	$(CMP) bbb00000.dump bbb00000.dump.src

html1.result: aaa00000.merged bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "test" > html1.result
html1.test: html1.result html1.result.src
	$(CMP) html1.result html1.result.src
html2.result: aaa00000.merged bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "ほんと" > html2.result
html2.test: html2.result html2.result.src
	$(CMP) html2.result html2.result.src
html3.result: aaa00000.merged bbb00000.cdb
	$(SEARCH) -tHTMLDocument -paaa ./ "ほんと" > html3.result
html3.test: html3.result html3.result.src
	$(CMP) html3.result html3.result.src
html4.result: aaa00000.merged bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "pre1" "pre2" > html4.result
html4.test: html4.result html4.result.src
	$(CMP) html4.result html4.result.src
html5.result: aaa00000.merged bbb00000.cdb
	$(SEARCH) -tHTMLDocument -D ./ "pre1" "pre4" > html5.result
html5.test: html5.result html5.result.src
	$(CMP) html5.result html5.result.src
html6.result: aaa00000.merged bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "pre1 pre2" > html6.result
html6.test: html6.result html6.result.src
	$(CMP) html6.result html6.result.src
html7.result: aaa00000.merged bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "pre1 pre2 pre3" > html7.result
html7.test: html7.result html7.result.src
	$(CMP) html7.result html7.result.src
html8.result: aaa00000.merged bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "title:ふう" > html8.result
html8.test: html8.result html8.result.src
	$(CMP) html8.result html8.result.src
html9.result: aaa00000.merged bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "title:ドー" > html9.result
html9.test: html9.result html9.result.src
	$(CMP) html9.result html9.result.src

clean_html:
	-rm aaa00000.cdb aaa00001.cdb bbb00000.cdb
	-rm aaa00000.dump aaa00001.dump bbb00000.dump aaa00000.merged.dump
	-rm html*.result
index_html: aaa00000.merged.test bbb00000.test
search_html: html1.result html2.result html3.result html4.result \
	html5.result html6.result html7.result html8.result html9.result

# E-Mail

email: clean_email index_email search_email

email1.msg email2.msg email3.msg: make_messages.py
	$(PYTHON) make_messages.py email1.msg email2.msg email3.msg
ccc00000.cdb: email1.msg email2.msg email3.msg
	$(INDEX) -tEMailDocument -pccc ./ email1.msg email2.msg email3.msg
ccc00000.dump: ccc00000.cdb
	$(DUMPIDX) ccc00000.cdb > ccc00000.dump
ccc00000.test: ccc00000.dump ccc00000.dump.src
	$(CMP) ccc00000.dump ccc00000.dump.src

email1.result: ccc00000.cdb
	$(SEARCH) -tEMailDocument -pccc ./ "date:2004" > email1.result
email1.test: email1.result email1.result.src
	$(CMP) email1.result email1.result.src
email2.result: ccc00000.cdb
	$(SEARCH) -tEMailDocument -pccc ./ "date:2004/08" > email2.result
email2.test: email2.result email2.result.src
	$(CMP) email2.result email2.result.src
email3.result: ccc00000.cdb
	$(SEARCH) -tEMailDocument -pccc ./ "逆" > email3.result
email3.test: email3.result email3.result.src
	$(CMP) email3.result email3.result.src
email4.result: ccc00000.cdb
	$(SEARCH) -tEMailDocument -pccc ./ "to:any@one" > email4.result
email4.test: email4.result email4.result.src
	$(CMP) email4.result email4.result.src
email5.result: ccc00000.cdb
	$(SEARCH) -tEMailDocument -pccc ./ "みなさん" > email5.result
email5.test: email5.result email5.result.src
	$(CMP) email5.result email5.result.src
header.result:
	$(SEARCH) -tEMailDocument -D -pccc ./ "to:きょう" "from:えう" > header.result
header.test: header.result header.result.src
	$(CMP) header.result header.result.src
html.result:
	$(SEARCH) -tEMailDocument -pccc ./ "do you wanna feel" > html.result
html.test: html.result html.result.src
	$(CMP) html.result html.result.src
attach.result:
	$(SEARCH) -tEMailDocument -pccc ./ "ふうばあ ばず" > attach.result
attach.test: attach.result attach.result.src
	$(CMP) attach.result attach.result.src

clean_email:
	-rm ccc00000.cdb ccc00000.dump
	-rm email1.msg email2.msg email3.msg
	-rm email*.result
	-rm header.result html.result attach.result
index_email: ccc00000.test	
search_email: email1.test email2.test email3.test email4.test email5.test \
	header.test html.test attach.test

# Plain text (yomi)

plainyomi: clean_plainyomi index_plainyomi search_plainyomi

idy00000.cdb: plainyomi1.txt
	$(INDEX) -tPlainTextDocument -pidy -Y ./ plainyomi1.txt
idy00000.dump: idy00000.cdb
	$(DUMPIDX) idy00000.cdb > idy00000.dump
idy00000.test: idy00000.dump idy00000.dump.src
	$(CMP) idy00000.dump idy00000.dump.src

plainyomi1.result: idy00000.cdb
	$(SEARCH) -tPlainTextDocument -pidy -Y ./ 'iitenki' > plainyomi1.result
plainyomi1.test: plainyomi1.result plainyomi1.result.src
	$(CMP) plainyomi1.result plainyomi1.result.src
plainyomi2.result: idy00000.cdb
	$(SEARCH) -tPlainTextDocument -pidy -Y ./ 'きじゃよ' > plainyomi2.result
plainyomi2.test: plainyomi2.result plainyomi2.result.src
	$(CMP) plainyomi2.result plainyomi2.result.src
plainyomi3.result: idy00000.cdb
	$(SEARCH) -tPlainTextDocument -pidy -Y ./ 'toukyoutokkyokyokakyoku' > plainyomi3.result
plainyomi3.test: plainyomi3.result plainyomi3.result.src
	$(CMP) plainyomi3.result plainyomi3.result.src
plainyomi4.result: idy00000.cdb
	$(SEARCH) -tPlainTextDocument -pidy -Y ./ 'to-kyo-tokkyokyokakyoku' > plainyomi4.result
plainyomi4.test: plainyomi4.result plainyomi4.result.src
	$(CMP) plainyomi4.result plainyomi4.result.src

clean_plainyomi:
	-rm idy00000.cdb idy00000.dump
	-rm plainyomi*.result
index_plainyomi: idy00000.test
search_plainyomi: plainyomi1.test plainyomi2.test plainyomi3.test plainyomi4.test

# TarDB

tardb: clean_tardb index_tardb search_tardb

testdb: plaintext1.txt
	$(TARDB) create testdb
	$(TARDB) add testdb foo plaintext1.txt

idz00000.cdb: testdb
	$(INDEX) -cTarDBCorpus -tPlainTextDocument -pidz -btestdb ./ 0
idz00000.dump: idz00000.cdb
	$(DUMPIDX) idz00000.cdb > idz00000.dump
idz00000.test: idz00000.dump idz00000.dump.src
	$(CMP) idz00000.dump idz00000.dump.src

tardb1.result: idz00000.cdb
	$(SEARCH) -tPlainTextDocument -pidz ./ "れれれ" > tardb1.result
tardb1.test: tardb1.result tardb1.result.src
	$(CMP) tardb1.result tardb1.result.src

clean_tardb:
	-rm idz00000.cdb idz00000.dump tardb*.result
	-rm -rf testdb
index_tardb: idz00000.test
search_tardb: tardb1.test
