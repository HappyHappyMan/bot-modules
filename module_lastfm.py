# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import sqlite3
import os
import logging

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


def command_np(bot, user, channel, args):
    """Lastfm module! Usage: .np without arguments will return your now playing. .np add "lastfm username" (no quotes) to add your name to the db."""

    settings = _import_yaml_data()

    DB = sqlite3.connect(settings['lastfm']['database'])
    usersplit = user.split('!', 1)[0]

    if args.split(" ")[0] == "add":
        lastid_updated = args.split(" ")[1].strip().lower()

        c = DB.cursor()
        testresult = c.execute("SELECT lastid FROM lookup WHERE nick LIKE ?", (usersplit.lower(),))
        try:
            testresult.fetchone()[0]
            worked = True
        except TypeError:
            worked = False

        if worked is True:
            vartuple = (str(lastid_updated).lower(), str(usersplit).lower())
            try:
                c.execute("UPDATE lookup SET lastid=(?) WHERE nick=(?)", vartuple)
            except sqlite3.Error, msg:
                log.error(msg)

            DB.commit()
            c.close()
            DB.close()

            bot.say(usersplit, "Last.fm username updated!")
            return
        else:
            vartuple = (str(usersplit).lower(), str(lastid_updated).lower())
            try:
                c.execute("INSERT INTO lookup VALUES (?, ?)", vartuple)
            except sqlite3.Error, msg:
                print msg

            DB.commit()
            c.close()
            DB.close()

            bot.say(usersplit, "Last.fm username set!")
            return
    else:
        c = DB.cursor()
        if len(args.split(" ")[0]) > 0:
            result = c.execute("SELECT lastid FROM lookup WHERE nick LIKE ?", (args.split(" ")[0].lower(),))
        else:
            result = c.execute("SELECT lastid FROM lookup WHERE nick LIKE ?", (usersplit.lower(),))
        try:
            lastid = result.fetchone()[0]
        except TypeError:
            if args.split(" ")[0].strip() == "":
                bot.say(channel, "You don't exist in my db! You should really look into that.")
                return
            else:
                bot.say(channel, "User \x02%s\x02 doesn't exist in my db! They should look into that." % args.split(" ")[0])
            return

        c.close()
        DB.close()

        call_url = API_URL % ("user.getrecenttracks", str(lastid), settings["lastfm"]["key"])
        xmlreturn = requests.get(call_url)
        data = xmlreturn.content.encode('utf-8')
        tree = ET.fromstring(data)

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

    DB = sqlite3.connect(settings["lastfm"]["database"])
    COMPARE_URL = "http://ws.audioscrobbler.com/2.0/?method=tasteometer.compare&type1=user&type2=user&value1=%s&value2=%s&api_key=%s&limit=4"
    usersplit = user.split("!", 1)[0]

    c = DB.cursor()
    argy = (args.split(" ")[0].strip().lower(),)
    me = (usersplit.strip().lower(),)
    lastid = ""
    yourid = ""

    for row in c.execute("SELECT lastid FROM lookup WHERE nick LIKE (?)", argy):
        lastid = row[0]
    for row in c.execute("SELECT lastid FROM lookup WHERE nick LIKE (?)", me):
        yourid = row[0]
    c.close()
    DB.close()

    if lastid == "":
        bot.say(channel, "User \x02%s\x02 doesn't exist in my db! They should look into that." % args.split(" ")[0])
        return
    if yourid == "":
        bot.say(channel, "User \x02%s\x02 doesn't exist in my db! They should look into that." % usersplit)
        return
    else:
        import math  # Yeah, yeah, whatever
        call_url = COMPARE_URL % (lastid, yourid, settings["lastfm"]["key"])
        xmlreturn = requests.get(call_url)
        data = xmlreturn.content.encode('utf-8')
        tree = ET.fromstring(data)

        number = math.ceil(float(tree[0][0][0].text) * 1000) / 1000 * 100


        matches = int(tree[0][0][1].attrib['matches'])
        artistList = []
        if matches < 4:
            for i in range(matches):
                artistList.append(tree[0][0][1][i][0].text)
        else:
            for i in range(4):
                artistList.append(tree[0][0][1][i][0].text)
        simString = "Similar artists include: "
        for r in range(len(artistList)):
            if (r + 1) == len(artistList):
                simString = simString + artistList[r]
            else:
                simString = simString + artistList[r] + ", "

        bot.say(channel, "Last.fm \x034\x02|\x02\x03 Users \x02%s\x02 and \x02%s\x02 have similarity %s%% \x034\x02|\x02\x03 %s" % 
            (lastid.encode('utf-8'), yourid.encode('utf-8'), number, simString.encode('utf-8')))


def command_charts(bot, user, channel, args):
    settings = _import_yaml_data()

    DB = sqlite3.connect(settings["lastfm"]["database"])
    usersplit = user.split("!", 1)[0]
    c = DB.cursor()

    if len(args.split(" ")[0]) > 0:
        print args.split(" ")[0]
        result = c.execute("SELECT lastid FROM lookup WHERE nick LIKE ?", (args.split(" ")[0].lower(),))
    else:
        result = c.execute("SELECT lastid FROM lookup WHERE nick LIKE ?", (usersplit.lower(),))

    lastid = result.fetchone()[0]

    if type(lastid) is None:
        bot.say(channel, "That user doesn't exist in my db! They should look into that.")

    c.close()
    DB.close()

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

    retString = ""
    for r in range(len(artistList)):
        if (r + 1) == len(artistList):
            retString = retString + artistList[r][0] + " " + "(" + artistList[r][1] + ")"
        else:
            retString = retString + artistList[r][0] + " " + "(" + artistList[r][1] + "), "

    bot.say(channel, "Last.fm weekly charts for \x02%s\x02 \x034\x02|\x02\x03 %s" % (lastid.encode('utf-8'), retString.encode('utf-8')))
