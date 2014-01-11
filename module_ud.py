# -*- coding: utf-8 -*-


import BeautifulSoup as bs
import urllib2
import HTMLParser

UD_URL = "http://www.urbandictionary.com/define.php?term=%s"


def command_ud(bot, user, channel, args):
    """.ud word def#. ie, to get the second definition for the word Google, you'd type .ud Google 2. Defaults to the first definition, if no number is given."""
    queryWord = args.split(" ")[0]

    try:
        defNum = int(args.split(" ")[-1]) - 1
        print "num specified"
        numGiven = True
    except ValueError:
        print "num not specified"
        numGiven = False
        defNum = 0

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
    try:
        defs = entries[0].findAll(attrs={'class':'definition'})
    except IndexError:
        if 'tripgod' in user.split('!', 1)[0]:
            bot.say(channel, "tripgod, have you perhaps tried GOOGLING SHIT FIRST?!")
        return

    shortlinkHtml = entries[0].findAll(attrs={'class':'word'})[defNum]
    defidIndex = shortlinkHtml.a['href'].index('defid=')
    shortlink = "http://%s.urbanup.com/%s" % (queryWord.strip("+").replace("+", "-"), shortlinkHtml.a['href'][defidIndex:])
    numResults = len(defs)

    try:
        defText = defs[defNum].text
    except IndexError:
        bot.say(channel, "Invalid number.")
        return

    defText = HTMLParser.HTMLParser().unescape(defText)
    print defText

    maxLen = 316
    textLen = 17 + len(queryWord) + 23 + 7 + len(shortlink) + 3 + len(defText) ## so that everything fits in one msg
    if textLen > maxLen:
        truncLen = 17 + len(queryWord) + 23 + 7 + len(shortlink) + 3
        while True:
            if defText[truncLen] == " ":
                break
            else:
                truncLen = truncLen - 1
                continue
        defText = defText[:truncLen] + "..."

    returnstr = "UD Definition of \x02%s\x02 (Definition %s of %s) \x02\x035|\x03\x02 %s \x02\x035|\x03\x02 %s" % (queryWord.strip("+").replace("+", " "), defNum + 1, numResults, defText, shortlink)

    usersplit = user.split('!', 1)[0]
    if channel == user:
        channel = usersplit

    bot.say(channel, returnstr.encode('utf-8'))

    return
