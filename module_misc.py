# -*- coding: utf-8 -*-

import random
import BeautifulSoup
import urllib2

def command_roll(bot, user, channel, args):
    """rolls dice. Usage: .roll xdy where x is the number of dice and y is the number of sides on each die"""
    nick = user.split('!', 1)[0]
    try:
        index = args.index('d')
    except ValueError:
        bot.say(channel, "The dice ricochet off the table and clatter onto the floor. Your peers laugh at you because you can't even roll virtual dice properly. Feel very ashamed, then go read the .help")
        return
    num = args[:index]
    args = args[index+1:]

    if int(args) < 16:
        arr = []
        for x in range(int(num)):
            arr.append(random.randint(1, int(args)))
    else:
        bot.say(channel, "I'm sorry, I don't have that many dice, %s." % nick)
        return

    if int(num) == 1:
        bot.say(channel, nick + ": You rolled a " + str(arr[0]))
    else:
        bot.say(channel, nick + ": You rolled a " + ', a '.join(map(str, arr[:-1])) + " and a " + str(arr[-1]) + " for a total of " + str(sum(arr)))
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

def command_btc(bot, user, channel, args):
    """Give it an abbreviation for a currency, like usd or jpy, and it will tell you how much of that currency one bitcoin is worth. Defaults to usd."""
    import json
    data = urllib2.urlopen("https://coinbase.com/api/v1/currencies/exchange_rates")
    data = json.load(data)

    try:
        if args:
            conv = 'btc_to_' + args
        else:
            conv = 'btc_to_usd'
        rate = data[conv]
    except KeyError:
        bot.say(channel, "Not a valid currency.")
        return

    bot.say(channel, "1 btc is worth %s %s" % (rate.encode('utf-8'), conv[-3:]))