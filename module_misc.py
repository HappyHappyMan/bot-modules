# -*- coding: utf-8 -*-

import random
import BeautifulSoup
import urllib2

def command_roll(bot, user, channel, args):
    """rolls dice"""
    nick = user.split('!', 1)[0]
    if args[0] == "d":
        args = args[1:]
    try:
        bot.say(channel, nick + ": you rolled a " + str(random.randint(1, int(args))))
    except ValueError:
        bot.say(channel, "Let's try to stay within the bounds of reality, okay, " + nick + "?")
    return

def command_isup(bot, user, channel, args):
    """Give it a url, it will tell you if it's up or not."""
    nick = user.split("!", 1)[0]
    args = args.split(" ",)[0]
    isup = urllib2.urlopen("http://isup.me/%s" % args)
    soup = BeautifulSoup.BeautifulSoup(isup)

    if user == channel:
        channel = nick

    if "It's not just you" in soup.div.text:
        bot.say(channel, "%s seems to be down for everyone, %s." % (args, nick))
    else:
        bot.say(channel, "It's just you, %s, %s is up from here." % (nick, args))

    return