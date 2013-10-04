# -*- coding: utf-8 -*-


import BeautifulSoup as bs
import urllib2
import HTMLParser
import re

UD_URL = "http://www.urbandictionary.com/define.php?term=%s"


def command_ud(bot, user, channel, args):
    """.ud word def#. ie, to get the second definition for the word Google, you'd type .ud Google 2. Defaults to the first definition, if no number is given."""
    queryWord = args.split(" ")[0]

    try:
        defNum = int(args.split(" ")[-1])
        print "num specified"
        numGiven = True
    except ValueError:
        print "num not specified"
        numGiven = False
        defNum = 1

    queryWord = ""
    if numGiven is True:
        for word in args.split(" ")[:-1]:
            queryWord = queryWord + word + "+"
    if numGiven is False:
        for word in args.split(" ")[:]:
            queryWord = queryWord + word + "+"

    print queryWord
    print defNum

    urlobj = urllib2.urlopen(UD_URL % queryWord)

    soup = bs.BeautifulSoup(urlobj.read())

    
    entries = soup.findAll(attrs={'id':'entries'})
    defs = entries[0].findAll(attrs={'id':re.compile(r'entry_*')})
    shortlinks = entries[0].findAll(attrs={'class':'word'})
    numResults = len(defs)

    defComplete = defs[defNum - 1].findAll(attrs={'class':'definition'})[0].findAll(text=True)
    shortlink = shortlinks[defNum - 1].a['href']

    ## time to build up the complete definition from any and all links
    defText = ""
    for item in defComplete:
        defText = defText + item

    textLen = 300 - (44 + len(shortlink))
    if len(defText) > textLen:
        trunclen = textLen - 1
        while True:
            if defText[trunclen] == " ":
                break
            else:
                trunclen = trunclen - 1
                continue
        defText = defText[:trunclen] + "..."
    defText = HTMLParser.HTMLParser().unescape(defText)
    returnstr = "UD Definition of \x02%s\x02 (Definition %s of %s) \x02\x035|\x03\x02 %s \x02\x035|\x03\x02 %s" % (queryWord.strip("+").replace("+", " "), defNum, numResults, defText, shortlink)

    usersplit = user.split('!', 1)[0]
    if channel == user:
        channel = usersplit

    bot.say(channel, returnstr.encode('utf-8'))

    return
