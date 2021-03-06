# -*- coding: utf-8 -*-


import bs4
import HTMLParser
import logging

log = logging.getLogger('ud')

try:
    import requests
except ImportError as e:
    log.error("Error importing modules: %s" % e.strerror)

UD_URL = "http://www.urbandictionary.com/define.php?term=%s"

def command_ud(bot, user, channel, args):
    """.ud word def:#. ie, to get the second definition for the word Google, you'd type .ud Google:2. Defaults to the first definition, if no number is given."""
    queryWord = args.split(":")[0].replace(" ", "+")
    if channel == user:
        channel = bot.factory.getNick(user)

    try:
        defNum = int(args.split(":")[1]) - 1
    except ValueError:
        defNum = 0
    except IndexError:
        defNum = 0

    urlobj = requests.get(UD_URL % queryWord)

    try:
        soup = bs4.BeautifulSoup(urlobj.content, 'html5lib') # prefer super fast method
    except TypeError:
        soup = bs4.BeautifulSoup(urlobj.content) # fallback to slower default

    defs = soup.findAll(attrs={'class':'def-panel'})

    numResults = len(defs)

    ## Check that we don't try to get a definition that doesn't exist.
    try:
        definition = defs[defNum]
    except IndexError:
        bot.say(channel, "Invalid number.")
        return

    ## Building the shortlink.
    log.debug(definition.attrs)
    try:
        defId = definition['data-defid']
        shortlink = "http://%s.urbanup.com/%s" % (queryWord.strip("+").replace("+", "-"), defId)
    except KeyError:
        ## Gentle reminders to some who tend to overuse the function.
        if 'tripgod' in user.split('!', 1)[0]:
            bot.say(channel, "tripgod, have you perhaps tried GOOGLING SHIT FIRST?!")
        else:
            bot.say(channel, "Word not found.")
        return


    ## Build our definition.
    defText = definition.find(attrs={'class':'meaning'}).text.strip()
    defText = HTMLParser.HTMLParser().unescape(defText)

    ## Magic numbers! Or in other words, truncate the definition so the total length 
    ## of the say() is such that it can all fit on one line. 
    maxLen = 316
    textLen = 17 + len(queryWord) + 23 + 7 + len(shortlink) + 3 + len(defText)
    if textLen > maxLen:
        truncLen = maxLen - (17 + len(queryWord) + 23 + 7 + len(shortlink) + 3)
        while True:
            if defText[truncLen] == " ":
                break
            else:
                truncLen = truncLen - 1
                continue
        defText = defText[:truncLen] + "..."

    returnstr = "UD Definition of \x02%s\x02 (Definition %s of %s) \x02\x035|\x03\x02 %s \x02\x035|\x03\x02 %s" % (queryWord.strip("+").replace("+", " "), defNum + 1, numResults, defText, shortlink)


    bot.say(channel, returnstr.encode('utf-8'))

    return
