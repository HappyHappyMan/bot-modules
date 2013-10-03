# -*- coding: utf-8 -*-


import BeautifulSoup as bs
import urllib2
import HTMLParser

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

    results = soup.findAll("td", attrs={'class': 'index'})
    numResults = len(results)
        ## time to build up the complete definition from any and all links
    defComplete = results[defNum - 1].parent.nextSibling.nextSibling.findAll(attrs={'class': 'definition'})[0].findAll(text=True)
    defText = ""
    for item in defComplete:
        defText = defText + item

    #definition = results[defNum - 1].parent.nextSibling.nextSibling.div.contents[0].replace("&quot;", '"')
    shortlink = results[defNum - 1].next.next['href']
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

    bot.say(channel, returnstr.encode('utf-8'))

    return
