# -*- coding: utf-8 -*-

"""
This module is specially crafted to only work with Quassel-managed Postgres databases.
"""

import psycopg2
import datetime
import random
import urllib
import hashlib
import os
import logging

log = logging.getLogger('stats')

try:
    import requests, yaml  
except ImportError as e:
    log.error("Error importing modules: %s" % e.strerror)

def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "db.settings")
        return yaml.load(file(settings_path))
    except OSError:
            log.warning("Settings file for database not set up; please setup the postgres db and modify the example settings file.")
            return


def command_stats(bot, user, channel, args):
    """Returns your usage stats (as near as can be approximated from your ident)"""
    ## these account for widely shared idents and cloaks, which we account for further 
    ## on when actually formulating the query.
    SPECIAL_IDENTS = ["~Mibbit", "~quassel", "~androirc", "~kiwiirc", "Mibbit", "androirc", "webchat"]
    SPECIAL_CLOAK = "user/"

    ## Disable on channels the database isn't set up for
    if channel == "#safefromparadox":
        bot.say(channel, "I'm sorry, this module isn't available on this channel.")
        return

    ## Get all the needed settings into variables
    real_ident = user.split("!")[1].split("@")[0]
    hostmask = user.split("@")[1]
    settings = _import_yaml_data()
    user = settings['db']['user']
    pw = settings['db']['pass']

    ## Account for special cloaks and idents like I said I would.
    if SPECIAL_CLOAK in hostmask:
        search = ".*" + hostmask
    else:
        if real_ident in SPECIAL_IDENTS:
            user_ident = user.split("@")[0]
        else:
            user_ident = real_ident
        search = ".*" + user_ident + "@.*?"

    bot.say(channel, "Calculating how much time you've wasted...")
    conn = psycopg2.connect(host="localhost", database="quassel", user=user, password=pw)
    cursor = conn.cursor()

    ## This block is actually highly specially crafted to just return my said lines,
    ## so you'll have to do some finagling if you want it to work with yours. 
    ## More specifically, you'll have to change the senderid to whatever yours is 
    ## and the ident to whatever yours is set to. Any other, more complicated changes
    ## I leave entirely up to you. 
    ## Of course, you'll also need to be using Quassel. But then, you read the disclaimer
    ## up top, I'm sure.
    if real_ident == "~HappyMan":
        print "IS an admin"
        cursor.execute("SELECT COUNT(*) FROM backlog WHERE senderid=6 AND type=1")
        result = cursor.fetchall()
        conn.close()
        num_lines = int(result[0][0])
        bot.say(channel, "My owner has said %s lines since May 4 2012 00:33:55 EDT!" % (num_lines))
        return
    ## General DB query. I think it's pretty self-explanatory, but just in case...
    ## This query first searches for all the senderids associated with a particular sender,
    ## by doing a regex-based search for their ident string. It then executes COUNT(*) on 
    ## the backlog for all those senderids. the type field matches only regular sent lines,
    ## not even /me lines. I think /me lines are type 4. You can add those in if you want.
    cursor.execute("SELECT COUNT(*) FROM backlog WHERE senderid IN (SELECT senderid FROM sender WHERE sender ~ %s) AND type=1", (search,))
    result = cursor.fetchall()
    num_lines = int(result[0][0])
    bot.say(channel, "User %s has said, as far as this bot can figure, %s lines since May 4 2012 00:33:55 EDT." % (search.strip(".*").strip("@.*?"), num_lines))
    conn.close()


def command_pod(bot, user, channel, args):
    """Pic of day access. .pod recent gives you the most recent, .pod with no arguments gives you a random pod, .pod followed by either a date (MM/DD/YY format only) or a number will return either the closest POD to that date or the POD matching that number. .pod list will give you a link to a dump of all PODs."""

    settings = _import_yaml_data()
    user = settings['db']['user']
    pw = settings['db']['pass']

    conn = psycopg2.connect(host="localhost", database="quassel", user=user, password=pw)
    cursor = conn.cursor()

    ## Once again, this query is specially crafted to only return things I've said 
    ## in a specific channel that begin with a specific string ("PIC OF DAY:"). 
    cursor.execute("SELECT message,time FROM backlog WHERE message ~ 'PIC OF DAY:' AND bufferid=11 AND senderid=6")
    result = cursor.fetchall()
    length = len(result)

    conn.close()


    try: 
        ## This block evaluates if args was a number
        int(args)
        text = "POD \x02%s/%s\x02 \x02\x0313|\x03\x02 " % (int(args), length) + result[int(args) - 1][0] + " \x02\x0313|\x03\x02 Date posted: \x02%s\x02" % (result[int(args) - 1][1].strftime("%x %X"))
    except ValueError:
        ## If args wasn't a number, we come down here to where the real fun is
        if args.strip(): ## if it wasn't blank
            if args.strip() == "recent":
                text = "Most recent POD \x02\x0313|\x03\x02 " + result[-1][0] + " \x02\x0313|\x03\x02 Date posted: \x02%s\x02" % (result[-1][1].strftime("%x %X"))
            elif args.strip() == "list":
                text = "POD list \x02\x0313|\x03\x02 " + _list(result) # goes and gets the list
            else:
                try:
                    ## checks the date syntax. 
                    ## TODO: look into dateutil library to make arbitrary datestrings possible
                    date_object = datetime.datetime.strptime(args.strip(), "%m/%d/%y")
                except ValueError:
                    bot.say(channel, "Invalid date syntax.")

                ## This block searches for the closest match to the input time by comparing
                ## timedeltas. We initialize delta_Match to be the max timedelta possible, 
                ## and then iterate through looking for the closest (least absolute value)
                ## timedelta.
                match = 0
                delta_match = datetime.timedelta.max
                for x in range(len(result)):
                    delta = date_object - result[x][1]
                    if abs(delta.total_seconds()) < abs(delta_match.total_seconds()):
                        match = x
                        delta_match = delta

                text = "Search result | POD \x02%s/%s\x02 \x02\x0313|\x03\x02 " % (match + 1, length) + result[match][0] + " \x02\x0313|\x03\x02 Date posted: \x02%s\x02" % (result[match][1].strftime("%x %X"))
        else:
            ## Here is the boringest part, where we just return the specified POD. 
            res_num = random.randint(1, length + 1)
            text = "POD \x02%s/%s\x02 \x02\x0313|\x03\x02 " % (res_num, length) + result[res_num - 1][0] + " \x02\x0313|\x03\x02 Date posted: \x02%s\x02" % (result[res_num - 1][1].strftime("%x %X"))

    if channel == user:
        bot.say(bot.factory.getNick(user), text)
    else:
        bot.say(channel, text)
    return


def _list(db_tuples):
    """
    The most convoluted way to do kind of thing ever invented, I think.
    The objective is to store the pastebin links for POD lists, so we don't waste time
    resending them every time somebody asks. Instead, we waste time hashing the returns 
    every time. I'm honestly not sure which is better. Probably just resending them.
    """
    ret_str = ""
    hashy = hashlib.sha224() # sha224 hashes to ascii characters only, which makes them serializable.
    ## Builds the POD list up, along with the hash query.
    for x in range(len(db_tuples)):
        build_str = 'POD %s: "%s", posted on %s\n' % (x + 1, db_tuples[x][0], db_tuples[x][1].strftime("%x %X"))
        hashy.update(build_str)
        ret_str = ret_str + build_str

    ## pods.txt stores a dict(str -> str)
    ##                   dict(hash of POD list -> url of pastebin)
    hash_dict = yaml.load(file("modules/pods.txt"))
    hashy_str = hashy.digest() # Do the hashing

    with open("modules/pods.txt", "a") as hash_file:
        try:
            url = hash_dict[hashy_str] # If it's present, fantastic!
        except KeyError:
            # If not, go do things with the internet
            ret_str = urllib.quote(ret_str)
            results = requests.post("http://ix.io", "f:1=%s" % ret_str)
            url = results.content.encode('utf-8').strip()
            hash_dict[hashy_str] = url
            yaml.dump(hash_dict, hash_file)

    return url
