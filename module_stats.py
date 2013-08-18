# -*- coding: utf-8 -*-

import psycopg2
import datetime
import random
import urllib
import urllib2
import hashlib
import os
import yaml


def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "db.settings")
        return yaml.load(file(settings_path))
    except OSError:
            print "Settings file for database not set up; please setup the postgres db and modify the example settings file."
            return


def command_stats(bot, user, channel, args):
    """Returns your usage stats (as near as can be approximated from your ident)"""
    SPECIAL_IDENTS = ["~Mibbit", "~quassel", "~androirc", "~kiwiirc", "Mibbit"]
    SPECIAL_CLOAK = "user/"
    real_ident = user.split("!")[1].split("@")[0]
    hostmask = user.split("@")[1]
    settings = _import_yaml_data()
    user = settings['db']['user']
    pw = settings['db']['pass']

    if SPECIAL_CLOAK in hostmask:
        search = ".*" + hostmask
    else:
        if real_ident in SPECIAL_IDENTS:
            user_ident = user.split("@")[0]
        else:
            user_ident = real_ident
        search = ".*" + user_ident + "@.*?"

     ## we are trying this
    bot.say(channel, "Calculating how much time you've wasted...")
    conn = psycopg2.connect(host="localhost", database="quassel", user=user, password=pw)
    cursor = conn.cursor()

    if real_ident == "~HappyMan":
        print "IS an admin"
        cursor.execute("SELECT COUNT(*) FROM backlog WHERE senderid=6 AND type=1")
        result = cursor.fetchall()
        conn.close()
        num_lines = int(result[0][0])
        bot.say(channel, "My owner has said %s lines since May 4 2012 00:33:55 EDT!" % (num_lines))
        return
    ##test db query
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

    cursor.execute("SELECT message,time FROM backlog WHERE message ~ 'PIC OF DAY:' AND bufferid=11 AND senderid=6")
    result = cursor.fetchall()
    length = len(result)

    conn.close()


    try: 
        int(args)
        ## stuff will happen here
        text = "POD \x02%s/%s\x02 \x02\x0313|\x03\x02 " % (int(args), length) + result[int(args) - 1][0] + " \x02\x0313|\x03\x02 Date posted: \x02%s\x02" % (result[int(args) - 1][1].strftime("%x %X"))
    except ValueError:
        ## stuff will also happen here, except this time it's more fun
        if args.strip():
            ## more things!
            if args.strip() == "recent":
                text = "Most recent POD \x02\x0313|\x03\x02 " + result[-1][0] + " \x02\x0313|\x03\x02 Date posted: \x02%s\x02" % (result[-1][1].strftime("%x %X"))
            elif args.strip() == "list":
                text = "POD list \x02\x0313|\x03\x02 " + _list(result)
            else:
                try:
                    date_object = datetime.datetime.strptime(args.strip(), "%m/%d/%y")
                except ValueError:
                    bot.say(channel, "Invalid date syntax.")

                match = 0
                delta_match = datetime.timedelta.max
                for x in range(len(result)):
                    delta = date_object - result[x][1]
                    if abs(delta.total_seconds()) < abs(delta_match.total_seconds()):
                        match = x
                        delta_match = delta

                text = "Search result | POD \x02%s/%s\x02 \x02\x0313|\x03\x02 " % (match + 1, length) + result[match][0] + " \x02\x0313|\x03\x02 Date posted: \x02%s\x02" % (result[match][1].strftime("%x %X"))
        else:
            res_num = random.randint(1, length + 1)
            text = "POD \x02%s/%s\x02 \x02\x0313|\x03\x02 " % (res_num, length) + result[res_num - 1][0] + " \x02\x0313|\x03\x02 Date posted: \x02%s\x02" % (result[res_num - 1][1].strftime("%x %X"))

    if channel == user:
        bot.say(bot.factory.getNick(user), text)
    else:
        bot.say(channel, text)


def _list(db_tuples):
    ret_str = ""
    hashy = hashlib.sha224()
    for x in range(len(db_tuples)):
        build_str = 'POD %s: "%s", posted on %s\n' % (x + 1, db_tuples[x][0], db_tuples[x][1].strftime("%x %X"))
        hashy.update(build_str)
        ret_str = ret_str + build_str

    hash_dict = yaml.load(file("modules/pods.txt"))
    hashy_str = hashy.digest()
    ret_str = urllib.quote(ret_str)

    with open("modules/pods.txt", "a") as hash_file:
        try:
            url = hash_dict[hashy_str]
            print "It worked!"
        except KeyError:
            results = urllib2.urlopen("http://ix.io", "f:1=%s" % ret_str)
            url = results.read().strip()
            hash_dict[hashy_str] = url
            yaml.dump(hash_dict, hash_file)

    return url
