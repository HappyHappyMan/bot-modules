# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import urllib2
import sqlite3
import yaml
import os

##IMPLEMENT THIS THING USE THE EXECUTE LINE TO IMPLEMENT OK? OK##


API_URL = "http://ws.audioscrobbler.com/2.0/?method=%s&user=%s&api_key=%s&limit=1"


def _import_yaml_data(directory=os.curdir):
    if os.path.exists(directory):
        settings_path = os.path.join(directory, "modules", "lastfm.settings")
        return yaml.load(file(settings_path))
    else:
        print "Settings file for Last.fm not set up; please create a Last.fm API account and modify the example settings file."
        return


def command_np(bot, user, channel, args):
    """Usage: .np without arguments will return your now playing. .np add "lastfm username" (no quotes) to add your name to the db."""

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
            print vartuple
            try:
                c.execute("UPDATE lookup SET lastid=(?) WHERE nick=(?)", vartuple)
            except sqlite3.Error, msg:
                print msg

            DB.commit()
            c.close()
            DB.close()

            bot.say(usersplit, "Last.fm username updated!")
            return
        else:
            vartuple = (str(usersplit).lower(), str(lastid_updated).lower())
            print vartuple
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
            print args.split(" ")[0]
            result = c.execute("SELECT lastid FROM lookup WHERE nick LIKE ?", (args.split(" ")[0].lower(),))
        else:
            result = c.execute("SELECT lastid FROM lookup WHERE nick LIKE ?", (usersplit.lower(),))
        lastid = result.fetchone()[0]

        if type(lastid) is None:
            bot.say(usersplit, "Please set your lastfm username: .np add")
            bot.say(channel, "User %s doesn't exist in my db! They should look into that." % args.split(" ")[0])
        print lastid

        c.close()
        DB.close()

        call_url = API_URL % ("user.getrecenttracks", str(lastid), settings["lastfm"]["key"])
        xmlreturn = urllib2.urlopen(call_url)
        data = xmlreturn.read()
        xmlreturn.close()
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
            bot.say(channel, 'Last.fm | %s is listening to "%s" by %s%s | http://www.last.fm/user/%s' %
                    (lastid.encode('utf-8'), track.encode('utf-8'), artist.encode('utf-8'), album.encode('utf-8'), lastid.encode('utf-8')))
            return
        else:
            bot.say(channel, 'Last.fm | %s last listened to "%s" by %s%s | http://www.last.fm/user/%s' %
                    (lastid.encode('utf-8'), track.encode('utf-8'), artist.encode('utf-8'), album.encode('utf-8'), lastid.encode('utf-8')))
            return


def command_compare(bot, user, channel, args):
    DB = sqlite3.connect(settings["lastfm"]["database"])
    COMPARE_URL = "http://ws.audioscrobbler.com/2.0/?method=tasteometer.compare&type1=user&type2=user&value1=%s&value2=%s&api_key=%s&limit=4"
    usersplit = user.split("!", 1)[0]

    c = DB.cursor()
    argy = (args.split(" ")[0].strip().lower(),)
    me = (usersplit.strip().lower(),)
    lastid = ""
    yourid = ""
    print argy, me
    for row in c.execute("SELECT lastid FROM lookup WHERE nick LIKE (?)", argy):
        lastid = row[0]
    for row in c.execute("SELECT lastid FROM lookup WHERE nick LIKE (?)", me):
        yourid = row[0]
    c.close()
    DB.close()

    if lastid == "":
        bot.say(channel, "User %s doesn't exist in my db! They should look into that." % args.split(" ")[0])
        return
    if yourid == "":
        bot.say(channel, "User %s doesn't exist in my db! They should look into that." % usersplit)
        return
    else:
        import math  # Yeah, yeah, whatever
        call_url = COMPARE_URL % (lastid, yourid, settings["lastfm"]["key"])
        xmlreturn = urllib2.urlopen(call_url)
        data = xmlreturn.read()
        xmlreturn.close()
        tree = ET.fromstring(data)

        number = math.ceil(float(tree[0][0][0].text) * 1000) / 1000 * 100
        print number

        matches = int(tree[0][0][1].attrib['matches'])
        print matches
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

        bot.say(channel, "Last.fm | Users %s and %s have similarity %s%% | %s" % 
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
    xmlreturn = urllib2.urlopen(call_url)
    data = xmlreturn.read()
    xmlreturn.close()
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

    bot.say(channel, "Last.fm weekly charts for %s: %s" % (lastid.encode('utf-8'), retString.encode('utf-8')))
