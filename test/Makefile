# Makefile

FOOLING=..
PYTHON=python -E
CMP=cmp

INDEX=$(PYTHON) $(FOOLING)/fooling/indexer.py -e euc-jp -F
SEARCH=$(PYTHON) $(FOOLING)/fooling/selection.py -e euc-jp
MERGE=$(PYTHON) $(FOOLING)/fooling/merger.py
DUMPIDX=$(PYTHON) $(FOOLING)/tools/dumpidx.py
ELIMDATE=fgrep -v 'term(f0):'

# Automated tests:

test: plaintext html email plainyomi

clean: clean_plaintext clean_html clean_email clean_plainyomi
	-rm *.cdb *.cdb.bak *.cdb.tmp

# Plain text

plaintext: clean_plaintext index_plaintext search_plaintext

idx00000.cdb: plaintext1.txt
	$(INDEX) -tPlainTextDocument ./ plaintext1.txt
idx00000.dump: idx00000.cdb
	$(DUMPIDX) idx00000.cdb > idx00000.dump
index_plaintext: idx00000.dump idx00000.dump.src
	$(CMP) idx00000.dump idx00000.dump.src

plaintext1.result: idx00000.cdb
	$(SEARCH) -tPlainTextDocument ./ "れれれ" > plaintext1.result
search_plaintext: plaintext1.result plaintext1.result.src
	$(CMP) plaintext1.result plaintext1.result.src

clean_plaintext:
	-rm idx00000.cdb idx00000.dump plaintext*.result

# HTML text

html: clean_html index_html search_html

aaa00000.cdb: html1.html
	$(INDEX) -tHTMLDocument -paaa ./ html1.html
aaa00000.dump: aaa00000.cdb
	$(DUMPIDX) aaa00000.cdb > aaa00000.dump
aaa00001.cdb: html2.html
	$(INDEX) -tHTMLDocument -paaa ./ html2.html
aaa00001.dump: aaa00001.cdb
	$(DUMPIDX) aaa00001.cdb > aaa00001.dump
bbb00000.cdb: html3.html
	$(INDEX) -tHTMLDocument -pbbb ./ html3.html
bbb00000.dump: bbb00000.cdb
	$(DUMPIDX) bbb00000.cdb > bbb00000.dump
merge_html: aaa00000.cdb aaa00001.cdb
	$(MERGE) -paaa ./
	-rm ccc00000.cdb
aaa00000.merged.dump: merge_html
	$(DUMPIDX) aaa00000.cdb > aaa00000.merged.dump
index_html: aaa00000.dump aaa00000.dump.src \
            aaa00001.dump aaa00001.dump.src \
            bbb00000.dump bbb00000.dump.src \
            aaa00000.merged.dump aaa00000.merged.dump.src
	$(CMP) aaa00000.dump aaa00000.dump.src
	$(CMP) aaa00001.dump aaa00001.dump.src
	$(CMP) bbb00000.dump bbb00000.dump.src
	$(CMP) aaa00000.merged.dump aaa00000.merged.dump.src

html1.result: merge_html bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "test" > html1.result
html2.result: merge_html bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "ほんと" > html2.result
html3.result: merge_html bbb00000.cdb
	$(SEARCH) -tHTMLDocument -paaa ./ "ほんと" > html3.result
html4.result: merge_html bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "pre1" "pre2" > html4.result
html5.result: merge_html bbb00000.cdb
	$(SEARCH) -tHTMLDocument -D ./ "pre1" "pre4" > html5.result
html6.result: merge_html bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "pre1 pre2" > html6.result
html7.result: merge_html bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "pre1 pre2 pre3" > html7.result
html8.result: merge_html bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "title:ふう" > html8.result
html9.result: merge_html bbb00000.cdb
	$(SEARCH) -tHTMLDocument ./ "title:ドー" > html9.result
search_html: html1.result html1.result.src \
             html2.result html2.result.src \
             html3.result html3.result.src \
             html4.result html4.result.src \
             html5.result html5.result.src \
             html6.result html6.result.src \
             html7.result html7.result.src \
             html8.result html8.result.src \
             html9.result html9.result.src
	$(CMP) html1.result html1.result.src
	$(CMP) html2.result html2.result.src
	$(CMP) html3.result html3.result.src
	$(CMP) html4.result html4.result.src
	$(CMP) html5.result html5.result.src
	$(CMP) html6.result html6.result.src
	$(CMP) html7.result html7.result.src
	$(CMP) html8.result html8.result.src
	$(CMP) html9.result html9.result.src

clean_html:
	-rm aaa00000.cdb aaa00001.cdb bbb00000.cdb
	-rm aaa00000.dump aaa00001.dump bbb00000.dump aaa00000.merged.dump
	-rm html*.result

# E-Mail

email: clean_email index_email search_email

email1.txt email2.txt email3.txt: make_messages.py
	$(PYTHON) make_messages.py email1.txt email2.txt email3.txt
ccc00000.cdb: email1.txt email2.txt email3.txt
	$(INDEX) -tEMailDocument -pccc ./ email1.txt email2.txt email3.txt
ccc00000.dump: ccc00000.cdb
	$(DUMPIDX) ccc00000.cdb > ccc00000.dump
index_email: ccc00000.dump ccc00000.dump.src
	$(CMP) ccc00000.dump ccc00000.dump.src

email1.result: ccc00000.cdb
	$(SEARCH) -tEMailDocument -pccc ./ "date:2004" > email1.result
email2.result: ccc00000.cdb
	$(SEARCH) -tEMailDocument -pccc ./ "date:2004/08" > email2.result
email3.result: ccc00000.cdb
	$(SEARCH) -tEMailDocument -pccc ./ "逆" > email3.result
email4.result: ccc00000.cdb
	$(SEARCH) -tEMailDocument -pccc ./ "to:any@one" > email4.result
email5.result: ccc00000.cdb
	$(SEARCH) -tEMailDocument -pccc ./ "みなさん" > email5.result
header.result:
	$(SEARCH) -tEMailDocument -D -pccc ./ "to:きょう" "from:えう" > header.result
html.result:
	$(SEARCH) -tEMailDocument -pccc ./ "do you wanna feel" > html.result
attach.result:
	$(SEARCH) -tEMailDocument -pccc ./ "ふうばあ ばず" > attach.result
search_email: email1.result email1.result.src \
              email2.result email2.result.src \
              email3.result email3.result.src \
              email4.result email4.result.src \
              email5.result email5.result.src \
              header.result header.result.src \
              html.result html.result.src \
              attach.result attach.result.src
	$(CMP) email1.result email1.result.src
	$(CMP) email2.result email2.result.src
	$(CMP) email3.result email3.result.src
	$(CMP) email4.result email4.result.src
	$(CMP) email5.result email5.result.src
	$(CMP) header.result header.result.src
	$(CMP) html.result html.result.src
	$(CMP) attach.result attach.result.src

clean_email:
	-rm ccc00000.cdb ccc00000.dump
	-rm email1.txt email2.txt email3.txt
	-rm email*.result
	-rm header.result html.result attach.result

# Plain text (yomi)

plainyomi: clean_plainyomi index_plainyomi search_plainyomi

idy00000.cdb: plainyomi1.txt
	$(INDEX) -tPlainTextDocument -pidy -Y ./ plainyomi1.txt
idy00000.dump: idy00000.cdb
	$(DUMPIDX) idy00000.cdb > idy00000.dump
index_plainyomi: idy00000.dump idy00000.dump.src
	$(CMP) idy00000.dump idy00000.dump.src

plainyomi1.result: idy00000.cdb
	$(SEARCH) -tPlainTextDocument -pidy -Y ./ 'iitenki' > plainyomi1.result
plainyomi2.result: idy00000.cdb
	$(SEARCH) -tPlainTextDocument -pidy -Y ./ 'きじゃよ' > plainyomi2.result
plainyomi3.result: idy00000.cdb
	$(SEARCH) -tPlainTextDocument -pidy -Y ./ 'toukyoutokkyokyokakyoku' > plainyomi3.result
plainyomi4.result: idy00000.cdb
	$(SEARCH) -tPlainTextDocument -pidy -Y ./ 'to-kyo-tokkyokyokakyoku' > plainyomi4.result
search_plainyomi: plainyomi1.result plainyomi1.result.src \
                  plainyomi2.result plainyomi2.result.src \
                  plainyomi3.result plainyomi3.result.src \
                  plainyomi4.result plainyomi4.result.src
	$(CMP) plainyomi1.result plainyomi1.result.src
	$(CMP) plainyomi2.result plainyomi2.result.src
	$(CMP) plainyomi3.result plainyomi3.result.src
	$(CMP) plainyomi4.result plainyomi4.result.src

clean_plainyomi:
	-rm idy00000.cdb idy00000.dump
	-rm plainyomi*.result
