# -*- encoding: utf-8 -*-

import os
import os.path
import sys
import re
import random
import linecache


def expl_parseterm(expl):
    expl = expl.split(" ")
    expl = expl[0]
    expl = expl.lower()
    expl = expl.strip()
    invalidchars = re.compile("[^a-z0-9\ :\.-]")
    expl = invalidchars.sub("_", expl)
    return expl


def check_params(bot, args, channel):
    """Do some initial checking for the stuff we need for every subcommand"""

    expldir = expl_getdir(channel)
    if not expldir:
        bot.log("No dbdir for channel %s, create %s to enable db." %
                (channel, os.path.join(sys.path[0], "expl/qdb", channel)))
        return False

    return expldir


def expl_getdir(channel):
    expldir = os.path.join(sys.path[0], "expl/qdb", channel)
    if not os.path.exists(expldir):
        return None
    return expldir


def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
        return i + 1


def command_qadd(bot, user, channel, args):
    """adds quote to db. Usage: .qadd <quote goes here, don't use any chevrons>"""

    try:
        expldir = check_params(bot, args, channel)
    except TypeError:
        bot.log("No expldir for channel %s" % channel)
        return

    if not args:
        return bot.say(user, "Try again please")

    with open(os.path.join(expldir, "quotes.txt"), "a") as quotestxt:
        quotestxt.write(args.strip('\n') + "\n")
    quotestxt.close()

    line_number = file_len(os.path.join(expldir, "quotes.txt"))

    bot.say(channel, "Quote %s successfully written" % line_number)


def command_qdel(bot, user, channel, args):
    """Deletes quote from database. Goes by line number, only available to bot owner."""

    if not isAdmin(user):
        bot.say(user, "You are not authorized to perform this command.")
        return
    else:
        try:
            expldir = check_params(bot, args, channel)
        except TypeError:
            bot.say(channel, "this is the most wtf part of everything")
            return

        args = args.split(" ", 1)
        if not args[0]:
            bot.say(user, "Try again please")
            return

        try:
            float(args[0])
        except ValueError:
            bot.say(user, "Try again please, this time with a number")
            return
        linecache.clearcache()
        del_line = linecache.getline(os.path.join(expldir, "quotes.txt"), args[0])

        f = open(os.path.join(expldir, "quotes.txt"), "r")
        lines = f.readlines()
        f.close()
        f = open(os.path.join(expldir, "quotes.txt"), "w")
        for line in lines:
            if line != del_line:
                f.write(line)
        f.close()

        bot.say(user, "Line successfully deleted")


def command_quote(bot, user, channel, args):
    """Returns a quote from the database. If you , returns random quote."""

    try:
        expldir = os.path.join(sys.path[0], "expl/qdb", channel)
    except TypeError:
        return

    argy = args.split(" ", 1)

    totlines = file_len(os.path.join(expldir, "quotes.txt"))
    try:
        int(argy[0])
    except ValueError:
        if len(args.strip()) < 1:
            quote_path = os.path.join(expldir, "quotes.txt")
            randy = random.randint(1, totlines)
            linecache.clearcache()
            return_line = linecache.getline(
                os.path.join(expldir, "quotes.txt"), randy).strip("\n")
            bot.say(channel, "Quote %s/%s: " % (randy, totlines) + return_line)
            #bot.say(channel, str(randy))
            return
        else:
            from fuzzywuzzy import fuzz
            args = args.lower()
            ratio = 0
            line_num = 0
            for x in range(totlines):
                line = linecache.getline(os.path.join(expldir, "quotes.txt"), x).strip("\n").lower()
                diff = fuzz.token_set_ratio(line, args)
                if diff > ratio:
                    ratio = diff
                    line_num = x
                    print "%s : %s" % (ratio, line_num)
            if ratio < 65:
                return
            return_line = linecache.getline(os.path.join(expldir, "quotes.txt"), line_num).strip("\n")
            bot.say(channel, "Quote %s/%s: " % (line_num, totlines) + return_line)
            bot.log("Input: %s | match ratio: %s | Output: %s" % (args, ratio, return_line))
            return

    if int(argy[0]) <= totlines:
        linecache.clearcache()
        return_line = linecache.getline(os.path.join(expldir, "quotes.txt"), (int(args[0]))).strip("\n")
        bot.say(channel, "Quote %s/%s: " % (argy[0], totlines) + return_line)
        return
