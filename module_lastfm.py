# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import os
import logging
from modules.dbHandler import dbHandler

log = logging.getLogger('lastfm')
# log.setLevel(20) # suppress debug output

try:
    import requests
    import yaml
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

    query_nick = args.split(" ")[0].strip()

    if query_nick == "add":
        bot.say(channel, 'Use .add lastfm "lastfm username" to add your lastfm to the db.')
        return
    log.debug("Querying database for lastid")
    if len(query_nick) > 0:  # If they want somebody else's lfm info
        log.debug("Wanting lastid for %s" % query_nick)
        lastid = db.get("lastfm", query_nick.strip())
    else:  # If they want their own
        log.debug("Wanting lastid for self, %s" % user)
        lastid = db.get("lastfm", user.strip())

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
    try:
        xmlreturn = requests.get(call_url)
    except requests.exceptions.ConnectionError:
        log.error("Max retries exceeded, notify user to try again in a couple seconds")
        bot.say(channel, "Last.fm didn't respond. Try again in a few seconds.")
        return

    if xmlreturn.status_code is not 200:
        # bot.say(channel, "Wow, looks like somebody didn't read the help text properly before adding their name to the db. Try again.")
        return

    data = xmlreturn.content
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


def command_charts(bot, user, channel, args):
    """Gets yours or somebody else's top five artists over the last week"""
    settings = _import_yaml_data()

    db = dbHandler(bot.factory.getDBPath())

    ## Checks whether a user wants their charts or somebody else's by doing a len()
    ## check on " "-tokenized args list.
    if len(args.split(" ")[0]) > 0:
        nick = args.split(" ")[0]
        lastid = db.get("lastfm", nick.strip())
    else:
        nick = bot.factory.getNick(user)
        lastid = db.get("lastfm", user.strip())

    if lastid is None:
        bot.say(channel, "User \x02%s\x02 doesn't exist in my db! They should look into that." % nick)
        return

    call_url = "http://ws.audioscrobbler.com/2.0/?method=%s&user=%s&api_key=%s&limit=5&period=7day" % ("user.gettopartists", str(lastid), settings["lastfm"]["key"])
    xmlreturn = requests.get(call_url)
    data = xmlreturn.content
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
