# -*- coding: utf-8 -*-

import requests
import logging

log = logging.getLogger('misc')

def command_roll(bot, user, channel, args):
    """rolls dice. Usage: .roll xdy where x is the number of dice and y is the number of sides on each die"""
    import random
    nick = user.split('!', 1)[0]
    try:
        index = args.index('d')
    except ValueError:
        bot.say(channel, "The dice ricochet off the table and clatter onto the floor. Your peers laugh at you because you can't even roll virtual dice properly. Feel very ashamed, then go read the .help")
        return
    num = args[:index]
    args = args[index+1:]

    if int(num) < 16:
        arr = []
        for x in range(int(num)):
            arr.append(random.randint(1, int(args)))
    else:
        bot.say(channel, "I'm sorry, I don't have that many dice, %s." % nick)
        return

    if int(args) > 20:
        bot.say(channel, "I don't have a die with that many sides. Because those are expensive. Go buy some for me.")
        return

    if int(num) == 1:
        bot.say(channel, nick + ": You rolled a " + str(arr[0]))
    else:
        bot.say(channel, nick + ": You rolled a " + ', a '.join(map(str, arr[:-1])) + " and a " + str(arr[-1]) + " for a total of " + str(sum(arr)))
    return

def command_changelog(bot, user, channel, args):
    """Changelog!"""
    import json

    log.debug(args)
    log.debug(type(args))
    try:
        args = int(args) - 1
        log.debug("We have found an int! It is " + str(args))
    except ValueError:
        log.debug("There are no args!")
        args = 0

    r = requests.get("https://api.github.com/repos/SriRamanujam/bot-modules/commits")
    j = json.loads(r.content.encode('utf-8'))


    if args > 29:
        args = 0

    message = j[args]['commit']['message'].encode("utf-8")
    bot.say(channel, "Changelog %s: %s" % (str(args + 1), message))


def command_isup(bot, user, channel, args):
    """Give it a url, it will tell you if it's up or not."""
    import BeautifulSoup

    nick = user.split("!", 1)[0]
    args = args.split(" ",)[0]
    isup = requests.get("http://isup.me/%s" % args)
    soup = BeautifulSoup.BeautifulSoup(isup.content.encode('utf-8'))

    if user == channel:
        channel = nick

    if "It's not just you" in soup.div.text:
        bot.say(channel, "%s seems to be down for everyone, %s." % (args, nick))
    elif "interwho" in soup.div.text:
        bot.say(channel, "%s: Enter a valid url you pansy-pants" % (nick))
    else:
        bot.say(channel, "It's just you, %s, %s is up from here." % (nick, args))
    return

def command_btc(bot, user, channel, args):
    """Give it an abbreviation for a currency, like usd or jpy, and it will tell you how much of that currency one bitcoin is worth. Defaults to usd."""
    import json
    data = requests.get("https://coinbase.com/api/v1/currencies/exchange_rates")
    data = json.loads(data.content.encode('utf-8'))

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

def command_doge(bot, user, channel, args):
    """This tells you how much a single dogecoin is worth in USD."""
    import json
    data = requests.get("http://data.bter.com/api/1/ticker/doge_usd")
    j = json.loads(str(data.content.encode('utf-8')))
    if j['result'] == "true":
        amount = j['last']
    else:
        bot.say(channel, "Try again later, something's wrong with the API.")
        return
    bot.say(channel, "1 dogecoin is worth %s USD." % amount)
    return
