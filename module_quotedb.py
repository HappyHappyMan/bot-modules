# -*- encoding: utf-8 -*-

import os
import os.path
import sys
import re
import random
import linecache
import logging

log = logging.getLogger('quotedb')

def check_params(bot, args, channel):
    """Do some initial checking for the stuff we need for every subcommand"""

    expldir = expl_getdir(channel)
    if not expldir:
        log.warning("No dbdir for channel %s, create %s to enable db." %
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

    args = re.sub(r"\x03[\d+]*|\x02", "", args)

    with open(os.path.join(expldir, "quotes.txt"), "a") as quotestxt:
        quotestxt.write(args.strip('\n') + "\n")
    quotestxt.close()

    line_number = file_len(os.path.join(expldir, "quotes.txt"))

    bot.say(channel, "Quote %s successfully written" % line_number)


def command_quote(bot, user, channel, args):
    """Returns a quote from the database. If you provide numeric argument, returns that number quote from the database. If you provide text arguments, searches db. If no arguments, returns random quote."""

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
            bot.say(channel, "Quote \x02%s/%s\x02 \x02\x036|\x03\x02 " % (randy, totlines) + return_line)
            #bot.say(channel, str(randy))
            return
        else:
            from fuzzywuzzy import fuzz
            args = args.lower()
            ratio = 0
            line_num = 0
            for x in range(1, totlines + 1):
                line = linecache.getline(os.path.join(expldir, "quotes.txt"), x).strip("\n").lower()
                diff = fuzz.token_set_ratio(line, args)
                if diff > ratio:
                    ratio = diff
                    line_num = x
                    print "%s : %s" % (line_num, ratio)
            if ratio < 65:
                bot.log("Input: %s | match ratio: %s" % (args, ratio))
                bot.say(channel, "No matches found.")
                return
            return_line = linecache.getline(os.path.join(expldir, "quotes.txt"), line_num).strip("\n")
            bot.say(channel, "Search result \x02\x036|\x03\x02 Quote \x02%s/%s\x02 \x02\x036|\x03\x02 " % (line_num, totlines) + return_line)
            bot.log("Input: %s | match ratio: %s | Output: %s" % (args, ratio, return_line))
            return

    if int(argy[0]) <= totlines:
        linecache.clearcache()
        return_line = linecache.getline(os.path.join(expldir, "quotes.txt"), (int(argy[0]))).strip("\n")
        bot.say(channel, "Quote \x02%s/%s\x02 \x02\x036|\x03\x02 " % (argy[0], totlines) + return_line)
        return
