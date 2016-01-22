# -*- coding: utf-8 -*-

import logging
import json
from modules.dbHandler import dbHandler

log = logging.getLogger('tell')

def command_tell(bot, user, channel, args):
    db = dbHandler(bot.factory.getDBPath())
    try:
        with open('tell.txt', 'r+') as f:
            j = json.load(f)
    except ValueError:
        j = {}

    args = args.split(' ', 1)
    tellee = args[0]
    msg = args[1].strip()

    try:
        userid = db._get_userid(tellee)
    except IDNotFoundError:
        bot.say(channel, "{}: Both users must be registered in order to use this functionality."
                .format(bot.factory.getNick(user)))

    if channel not in j.keys():
        j[channel] = {}

    if userid is not None:
        teller = bot.factory.getNick(user)
        try:
            j[channel][str(userid)].append((teller, msg))
        except KeyError:
            j[channel][str(userid)] = []
            j[channel][str(userid)].append((teller, msg))
        bot.say(channel, "Message stored!")
    else:
        bot.say(channel, "{}: Both users must be registered in order to use this functionality."
                .format(bot.factory.getNick(user)))
    
    with open('tell.txt', 'w') as f:
        json.dump(j, f);

def handle_userJoined(bot, user, channel):
    db = dbHandler(bot.factory.getDBPath())
    with open('tell.txt', 'r+') as f:
        j = json.load(f)

    try:
        userid = db._get_userid(user.strip())
    except IDNotFoundError:
        return

    if userid is not None:
        try:
            tells = j[channel][str(userid)]
            if len(tells) > 1:
                bot.say(channel, "{}: You have multiple messages! Check your PMs to see them".format(
                        bot.factory.getNick(user)))
                for tell in tells:
                    bot.say(bot.factory.getNick(user), '{} left you a message: "{}"'.format(tell[0], tell[1]))
            elif len(tells) == 1:
                bot.say(channel, '{}: {} left you this message: "{}"'.format(
                        bot.factory.getNick(user), tells[0][0], tells[0][1]))
            else:
                return

            j[channel][str(userid)] = []

            with open('tell.txt', 'w') as f:
                json.dump(j, f)
        except KeyError:
            return

