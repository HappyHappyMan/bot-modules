# -*- coding: utf-8 -*-

import random

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