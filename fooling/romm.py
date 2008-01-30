#!/usr/bin/env python
# -*- encoding: euc_jp -*-

##  romm.py - handles Roma-ji and kana.
##

##  Constants
##
MORA_DATA = [
  # (symbol, zenkaku_kana, hankaku_kana, zenkaku_hira, output, input)
  
  ( '.a', u'��', u'\uff71', u'��', 'a', 'a', '3a' ),
  ( '.i', u'��', u'\uff72', u'��', 'i', 'i', '3i', '2y' ),
  ( '.u', u'��', u'\uff73', u'��', 'u', 'u', '3u', '3wu', '2w' ),
  ( '.e', u'��', u'\uff74', u'��', 'e', 'e', '3e' ),
  ( '.o', u'��', u'\uff75', u'��', 'o', 'o', '3o' ),
  
  ( 'ka', u'��', u'\uff76', u'��', 'ka', 'ka', '3ka', '3ca' ),
  ( 'ki', u'��', u'\uff77', u'��', 'ki', 'ki', '3ki', '2ky' ),
  ( 'ku', u'��', u'\uff78', u'��', 'ku', 'ku', '3ku', '2k', '2c', '2q' ),
  ( 'ke', u'��', u'\uff79', u'��', 'ke', 'ke', '3ke' ),
  ( 'ko', u'��', u'\uff7a', u'��', 'ko', 'ko', '3ko' ),
  
  ( 'sa', u'��', u'\uff7b', u'��', 'sa', 'sa', '3sa' ),
  ( 'si', u'��', u'\uff7c', u'��', 'si', 'shi', '3si', '3shi', '2sy' ),
  ( 'su', u'��', u'\uff7d', u'��', 'su', 'su', '3su', '2s' ),
  ( 'se', u'��', u'\uff7e', u'��', 'se', 'se', '3se' ),
  ( 'so', u'��', u'\uff7f', u'��', 'so', 'so', '3so' ),
                               
  ( 'ta', u'��', u'\uff80', u'��', 'ta', 'ta', '3ta' ),
  ( 'ti', u'��', u'\uff81', u'��', 'ti', 'chi', '3chi', '3ci', '1ti', '2chy', '2ch' ),
  ( 'tu', u'��', u'\uff82', u'��', 'tu', 'tsu', '3tsu', '1tu' ),
  ( 'te', u'��', u'\uff83', u'��', 'te', 'te', '3te' ),
  ( 'to', u'��', u'\uff84', u'��', 'to', 'to', '3to', '2t' ),
  
  ( 'na', u'��', u'\uff85', u'��', 'na', 'na', '3na' ),
  ( 'ni', u'��', u'\uff86', u'��', 'ni', 'ni', '3ni', '2ny' ),
  ( 'nu', u'��', u'\uff87', u'��', 'nu', 'nu', '3nu' ),
  ( 'ne', u'��', u'\uff88', u'��', 'ne', 'ne', '3ne' ),
  ( 'no', u'��', u'\uff89', u'��', 'no', 'no', '3no' ),
  
  ( 'ha', u'��', u'\uff8a', u'��', 'ha', 'ha', '3ha' ),
  ( 'hi', u'��', u'\uff8b', u'��', 'hi', 'hi', '3hi', '2hy' ),
  ( 'hu', u'��', u'\uff8c', u'��', 'hu', 'fu', '3hu', '3fu', '2f' ),
  ( 'he', u'��', u'\uff8d', u'��', 'he', 'he', '3he' ),
  ( 'ho', u'��', u'\uff8e', u'��', 'ho', 'ho', '3ho' ),
  
  ( 'ma', u'��', u'\uff8f', u'��', 'ma', 'ma', '3ma' ),
  ( 'mi', u'��', u'\uff90', u'��', 'mi', 'mi', '3mi', '2my' ),
  ( 'mu', u'��', u'\uff91', u'��', 'mu', 'mu', '3mu', '2m' ),
  ( 'me', u'��', u'\uff92', u'��', 'me', 'me', '3me' ),
  ( 'mo', u'��', u'\uff93', u'��', 'mo', 'mo', '3mo' ),
  
  ( 'ya', u'��', u'\uff94', u'��', 'ya', 'ya', '3ya' ),
  ( 'yu', u'��', u'\uff95', u'��', 'yu', 'yu', '3yu' ),
  ( 'ye', u'����', u'\uff72\uff6a', u'����', 'ye', 'ye', '3ye' ),
  ( 'yo', u'��', u'\uff96', u'��', 'yo', 'yo', '3yo' ),
  
  ( 'ra', u'��', u'\uff97', u'��', 'ra', 'ra', '3ra', '2la' ),
  ( 'ri', u'��', u'\uff98', u'��', 'ri', 'ri', '3ri' ,'2li', '2ry', '2ly' ),
  ( 'ru', u'��', u'\uff99', u'��', 'ru', 'ru', '3ru' ,'2lu', '2r', '2l' ),
  ( 're', u'��', u'\uff9a', u'��', 're', 'le', '3re', '2le' ),
  ( 'ro', u'��', u'\uff9b', u'��', 'ro', 'ro', '3ro', '2lo' ),
  
  ( 'wa', u'��', u'\uff9c', u'��', 'wa', 'wa', '3wa' ),
  ( 'wi', u'����', u'\uff73\uff68', u'����', 'wi', 'wi', '3whi', '3wi', '2wy', '2why' ),
  ( 'we', u'����', u'\uff73\uff6a', u'����', 'we', 'we', '3whe', '3we' ),
  ( 'wo', u'����', u'\uff73\uff6b', u'����', 'wo', 'wo', '1xwo', '2wo' ),
  
  ( 'Wi', u'��', u'', u'��', 'wi', 'i', '1xwi' ),
  ( 'We', u'��', u'', u'��', 'we', 'e', '1xwe' ),
  ( 'Wo', u'��', u'\uff66', u'��', 'wo', 'o', '1wo' ),

  ( '.n', u'��', u'\uff9d', u'��', "nn", 'n', '3n', "3n'", '3m:p', '2ng' ),
  
  # Special morae: They don't have actual pronunciation,
  #                but we keep them for IMEs.
  ( 'xW', u'��', u'\uff67', u'��', '(a)', '(a)', '1xa', '1la' ),
  ( 'xI', u'��', u'\uff68', u'��', '(i)', '(i)', '1xi', '1li' ),
  ( 'xV', u'��', u'\uff69', u'��', '(u)', '(u)', '1xu', '1lu' ),
  ( 'xE', u'��', u'\uff6a', u'��', '(e)', '(e)', '1xe', '1le' ),
  ( 'xR', u'��', u'\uff6b', u'��', '(o)', '(o)', '1xo', '1lo' ),
  ( 'xA', u'��', u'\uff6c', u'��', '(ya)', '(ya)', '1xya', '1lya' ),
  ( 'xU', u'��', u'\uff6d', u'��', '(yu)', '(yu)', '1xyu', '1lyu' ),
  ( 'xO', u'��', u'\uff6e', u'��', '(yo)', '(yo)', '1xyo', '1lyo' ),
  
  ( '!v', u'��', u'\uff9e', u'��', '(dakuten)', '(dakuten)' ),
  ( '!p', u'��', u'\uff9f', u'��', '(handakuten)', '(handakuten)' ),
  ( '!.', u'��', u'\uff61', u'��', '.', '.', '3.' ),
  ( '!,', u'��', u'\uff64', u'��', ',', ',', '3,' ),
  ( '!_', u'��', u'\uff65', u'��', '(nakaguro)', '(nakaguro)', '1x.' ),
  ( '![', u'��', u'\uff62', u'��', '[', '[', '3[' ),
  ( '!]', u'��', u'\uff63', u'��', ']', ']', '3]' ),
  
  # chouon
  ( '.-', u'��', u'\uff70', u'��', 'h', 'h', '1-', '2h' ),
  
  # choked sound (Sokuon)
  ( '.t', u'��', u'\uff6f', u'��', '>', '>', '1xtu', '1ltu',
    '3k:k', '3s:s', '3t:t', '3h:h', '3f:f', '3m:m', '3r:r', '3p:p',
    '3g:g', '3z:z', '3j:j', '3d:d', '3b:b', '3v:v', '3b:c', '3t:c' ),
  
  # voiced (Dakuon)
  ( 'ga', u'��', u'\uff76\uff9e', u'��', 'ga', 'ga', '3ga' ),
  ( 'gi', u'��', u'\uff77\uff9e', u'��', 'gi', 'gi', '3gi', '2gy' ),
  ( 'gu', u'��', u'\uff78\uff9e', u'��', 'gu', 'gu', '3gu', '2g'),
  ( 'ge', u'��', u'\uff79\uff9e', u'��', 'ge', 'ge', '3ge' ),
  ( 'go', u'��', u'\uff7a\uff9e', u'��', 'go', 'go', '3go' ),
  
  ( 'za', u'��', u'\uff7b\uff9e', u'��', 'za', 'za', '3za' ),
  ( 'zi', u'��', u'\uff7c\uff9e', u'��', 'zi', 'ji', '3ji', '1zi' ),
  ( 'zu', u'��', u'\uff7d\uff9e', u'��', 'zu', 'zu', '3zu', '2z' ),
  ( 'ze', u'��', u'\uff7e\uff9e', u'��', 'ze', 'ze', '3ze' ),
  ( 'zo', u'��', u'\uff7f\uff9e', u'��', 'zo', 'zo', '3zo' ),
  
  ( 'da', u'��', u'\uff80\uff9e', u'��', 'da', 'da', '3da' ),
  ( 'di', u'��', u'\uff81\uff9e', u'��', 'di', 'dzi', '3dzi', '1di' ),
  ( 'du', u'��', u'\uff82\uff9e', u'��', 'du', 'dzu', '3dzu', '1du' ),
  ( 'de', u'��', u'\uff83\uff9e', u'��', 'de', 'de', '3de' ),
  ( 'do', u'��', u'\uff84\uff9e', u'��', 'do', 'do', '3do', '2d' ),
  
  ( 'ba', u'��', u'\uff8a\uff9e', u'��', 'ba', 'ba', '3ba' ),
  ( 'bi', u'��', u'\uff8b\uff9e', u'��', 'bi', 'bi', '3bi', '2by' ),
  ( 'bu', u'��', u'\uff8c\uff9e', u'��', 'bu', 'bu', '3bu', '2b' ),
  ( 'be', u'��', u'\uff8d\uff9e', u'��', 'be', 'be', '3be' ),
  ( 'bo', u'��', u'\uff8e\uff9e', u'��', 'bo', 'bo', '3bo' ),
  
  # p- sound (Handakuon)
  ( 'pa', u'��', u'\uff8a\uff9f', u'��', 'pa', 'pa', '3pa' ),
  ( 'pi', u'��', u'\uff8b\uff9f', u'��', 'pi', 'pi', '3pi', '2py' ),
  ( 'pu', u'��', u'\uff8c\uff9f', u'��', 'pu', 'pu', '3pu', '2p' ),
  ( 'pe', u'��', u'\uff8d\uff9f', u'��', 'pe', 'pe', '3pe' ),
  ( 'po', u'��', u'\uff8e\uff9f', u'��', 'po', 'po', '3po' ),

  # double consonants (Youon)
  ( 'KA', u'����', u'\uff77\uff6c', u'����', 'kya', 'kya', '3kya' ),
  ( 'KU', u'����', u'\uff77\uff6d', u'����', 'kyu', 'kyu', '3kyu', '2cu' ),
  ( 'KE', u'����', u'\uff77\uff6a', u'����', 'kye', 'kye', '3kye' ),
  ( 'KO', u'����', u'\uff77\uff6e', u'����', 'kyo', 'kyo', '3kyo' ),

  ( 'kA', u'����', u'\uff78\uff67', u'����', 'qa', 'qa', '3qa' ),
  ( 'kI', u'����', u'\uff78\uff68', u'����', 'qi', 'qi', '3qi' ),
  ( 'kE', u'����', u'\uff78\uff6a', u'����', 'qe', 'qe', '3qe' ),
  ( 'kO', u'����', u'\uff78\uff6b', u'����', 'qo', 'qo', '3qo' ),
  
  ( 'SA', u'����', u'\uff7c\uff6c', u'����', 'sya', 'sha', '3sya', '3sha' ),
  ( 'SU', u'����', u'\uff7c\uff6d', u'����', 'syu', 'shu', '3syu', '3shu', '2sh' ),
  ( 'SE', u'����', u'\uff7c\uff6a', u'����', 'sye', 'she', '3sye', '3she' ),
  ( 'SO', u'����', u'\uff7c\uff6e', u'����', 'syo', 'sho', '3syo', '3sho' ),
  
  ( 'CA', u'����', u'\uff81\uff6c', u'����', 'tya', 'cha', '3tya', '1cya', '3cha' ),
  ( 'CU', u'����', u'\uff81\uff6d', u'����', 'tyu', 'chu', '3tyu', '1cyu', '3chu' ),
  ( 'CE', u'����', u'\uff81\uff6a', u'����', 'tye', 'che', '3tye', '1cye', '3che' ),
  ( 'CO', u'����', u'\uff81\uff6e', u'����', 'tyo', 'cho', '3tyo', '1cyo', '3cho' ),
  ( 'TI', u'�ƥ�', u'\uff83\uff68', u'�Ƥ�', 'tyi', 'ti', '3tyi', '3thi', '2ti' ),
  ( 'TU', u'�ƥ�', u'\uff83\uff6d', u'�Ƥ�', 'thu', 'tu', '3thu', '2tu' ),
  ( 'TO', u'�ȥ�', u'\uff84\uff69', u'�Ȥ�', 'to', 'to', '3tho', '2two' ),
  
  ( 'NA', u'�˥�', u'\uff86\uff6c', u'�ˤ�', 'nya', 'nya', '3nya' ),
  ( 'NU', u'�˥�', u'\uff86\uff6d', u'�ˤ�', 'nyu', 'nyu', '3nyu' ),
  ( 'NI', u'�˥�', u'\uff86\uff6a', u'�ˤ�', 'nye', 'nye', '3nye' ),
  ( 'NO', u'�˥�', u'\uff86\uff6e', u'�ˤ�', 'nyo', 'nyo', '3nyo' ),
  
  ( 'HA', u'�ҥ�', u'\uff8b\uff6c', u'�Ҥ�', 'hya', 'hya', '3hya' ),
  ( 'HU', u'�ҥ�', u'\uff8b\uff6d', u'�Ҥ�', 'hyu', 'hyu', '3hyu' ),
  ( 'HE', u'�ҥ�', u'\uff8b\uff6a', u'�Ҥ�', 'hye', 'hye', '3hye' ),
  ( 'HO', u'�ҥ�', u'\uff8b\uff6e', u'�Ҥ�', 'hyo', 'hyo', '3hyo' ),
  
  ( 'FA', u'�ե�', u'\uff8c\uff67', u'�դ�', 'fa', 'fa', '3fa' ),
  ( 'FI', u'�ե�', u'\uff8c\uff68', u'�դ�', 'fi', 'fi', '3fi', '2fy' ),
  ( 'FE', u'�ե�', u'\uff8c\uff6a', u'�դ�', 'fe', 'fe', '3fe' ),
  ( 'FO', u'�ե�', u'\uff8c\uff6b', u'�դ�', 'fo', 'fo', '3fo' ),
  ( 'FU', u'�ե�', u'\uff8c\uff6d', u'�դ�', 'fyu', 'fyu', '3fyu' ),
  ( 'Fo', u'�ե�', u'\uff8c\uff6e', u'�դ�', 'fyo', 'fyo', '3fyo' ),
  
  ( 'MA', u'�ߥ�', u'\uff90\uff6c', u'�ߤ�', 'mya', 'mya', '3mya' ),
  ( 'MU', u'�ߥ�', u'\uff90\uff6d', u'�ߤ�', 'myu', 'myu', '3myu' ),
  ( 'ME', u'�ߥ�', u'\uff90\uff6a', u'�ߤ�', 'mye', 'mye', '3mye' ),
  ( 'MO', u'�ߥ�', u'\uff90\uff6e', u'�ߤ�', 'myo', 'myo', '3myo' ),
  
  ( 'RA', u'���', u'\uff98\uff6c', u'���', 'rya', 'rya', '3rya', '2lya' ),
  ( 'RU', u'���', u'\uff98\uff6d', u'���', 'ryu', 'ryu', '3ryu', '2lyu' ),
  ( 'RE', u'�ꥧ', u'\uff98\uff6a', u'�ꤧ', 'rye', 'rye', '3rye', '2lye' ),
  ( 'RO', u'���', u'\uff98\uff6e', u'���', 'ryo', 'ryo', '3ryo', '2lyo' ),
  
  # double consonants + voiced
  ( 'GA', u'����', u'\uff77\uff9e\uff6c', u'����', 'gya', 'gya', '3gya' ),
  ( 'GU', u'����', u'\uff77\uff9e\uff6d', u'����', 'gyu', 'gyu', '3gyu' ),
  ( 'GE', u'����', u'\uff77\uff9e\uff6a', u'����', 'gye', 'gye', '3gye' ),
  ( 'GO', u'����', u'\uff77\uff9e\uff6e', u'����', 'gyo', 'gyo', '3gyo' ),
  
  ( 'Ja', u'����', u'\uff7c\uff9e\uff6c', u'����', 'zya', 'ja', '3zya', '3ja', '3zha' ),
  ( 'Ju', u'����', u'\uff7c\uff9e\uff6d', u'����', 'zyu', 'ju', '3zyu', '3ju', '3zhu' ),
  ( 'Je', u'����', u'\uff7c\uff9e\uff6a', u'����', 'zye', 'je', '3zye', '3je', '3zhe' ),
  ( 'Jo', u'����', u'\uff7c\uff9e\uff6e', u'����', 'zyo', 'jo', '3zyo', '3jo', '3zho' ),
  
  ( 'JA', u'�¥�', u'\uff81\uff9e\uff6c', u'�¤�', 'dya', 'dya', '3dya' ),
  ( 'JU', u'�¥�', u'\uff81\uff9e\uff6d', u'�¤�', 'dyu', 'dyu', '3dyu' ),
  ( 'JE', u'�¥�', u'\uff81\uff9e\uff6a', u'�¤�', 'dye', 'dye', '3dye' ),
  ( 'JO', u'�¥�', u'\uff81\uff9e\uff6e', u'�¤�', 'dyo', 'dyo', '3dyo' ),

  ( 'dI', u'�ǥ�', u'\uff83\uff9e\uff68', u'�Ǥ�', 'dhi', 'di', '3dyi', '3dhi', '2di' ),
  ( 'dU', u'�ǥ�', u'\uff83\uff9e\uff6d', u'�Ǥ�', 'dhu', 'du', '3dhu', '2du' ),
  ( 'dO', u'�ɥ�', u'\uff84\uff9e\uff69', u'�ɤ�', 'dho', 'dho', '3dho' ),
  
  ( 'BA', u'�ӥ�', u'\uff8b\uff9e\uff6c', u'�Ӥ�', 'bya', 'bya', '3bya' ),
  ( 'BU', u'�ӥ�', u'\uff8b\uff9e\uff6d', u'�Ӥ�', 'byu', 'byu', '3byu' ),
  ( 'BE', u'�ӥ�', u'\uff8b\uff9e\uff6a', u'�Ӥ�', 'bye', 'bye', '3bye' ),
  ( 'BO', u'�ӥ�', u'\uff8b\uff9e\uff6e', u'�Ӥ�', 'byo', 'byo', '3byo' ),
  
  ( 'va', u'����', u'\uff73\uff9e\uff67', u'������', 'va', 'va', '3va' ),
  ( 'vi', u'����', u'\uff73\uff9e\uff68', u'������', 'vi', 'vi', '3vi', '2vy' ),
  ( 'vu', u'��',   u'\uff73\uff9e',       u'����', 'vu', 'vu', '3vu', '2v' ),
  ( 've', u'����', u'\uff73\uff9e\uff6a', u'������', 've', 've', '3ve' ),
  ( 'vo', u'����', u'\uff73\uff9e\uff6b', u'������', 'vo', 'vo', '3vo' ),
  
  # double consonants + p-sound
  ( 'PA', u'�ԥ�', u'\uff8b\uff9f\uff6c', u'�Ԥ�', 'pya', 'pya', '3pya' ),
  ( 'PU', u'�ԥ�', u'\uff8b\uff9f\uff6d', u'�Ԥ�', 'pyu', 'pyu', '3pyu' ),
  ( 'PE', u'�ԥ�', u'\uff8b\uff9f\uff6a', u'�Ԥ�', 'pye', 'pye', '3pye' ),
  ( 'PO', u'�ԥ�', u'\uff8b\uff9f\uff6e', u'�Ԥ�', 'pyo', 'pyo', '3pyo' ),
]

SYMBOL = {
  u'��':' ', u'��':',', u'��':'.', u'��':',', u'��':'.',
  u'��':'-', u'��':':', u'��':';', u'��':'?', u'��':'!',
  u'��':'(dakuten)', u'��':'(handakuten)', u'��':"'", u'��':'`',
  u'��':'"', u'��':'^', u'��':'~', u'��':'_', u'��':'(repeat)',
  u'��':'(repeat-dakuten)', u'��':'(repeat)', u'��':'(repeat-dakuten)',
  u'��':'"', u'��':'(shime)', u'��':'0', u'��':'-', u'��':'--',
  u'��':' - ', u'��':'/', u'��':'\\', u'��':'-', u'��':'||',
  u'��':'|', u'��':'...', u'��':'..', u'��':'`', u'��':"'",
  u'��':'"', u'��':'"', u'��':'(', u'��':')', u'��':'[',
  u'��':']', u'��':'[', u'��':']', u'��':'{', u'��':'}',
  u'��':'<', u'��':'>', u'��':'<<', u'��':'>>', u'��':'"',
  u'��':'"', u'��':'[[', u'��':']]', u'��':'{{', u'��':'}}',
  u'��':'+', u'��':'-', u'��':'+-', u'��':'*', u'��':'/',
  u'��':'=', u'��':'!=', u'��':'<', u'��':'>', u'��':'<=',
  u'��':'>=', u'��':'(inf)', u'��':'(3dot-therefore)', u'��':'(male)',
  u'��':'(female)', u'��':'(degree)', u'��':"'", u'��':"''",
  u'��':'(Celsius)', u'��':'(Yen)', u'��':'$', u'��':'(Cent)',
  u'��':'(Pound)', u'��':'%', u'��':'#', u'��':'&', u'��':'*',
  u'��':'@', u'��':'(section)', u'��':'(star)', u'��':'(STAR)',
  u'��':'(circle)', u'��':'(CIRCLE)', u'��':'(circle2)', u'��':'(dia)',
  u'��':'(DIA)', u'��':'(box)', u'��':'(BOX)', u'��':'(triangle)',
  u'��':'(TRIANGLE)', u'��':'(tri2)', u'��':'(TRI2)', u'��':'(*)',
  u'��':'(Yuubin)', u'��':'(right)', u'��':'(left)', u'��':'(up)', u'��':'(down)',
  u'��':'(geta)', u'��':'(included)', u'��':'(including)',
  u'��':'(subsumed-equal)', u'��':'(subsuming-equal)', u'��':'(subsumed)',
  u'��':'(subsuming)', u'��':'(union)', u'��':'(intersection)',
  u'��':'(and)', u'��':'(or)', u'��':'(not)', u'��':'(=>)',
  u'��':'(<=>)', u'��':'(forall)', u'��':'(exists)', u'��':'(angle)',
  u'��':'(perpendicular)', u'��':'(arc)', u'��':'(partial)',
  u'��':'(nabra)', u'��':'(:=)', u'��':'(nearly=)', u'��':'(<<)',
  u'��':'(>>)', u'��':'(sqrt)', u'��':'(lazy)', u'��':'(proportional)',
  u'��':'(3dot-becasue)', u'��':'(integral)', u'��':'(integral2)',
  u'��':'(angstrom)', u'��':'(permil)', u'��':'(sharp)', u'��':'(flat)',
  u'��':'(note)', u'��':'(dagger)', u'��':'(ddagger)', u'��':'(paragraph)',
  u'��':'(O)',

  u'��':'(small-wa)',
  u'��':'(ka)', u'��':'(ko)', 

  u'��':'(ALPHA)', u'��':'(BETA)', u'��':'(GAMMA)', u'��':'(DELTA)',
  u'��':'(EPSILON)', u'��':'(ZETA)', u'��':'(ETA)', u'��':'(THETA)',
  u'��':'(IOTA)', u'��':'(KAPPA)', u'��':'(LAMBDA)', u'��':'(MU)',
  u'��':'(NU)', u'��':'(XI)', u'��':'(OMICRON)', u'��':'(PI)',
  u'��':'(RHO)', u'��':'(SIGMA)', u'��':'(TAU)', u'��':'(UPSILON)',
  u'��':'(PHI)', u'��':'(CHI)', u'��':'(PSI)', u'��':'(OMEGA)',
  u'��':'(alpha)', u'��':'(beta)', u'��':'(gamma)', u'��':'(delta)', 
  u'��':'(epsilon)', u'��':'(zeta)', u'��':'(eta)', u'��':'(theta)',
  u'��':'(iota)', u'��':'(kappa)', u'��':'(lambda)', u'��':'(mu)',
  u'��':'(nu)', u'��':'(xi)', u'��':'(omicron)', u'��':'(pi)',
  u'��':'(rho)', u'��':'(sigma)', u'��':'(tau)', u'��':'(upsilon)',
  u'��':'(phi)', u'��':'(chi)', u'��':'(psi)', u'��':'(omega)',
  
  u'��':'(C-A)', u'��':'(C-B")', u'��':'(C-V)', u'��':'(C-G)',
  u'��':'(C-D)', u'��':'(C-YE)', u'��':'(C-YO)', u'��':'(C-ZH)',
  u'��':'(C-Z)', u'��':'(C-II)', u'��':'(C-II")', u'��':'(C-K)', 
  u'��':'(C-L)', u'��':'(C-M)', u'��':'(C-N)', u'��':'(C-O)', 
  u'��':'(C-P)', u'��':'(C-R")', u'��':'(C-S)', u'��':'(C-T)',
  u'��':'(C-U)', u'��':'(C-F)', u'��':'(C-X)', u'��':'(C-TS)',
  u'��':'(C-CH)', u'��':'(C-SH)', u'��':'(C-SCH)', u'��':'(C-SOFT)',
  u'��':'(C-I)', u'��':'(C-SEP)', u'��':'(C-EH)', u'��':'(C-YU)',
  u'��':'(C-YA)', 
  
  u'��':'(c-a)', u'��':'(c-b)', u'��':'(c-v)', u'��':'(c-g)',
  u'��':'(c-g)', u'��':'(c-ye)', u'��':'(c-yo)', u'��':'(c-zh)',
  u'��':'(c-z)', u'��':'(c-ii)', u'��':'(c-ii:)', u'��':'(c-k)',
  u'��':'(c-l)', u'��':'(c-m)', u'��':'(c-n)', u'��':'(c-o)',
  u'��':'(c-p)', u'��':'(c-r)', u'��':'(c-s)', u'��':'(c-t)',
  u'��':'(c-u)', u'��':'(c-f)', u'��':'(c-x)', u'��':'(c-ts)',
  u'��':'(c-ch)', u'��':'(c-sh)', u'��':'(c-sch)', u'��':'(c-soft)',
  u'��':'(c-i)', u'��':'(c-sep)', u'��':'(c-eh)', u'��':'(c-yu)',
  u'��':'(c-ya)',
  
  u'��':'-', u'��':'|', u'��':'+', u'��':'+', u'��':'+',
  u'��':'+', u'��':'+', u'��':'+', u'��':'+', u'��':'+',
  u'��':'+', u'��':'=', u'��':'|', u'��':'+', u'��':'+',
  u'��':'+', u'��':'+', u'��':'+', u'��':'+', u'��':'+',
  u'��':'+', u'��':'+', u'��':'+', u'��':'+', u'��':'+',
  u'��':'+', u'��':'+', u'��':'+', u'��':'+', u'��':'+',
  u'��':'+', u'��':'+',
  }

# 0x20-0x7e:  !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~
ZENKAKU = (
  u'�����ɡ������ǡʡˡ��ܡ��ݡ������������������������������䡩'
  u'�����£ãģţƣǣȣɣʣˣ̣ͣΣϣУѣңӣԣգ֣ףأ٣ڡΡ��ϡ���'
  u'�ƣ���������������������������������Сáѡ�'
  )

HANKAKU = (
  ' !"#'
  "$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]"
  '^_`abcdefghijklmnopqrstuvwxyz{|}~'
  )

z2hmap = dict(zip(ZENKAKU, HANKAKU))
h2zmap = dict(zip(ZENKAKU, HANKAKU))

def zen2han(z):
  return ''.join( z2hmap.get(c,c) for c in z )

# Mora Object
class Mora:
  
  def __init__(self, mid, zenk, hank, zenh):
    self.mid = mid
    self.zenk = zenk
    self.hank = hank
    self.zenh = zenh
    return

  def __repr__(self):
    return '<%s>' % self.mid

  # unicode(m) or str(m) converts to katakana.
  def __str__(self):
    return self.zenk
  

##  Translation Table
##

# ParseTable
class ParseTable:
  
  def __init__(self):
    self.tbl = {}
    return

  def __contains__(self, k):
    # Different from (self.tbl in k) --
    # even if self.tbl[k] exists, it might be None.
    return self.tbl.get(k)

  def update(self, src):
    self.tbl.update(src.tbl)
    return

  def add(self, s, mora, allowconflict=False):
    if self.tbl.get(s) and not allowconflict:
      raise ValueError('%r (%r) is already defined: %r' %
                       (s, mora, self.tbl[s]))
    if ':' in s:
      (parselen, s) = (s.index(':'), s.replace(':',''))
    else:
      parselen = len(s)
    for i in range(len(s)):
      w = s[:i+1]
      if w == s:
        self.tbl[w] = (parselen, mora)
      elif w not in self.tbl:
        self.tbl[w] = None
    return
  
  def parse(self, s, i=0):
    while i < len(s):
      n = 1
      r = (1, s[i])
      while i+n <= len(s):
        w = zen2han(s[i:i+n]).lower()
        if w not in self.tbl: break
        x = self.tbl[w]
        if x:
          r = x
        n += 1
      (n, m) = r
      yield m
      i += n
    return

# GenTable
class GenTable(dict):

  def add(self, mora, s):
    if mora in self:
      raise ValueError('%r (%r) is already defined: %r' %
                       (mora, s, self[mora]))
    self[mora] = s
    return
    
  def generate(self, morae, addrule=False, nreduce=False):
    (m0,s0) = (None,'')
    for x in morae:
      if isinstance(x, Mora):
        assert x in self, 'Invalid mora: %r' % x
        (m1,s1) = (x, self[x])
      else:
        (m1,s1) = (None, x)
      if m0:
        if m0.mid == '.t':
          if addrule and s1[0] == 'c':
            s0 = 't'  # qT+"c" -> "tc"
          else:
            s0 = s1[0]
        elif m0.mid == '.n':
          if addrule and s1[0] == 'p':
            s0 = 'm'  # NN+"p" -> "mp"
          elif nreduce and (s1[0] not in 'auieon'):
            s0 = 'n'  # NN+C -> "n"+C
      yield s0
      (m0,s0) = (m1,s1)
    yield s0
    return


##  Initialization
##
MORA = {}
PARSE_OFFICIAL = ParseTable()
PARSE_OFFICIAL_ANNA = ParseTable()
PARSE_ENGLISH = ParseTable()
GEN_OFFICIAL = GenTable()
GEN_OFFICIAL_ANNA = GenTable()
GEN_ENGLISH = GenTable()
def initialize():
  NN = None
  for m in MORA_DATA:
    (mid, zenk, hank, zenh, p_off, p_eng) = m[:6]
    assert mid not in MORA
    assert isinstance(zenk, unicode)
    assert isinstance(hank, unicode)
    assert isinstance(zenh, unicode)
    mora = Mora(mid, zenk, hank, zenh)
    MORA[mid] = mora
    PARSE_OFFICIAL.add(zenk, mora, True)
    PARSE_OFFICIAL.add(hank, mora, True)
    PARSE_OFFICIAL.add(zenh, mora, True)
    PARSE_ENGLISH.add(zenk, mora, True)
    PARSE_ENGLISH.add(hank, mora, True)
    PARSE_ENGLISH.add(zenh, mora, True)
    for x in m[6:]:
      (c,k) = (ord(x[0])-48,x[1:])
      if c & 1:
        PARSE_OFFICIAL.add(k, mora)
      if c & 2:
        PARSE_ENGLISH.add(k, mora)
    if mid == '.n':
      NN = mora
    else:
      GEN_OFFICIAL.add(mora, p_off)
    GEN_ENGLISH.add(mora, p_eng)
  PARSE_OFFICIAL_ANNA.update(PARSE_OFFICIAL)
  PARSE_OFFICIAL.add('nn', NN)
  GEN_OFFICIAL_ANNA.update(GEN_OFFICIAL)
  GEN_OFFICIAL_ANNA.add(NN, "n'")
  GEN_OFFICIAL.add(NN, 'nn')
  return
initialize()


##  Aliases
##
PARSE_DEFAULT = PARSE_OFFICIAL
GEN_DEFAULT = GEN_OFFICIAL
def romm2kana(s, ignore=False, parser=PARSE_DEFAULT):
  morae = parser.parse(s)
  if ignore:
    morae = ( m for m in morae if isinstance(m, Mora) )
  return ''.join( unicode(m) for m in morae )
def kana2romm(s, ignore=False, parser=PARSE_DEFAULT, generator=GEN_DEFAULT):
  morae = parser.parse(s)
  if ignore:
    morae = ( m for m in morae if isinstance(m, Mora) )
  return ''.join(generator.generate(morae))

def official2kana(s, ignore=False):
  return romm2kana(s, ignore, PARSE_OFFICIAL)
def official_anna2kana(s, ignore=False):
  return romm2kana(s, ignore, PARSE_OFFICIAL_ANNA)
def english2kana(s, ignore=False):
  return romm2kana(s, ignore, PARSE_ENGLISH)

def kana2official(s, ignore=False):
  return kana2romm(s, ignore, PARSE_OFFICIAL, GEN_OFFICIAL)
def kana2official_anna(s, ignore=False):
  return kana2romm(s, ignore, PARSE_OFFICIAL_ANNA, GEN_OFFICIAL_ANNA)
def kana2english(s, ignore=False):
  return kana2romm(s, ignore, PARSE_ENGLISH, GEN_ENGLISH)

# Test cases
if __name__ == '__main__':
  import unittest

  class TestRoma(unittest.TestCase):

    def checkParse(self, table, s, morae0):
      morae = [ isinstance(m,Mora) and m.mid for m in table.parse(s) ]
      self.assertEqual(morae0, morae)
      
    def test_00_parse_basic_official(self):
      self.checkParse(PARSE_OFFICIAL,
                      'akasatana',
                      ['.a','ka','sa','ta','na'])
    def test_01_parse_basic_official_anna(self):
      self.checkParse(PARSE_OFFICIAL_ANNA,
                      'akasatana',
                      ['.a','ka','sa','ta','na'])
    def test_02_parse_basic_english(self):
      self.checkParse(PARSE_ENGLISH,
                      'akasatana',
                      ['.a','ka','sa','ta','na'])
    def test_03_parse_official_ta1(self):
      self.checkParse(PARSE_OFFICIAL,
                      'tatituteto',
                      ['ta','ti','tu','te','to'])
      return
    def test_03_parse_official_ta2(self):
      self.checkParse(PARSE_OFFICIAL,
                      'tachitsuteto',
                      ['ta','ti','tu','te','to'])
      return
    def test_04_parse_official_nn1(self):
      self.checkParse(PARSE_OFFICIAL,
                      'sonna,anna',
                      ['so','.n','.a','!,','.a','.n','.a'])
      return
    def test_04_parse_official_nn2(self):
      self.checkParse(PARSE_OFFICIAL,
                      'sonnna,annna',
                      ['so','.n','na','!,','.a','.n','na'])
      return
    def test_05_parse_official_anna_nn1(self):
      self.checkParse(PARSE_OFFICIAL_ANNA,
                      'sonna,anna',
                      ['so','.n','na','!,','.a','.n','na'])
      return
    def test_05_parse_official_anna_nn2(self):
      self.checkParse(PARSE_OFFICIAL_ANNA,
                      'sonnna,annna',
                      ['so','.n','.n','na','!,','.a','.n','.n','na'])
      return
    def test_06_parse_official_youon(self):
      self.checkParse(PARSE_OFFICIAL,
                      'dosyaburi',
                      ['do','SA','bu','ri'])
      return
    def test_06_parse_official_sokuon1(self):
      self.checkParse(PARSE_OFFICIAL,
                      'tyotto',
                      ['CO','.t','to'])
      return
    def test_06_parse_official_sokuon2(self):
      self.checkParse(PARSE_OFFICIAL,
                      'dotchimo',
                      ['do','.t','ti','mo'])
      return
    def test_07_parse_mixed(self):
      self.checkParse(PARSE_OFFICIAL,
                      u'aI�դ���',
                      ['.a','.i','.u','.e','.o'])
      return
    def test_07_parse_ignore(self):
      self.checkParse(PARSE_OFFICIAL,
                      u'ai$u��o',
                      ['.a','.i',False,'.u',False,'.o'])
      return

    def checkGen(self, table, morae, s0):
      s = ''.join(table.generate( MORA[x] for x in morae ))
      self.assertEqual(s0, s)
    def checkGenNReduce(self, table, morae, s0):
      s = ''.join(table.generate(( MORA[x] for x in morae ), nreduce=True))
      self.assertEqual(s0, s)
    def checkGenAddRule(self, table, morae, s0):
      s = ''.join(table.generate(( MORA[x] for x in morae ), addrule=True))
      self.assertEqual(s0, s)
    def checkGenRaw(self, table, morae, s0):
      s = ''.join(table.generate(morae))
      self.assertEqual(s0, s)

    def test_10_gen_basic_official(self):
      self.checkGen(GEN_OFFICIAL,
                    ['.a','ka','sa','ta','na'],
                    'akasatana')
    def test_11_gen_basic_official_anna(self):
      self.checkGen(GEN_OFFICIAL_ANNA,
                    ['.a','ka','sa','ta','na'],
                    'akasatana')
    def test_12_gen_basic_english(self):
      self.checkGen(GEN_ENGLISH,
                    ['.a','ka','sa','ta','na'],
                    'akasatana')
    def test_13_gen_official_ta(self):
      self.checkGen(GEN_OFFICIAL,
                    ['ta','ti','tu','te','to'],
                    'tatituteto')
    def test_14_gen_english_ta(self):
      self.checkGen(GEN_ENGLISH,
                    ['ta','ti','tu','te','to'],
                    'tachitsuteto')
    def test_15_gen_official_nn1(self):
      self.checkGen(GEN_OFFICIAL,
                    ['so','.n','.a','!,','.a','.n','.a'],
                    'sonna,anna')
    def test_15_gen_official_nn2(self):
      self.checkGen(GEN_OFFICIAL,
                    ['so','.n','na','!,','.a','.n','na'],
                    'sonnna,annna')
    def test_16_gen_official_nn_noreduce(self):
      self.checkGen(GEN_OFFICIAL,
                    ['so','.n','ka','!,','.a','.n','ka'],
                    'sonnka,annka')
    def test_16_gen_official_nn_reduce(self):
      self.checkGenNReduce(GEN_OFFICIAL,
                           ['so','.n','ka','!,','.a','.n','ka'],
                           'sonka,anka')
    def test_17_gen_official_anna_nn1(self):
      self.checkGen(GEN_OFFICIAL_ANNA,
                    ['so','.n','.a','!,','.a','.n','.a'],
                    "son'a,an'a")
    def test_17_gen_official_anna_nn2(self):
      self.checkGen(GEN_OFFICIAL_ANNA,
                    ['so','.n','na','!,','.a','.n','na'],
                    "son'na,an'na")
    def test_18_gen_official_anna_nn_noreduce(self):
      self.checkGen(GEN_OFFICIAL_ANNA,
                    ['so','.n','ka','!,','.a','.n','ka'],
                    "son'ka,an'ka")
    def test_18_gen_official_anna_nn_reduce(self):
      self.checkGenNReduce(GEN_OFFICIAL_ANNA,
                           ['so','.n','ka','!,','.a','.n','ka'],
                           'sonka,anka')
    def test_19_gen_official_addrule(self):
      self.checkGenAddRule(GEN_OFFICIAL,
                           ['ka','.n','pu'],
                           'kampu')
    def test_19_gen_english_addrule(self):
      self.checkGenAddRule(GEN_ENGLISH,
                           ['do','.t','ti','mo'],
                           'dotchimo')

    def test_20_gen_mixed(self):
      self.checkGenRaw(GEN_OFFICIAL,
                       [MORA['.a'], u'��u', MORA['.e']],
                       u'a��ue')
      
    def checkKana2Official(self, kana, r0):
      roma = kana2official(kana)
      self.assertEqual(roma, r0)
    def checkOfficial2Kana(self, roma, k0):
      kana = official2kana(roma)
      self.assertEqual(kana, k0)

    def test_30_kana2official_basic1(self):
      self.checkKana2Official(u'���礤�Ȥ��󤿡�����ʤ��Ȥ��äƤä��ɤ�',
                              u'tyoitoannta,sonnnakotoittekkedosa')
    def test_30_kana2official_basic2(self):
      self.checkKana2Official(u'�ˤä��⤵�ä��⡣',
                              u'nittimosattimo.')
    def test_31_kana2official_mixed(self):
      self.checkKana2Official(u'���礤�Ȥ��󤿥���ʥ��Ȥ��äƤä��ɥ���',
                              u'tyoitoanntasonnnakotoittekkedosa.')
    def test_32_kana2official_ignore(self):
      self.checkKana2Official(u'���礤�Ȥ��󤿡�������������ʤ��Ȥ��äƤä��ɤ���',
                              u'tyoitoannta����������sonnnakotoittekkedosa.')
    def test_33_official2kana_basic1(self):
      self.checkOfficial2Kana(u'choitoanta,sonnnakotoittekkedosa',
                              u'���祤�ȥ��󥿡�����ʥ��ȥ��åƥå��ɥ�')
    def test_33_official2kana_basic2(self):
      self.checkOfficial2Kana(u'nitchimosatchimo.',
                              u'�˥å��⥵�å��⡣')
  
  unittest.main()
