# Makefile

FOOLING=..
PYTHON=python2.4 -E

INDEX=$(PYTHON) $(FOOLING)/fooling/indexer.py -e euc-jp -F
SEARCH=$(PYTHON) $(FOOLING)/fooling/selection.py -e euc-jp
MERGE=$(PYTHON) $(FOOLING)/fooling/merger.py
DUMPIDX=$(PYTHON) $(FOOLING)/tools/dumpidx.py
ELIMDATE=fgrep -v 'term(32):'

# Automated tests:

test: searchplaintest searchhtmltest searchmailtest searchplainyomitest

clean:
	-rm *.cdb *.dump *.cdb.bak *.result

indexplaintest: clean
	$(INDEX) -tPlainTextDocument ./ plain1.txt
	$(DUMPIDX) idx00000.cdb > idx00000.dump
	cmp idx00000.dump idx00000.dump.src

searchplaintest: indexplaintest
	$(SEARCH) -tPlainTextDocument ./ れれれ > plain1.result
	cmp plain1.result plain1.result.src

indexhtmltest: clean
	$(INDEX) -tHTMLDocument -paaa ./ foo.html
	$(DUMPIDX) aaa00000.cdb | $(ELIMDATE) > aaa00000.dump
	cmp aaa00000.dump aaa00000.dump.src
	$(INDEX) -tHTMLDocument -paaa ./ bar.html
	$(DUMPIDX) aaa00001.cdb | $(ELIMDATE) > aaa00001.dump
	cmp aaa00001.dump aaa00001.dump.src
	$(MERGE) -paaa ./
	$(DUMPIDX) aaa00000.cdb | $(ELIMDATE) > aaa00000.merged.dump
	cmp aaa00000.merged.dump aaa00000.merged.dump.src
	$(INDEX) -tHTMLDocument -pbbb ./ baz.html
	$(DUMPIDX) bbb00000.cdb | $(ELIMDATE) > bbb00000.dump
	cmp bbb00000.dump bbb00000.dump.src

searchhtmltest: indexhtmltest
	$(SEARCH) -tHTMLDocument ./ test > test.result
	cmp test.result test.result.src
	$(SEARCH) -tHTMLDocument ./ ほんと > honto.result
	cmp honto.result honto.result.src
	$(SEARCH) -tHTMLDocument -paaa ./ ほんと > limit.result
	cmp limit.result limit.result.src
	$(SEARCH) -tHTMLDocument ./ pre1 pre2 > and.result
	cmp and.result and.result.src
	$(SEARCH) -tHTMLDocument -D ./ pre1 pre4 > disjunctive.result
	cmp disjunctive.result disjunctive.result.src
	$(SEARCH) -tHTMLDocument ./ "pre1 pre2" > cons.result
	cmp cons.result cons.result.src
	$(SEARCH) -tHTMLDocument ./ "pre1 pre2 pre3" > notfound.result
	cmp notfound.result notfound.result.src
	$(SEARCH) -tHTMLDocument ./ title:ふう > title1.result
	cmp title1.result title1.result.src
	$(SEARCH) -tHTMLDocument ./ title:ドー > title2.result
	cmp title2.result title2.result.src

indexmailtest: clean
	$(INDEX) -tEMailDocument -pccc ./ mail1.txt mail2.txt mail3.txt
	$(DUMPIDX) ccc00000.cdb > ccc00000.dump
	cmp ccc00000.dump ccc00000.dump.src

searchmailtest: indexmailtest
	$(SEARCH) -tEMailDocument -pccc ./ date:2006 > date2006.result
	cmp date2006.result date2006.result.src
	$(SEARCH) -tEMailDocument -pccc ./ date:2006/08 > date200608.result
	cmp date200608.result date200608.result.src
	$(SEARCH) -tEMailDocument -pccc ./ 焼肉 > content.result
	cmp content.result content.result.src
	$(SEARCH) -tEMailDocument -pccc ./ any@one > header.result
	cmp header.result header.result.src
	$(SEARCH) -tEMailDocument -pccc ./ to:デス > subject.result
	cmp subject.result subject.result.src
	$(SEARCH) -tEMailDocument -D -pccc ./ to:デス from:デス > disjunctive2.result
	cmp disjunctive2.result disjunctive2.result.src
	$(SEARCH) -tEMailDocument -pccc ./ "this is a test" > html.result
	cmp html.result html.result.src
	$(SEARCH) -tEMailDocument -pccc ./ "a.html" > attach.result
	cmp attach.result attach.result.src
	$(SEARCH) -tEMailDocument -pccc ./ 我田引水 > iso2022.result
	cmp iso2022.result iso2022.result.src

indexplainyomitest: clean
	$(INDEX) -tPlainTextDocument -pidy -Y ./ plain2.txt
	$(DUMPIDX) idy00000.cdb | $(ELIMDATE) > idy00000.dump
	cmp idy00000.dump idy00000.dump.src

searchplainyomitest: indexplainyomitest
	$(SEARCH) -tPlainTextDocument -pidy -Y ./ 'iitenki' > plain2r.result
	cmp plain2r.result plain2r.result.src
	$(SEARCH) -tPlainTextDocument -pidy -Y ./ 'きじゃよ' > plain2h.result
	cmp plain2h.result plain2h.result.src
