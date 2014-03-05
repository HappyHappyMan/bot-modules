# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import os
import logging
from modules.dbHandler import dbHandler

log = logging.getLogger('lastfm')

try:
    import requests, yaml  
except ImportError as e:
    log.error("Error importing modules: %s" % e.strerror)

API_URL = "http://ws.audioscrobbler.com/2.0/?method=%s&user=%s&api_key=%s&limit=1"


def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "lastfm.settings")
        return yaml.load(file(settings_path))
    except OSError:
            log.warning("Settings file for Last.fm not set up; please create a Last.fm API account and modify the example settings file.")
            return

def _add_lastfm(bot, user, args):
    db = dbHandler(bot.factory.getDBPath())
    lastid = args.split(" ")[0].strip().lower()

    db.set("lastfm", user, lastid)

    bot.say(bot.factory.getNick(user), "Last.fm username set!")
    return
    pass

def command_np(bot, user, channel, args):
    """Lastfm module! Usage: .np without arguments will return your now playing. .add lastfm "lastfm username" (no quotes) to add your username to the db."""

    settings = _import_yaml_data()
    db = dbHandler(bot.factory.getDBPath())

    # The user wants to retrieve now playing information
    query_nick = args.split(" ")[0].strip()
    log.debug("Querying database for lastid")
    if len(query_nick) > 0: # If they want somebody else's
        log.debug("Wanting lastid for %s" % query_nick)
        lastid = db.get("lastfm", query_nick)
    else: # If they want their own
        log.debug("Wanting lastid for self, %s" % user)
        lastid = db.get("lastfm", user)

    log.debug("Found lastid %s in db" % lastid)

    if lastid is None:
        log.debug("Lastid not found!")
        if len(query_nick) > 0:
            log.debug("length of query_nick is " + str(len(query_nick)))
            bot.say(channel, "User \x02%s\x02 doesn't exist in my db! They should look into that." % args.split(" ")[0])
        else:
            bot.say(channel, "You don't exist in my db! You should really look into that.")
        return

    ## Whoof. After that guantlet, we can be reasonably sure that we have valid input
    ## for the API call. Time to go get it.
    log.debug("Calling API for lastid %s now" % lastid)
    call_url = API_URL % ("user.getrecenttracks", str(lastid), settings["lastfm"]["key"])
    xmlreturn = requests.get(call_url)
    data = xmlreturn.content.encode('utf-8')
    tree = ET.fromstring(data)

    ## I do wish the etree library formatted everything into a dict like the json
    ## library does, then maybe this wouldn't seem like such a mess of magic
    ## integers. Nevertheless, this works, and is entirely motivated by the XML
    ## lastfm returns.
    try:
        artist = tree[0][0][0][0].text
    except IndexError:
        artist = tree[0][0][0].text
    track = tree[0][0][1].text
    album = tree[0][0][4].text
    nowplaying = tree[0][0].attrib
    if track is None:
        track = ""
    if album is None:
        album = ""
    else:
        album = " from album " + album
    if artist is None:
        artist = ""

    ## This will account for the nowplaying attribute lastfm returns, and format
    ## the output string appropriately. 
    if len(nowplaying) > 0:
        bot.say(channel, 'Last.fm \x034\x02|\x02\x03 \x02%s\x02 is listening to "%s" by %s%s \x034\x02|\x02\x03 http://www.last.fm/user/%s/now' %
                (lastid.encode('utf-8'), track.encode('utf-8'), artist.encode('utf-8'), album.encode('utf-8'), lastid.encode('utf-8')))
        return
    else:
        bot.say(channel, 'Last.fm \x034\x02|\x02\x03 \x02%s\x02 last listened to "%s" by %s%s \x034\x02|\x02\x03 http://www.last.fm/user/%s/now' %
                (lastid.encode('utf-8'), track.encode('utf-8'), artist.encode('utf-8'), album.encode('utf-8'), lastid.encode('utf-8')))
        return


def command_compare(bot, user, channel, args):

    settings = _import_yaml_data()
    db = dbHandler(bot.factory.getDBPath())

    COMPARE_URL = "http://ws.audioscrobbler.com/2.0/?method=tasteometer.compare&type1=user&type2=user&value1=%s&value2=%s&api_key=%s&limit=4"

    compare_nick = args.split(" ")[0].strip() # Ensure only one nick gets processed
    lastid = db.get("lastfm", compare_nick)
    yourid = db.get("lastfm", user)


    ## Handles the two possible ways a user couldn't exist to be compared with.
    if lastid is None:
        bot.say(channel, "User \x02%s\x02 doesn't exist in my db! They should look into that." % args.split(" ")[0])
        return
    if yourid is None:
        bot.say(channel, "User \x02%s\x02 doesn't exist in my db! They should look into that." % bot.factory.getNick())
        return
    else:
        import math  # Yeah, yeah, whatever
        call_url = COMPARE_URL % (lastid, yourid, settings["lastfm"]["key"])
        xmlreturn = requests.get(call_url)
        data = xmlreturn.content.encode('utf-8')
        tree = ET.fromstring(data)

        ## A particularly innovative way to round the float they send back to two
        ## decimal places. Nobody tell past me about math.round().
        number = math.ceil(float(tree[0][0][0].text) * 1000) / 1000 * 100 


        matches = int(tree[0][0][1].attrib['matches']) # extracts the common artists
        artistList = []

        ## Puts the top 4 common artists into a list.
        if matches < 4:
            for i in range(matches):
                artistList.append(tree[0][0][1][i][0].text)
        else:
            for i in range(4):
                artistList.append(tree[0][0][1][i][0].text)
        
        simString = "Similar artists include: "
        ## Formats the common artist list slightly better than a map() would, by
        ## being smart enough to not add a comma to the last entry.
        for r in range(len(artistList)):
            if (r + 1) == len(artistList):
                simString = simString + artistList[r]
            else:
                simString = simString + artistList[r] + ", "

        bot.say(channel, "Last.fm \x034\x02|\x02\x03 Users \x02%s\x02 and \x02%s\x02 have similarity %s%% \x034\x02|\x02\x03 %s" % 
            (lastid.encode('utf-8'), yourid.encode('utf-8'), number, simString.encode('utf-8')))
        return


def command_charts(bot, user, channel, args):
    settings = _import_yaml_data()

    db = dbHandler(bot.factory.getDBPath())

    ## Checks whether a user wants their charts or somebody else's by doing a len()
    ## check on " "-tokenized args list.
    if len(args.split(" ")[0]) > 0:
        nick = args.split(" ")[0]
        lastid = db.get("lastfm", nick)
    else:
        nick = bot.factory.getNick(user)
        lastid = db.get("lastfm", user)

    if lastid is None:
        bot.say(channel, "User \x02%s\x02 doesn't exist in my db! They should look into that." % nick)
        return


    call_url = "http://ws.audioscrobbler.com/2.0/?method=%s&user=%s&api_key=%s&limit=5&period=7day" % ("user.gettopartists", str(lastid), settings["lastfm"]["key"])
    xmlreturn = requests.get(call_url)
    data = xmlreturn.content.encode('utf-8')
    tree = ET.fromstring(data)

    artistList = []
    numArtists = 0
    for child in tree[0]:
        numArtists = numArtists + 1

    for i in range(numArtists):
        artistList.append((tree[0][i][0].text, tree[0][i][1].text))

    simString = ""
    ## Formats the common artist list slightly better than a map() would, by
    ## being smart enough to not add a comma to the last entry.
    for r in range(len(artistList)):
        if (r + 1) == len(artistList):
            simString = simString + artistList[r][0] + " " + "(" + artistList[r][1] + ")"
        else:
            simString = simString + artistList[r][0] + " " + "(" + artistList[r][1] + "), "

    bot.say(channel, "Last.fm weekly charts for \x02%s\x02 \x034\x02|\x02\x03 %s" % (lastid.encode('utf-8'), simString.encode('utf-8')))
    return
