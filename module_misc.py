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
    """This tells you how much a single dogecoin is worth in whatever currency you want. Defaults to USD."""
    import json
    if not args:
        args = "usd"
    data = requests.get("https://api.cryptonator.com/api/ticker/doge-{}".format(args.lower()))
    j = json.loads(str(data.content.encode('utf-8')))
    if j['success'] == True:
        try:
            amount = j['ticker']['price']
        except IndexError:
            bot.say(channel, "Pricing information not available for this currency at this time.")
            return
    else:
        bot.say(channel, "Try again later, something's wrong with the API.")
        return
    bot.say(channel, "1 dogecoin is worth {} {}.".format(amount, args.upper()))
    return

def command_8ball(bot, user, channel, args):
    """It's an 8ball function, it does exactly what you think it does."""
    from random import randint
    response_list = ["It is certain",
            "It is decidedly so",
            "Without a doubt",
            "Yes definitely",
            "You may rely on it",
            "As I see it, yes",
            "Most likely",
            "Outlook good",
            "Yes",
            "Signs point to yes",
            "Reply hazy try again",
            "Ask again later",
            "Better not tell you now",
            "Cannot predict now",
            "Concentrate and ask again",
            "Don't count on it",
            "My reply is no",
            "My sources say no",
            "Outlook not so good",
            "Very doubtful"
            ]
    bot.say(channel, "%s: %s" % (bot.factory.getNick(user), response_list[randint(0, len(response_list) - 1)]))
    return

def command_horoscope(bot, user, channel, args):
    try:
        from lxml import etree
    except ImportError as e:
        log.error("Module not found: %s", e)
        return
    data = requests.get("http://www.findyourfate.com/rss/dailyhoroscope-feed.asp?sign={}".format(args.title()))
    root = etree.fromstring(data.content)

    descs = root.xpath("//description")
    if len(descs) != 2:
        bot.say(channel, "{}: Sign not found".format(bot.factory.getNick(user)))
        return
    else:
        desc = descs[1].text
    bot.say(channel, "{}: Your personal horoscope for {} | {}".format(bot.factory.getNick(user), args.title(), desc))
    return

def command_imdb(bot, user, channel, args):
    """Give it a movie title and it'll search imdb"""
    import urllib
    data = requests.get("http://omdbapi.com/?t={}&y=&plot=short&r=json".format(urllib.quote(args)))
    j = data.json()
    if j['Response'] == "True":
        bot.say(channel, "{} ({}) | {} | Rated {}, released {} | Metascore: {} | http://www.imdb.com/title/{}/".format(
            j['Title'].encode('utf-8'), j['Year'].encode('utf-8'), j['Plot'].encode('utf-8'), j['Rated'].encode('utf-8'), j['Released'].encode('utf-8'), j['Metascore'].encode('utf-8'), j['imdbID'].encode('utf-8')))
    else:
        bot.say(channel, '"{}" not found. Check for typos, or try being more specific.'.format(args))
    return

