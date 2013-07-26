# -*- coding: utf-8 -*-

import psycopg2


# def command_stats(bot, user, channel, args):
#     """Returns your usage stats for this channel using your current ident."""

#     ident = user.split("!")[1].split("@")[0]

#     conn = sqlite3.connect("/home/sri/.config/quassel-irc.org/quassel-storage.sqlite")

#     c = conn.cursor()

#     chan = c.execute("SELECT bufferid FROM buffer WHERE buffername LIKE ?",(channel,))

#     chanresult = chan.fetchone()[0]
#     print chanresult

#     ident2 = "%" + ident + "@%"
#     print ident2

#     output = c.execute("SELECT COUNT(*) FROM backlog WHERE type = 1 AND senderid in(SELECT senderid FROM sender WHERE sender LIKE (?)) AND bufferid = ?",(ident2,chanresult))
#     output = output.fetchone()
#     print output[0]
#     c.close()
#     conn.close()



#     bot.say(channel, "User with ident %s has said %s lines in this channel." % (ident, output[0]))

## the format of the query here is going to be 'SELECT COUNT(*) FROM backlog WHERE senderid IN (SELECT senderid FROM sender WHERE sender ~ '.*~ident@.*?') AND type=1;'

def command_stats(bot, user, channel, args):
    """Returns your usage stats (as near as can be approximated from your ident)"""
    SPECIAL_IDENTS = ["~Mibbit", "~quassel", "~androirc"]
    real_ident = user.split("!")[1].split("@")[0]
    if real_ident in SPECIAL_IDENTS:
        user_ident = user.split("@")[0]
    else:
        user_ident = real_ident

    ident = ".*" + user_ident + "@.*?"

     ## we are trying this

    conn = psycopg2.connect(host="localhost", database="quassel", user="postgres", password="KittyKat")
    cursor = conn.cursor()

    ##test db query
    cursor.execute("SELECT COUNT(*) FROM backlog WHERE senderid IN (SELECT senderid FROM sender WHERE sender ~ %s) AND type=1", (ident,)) 
    result = cursor.fetchall()
    num_lines = int(result[0][0])
    bot.say(channel, "User with ident %s has said, as far as this bot can figure, %s lines since May 4 2012 00:33:55 EDT." % (user_ident, num_lines))
    conn.close()
