# -*- encoding: utf-8 -*-

import os
import os.path
import sys
import re
import random
import linecache
import logging

log = logging.getLogger('quotedb')

try:
    from fuzzywuzzy import fuzz
    search_support = True
except ImportError as e:
    search_support = False
    log.warning("Fuzzy matching library not found, fuzzy searching will not work. To install, please go to https://github.com/seatgeek/fuzzywuzzy")

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
        log.info("No expldir for channel %s" % channel)
        return

    if not args:
        bot.say(user, "Try again please")
        return

    args = re.sub(r"\x03[\d+]*|\x02", "", args) # This removes any mIRC color codes, I think?

    with open(os.path.join(expldir, "quotes.txt"), "a") as quotestxt:
        quotestxt.write(args.strip('\n') + "\n")
    quotestxt.close()

    line_number = file_len(os.path.join(expldir, "quotes.txt"))

    bot.say(channel, "Quote %s successfully written" % line_number)


def command_q(bot, user, channel, args):
    return command_quote(bot, user, channel,args)

def command_quote(bot, user, channel, args):
    """Returns a quote from the database. If you provide numeric argument, returns that number quote from the database. If you provide text arguments, searches db. If no arguments, returns random quote."""

    try:
        expldir = os.path.join(sys.path[0], "expl/qdb", channel)
        os.path.join(expldir, "quotes.txt")
    except TypeError as e:
        bot.error("Error with quotes directory:")
        bot.error(e.strerror)
        return

    argy = args.split(" ", 1)

    totlines = file_len(os.path.join(expldir, "quotes.txt"))
    try:
        int(argy[0]) # Check if user is asking for a specific quote.
    except ValueError:
        if len(args.strip()) < 1: # If user is asking for a random quote, this will evaluate as True
            randy = random.randint(1, totlines)
            linecache.clearcache()
            return_line = linecache.getline(
                os.path.join(expldir, "quotes.txt"), randy).strip("\n")
            bot.say(channel, "Quote \x02%s/%s\x02 \x02\x036|\x03\x02 " % (randy, totlines) + return_line)
            return
        else: # If we're down here, they're searching for something
            if search_support is True: # Confirms that fuzzy matching has been installed
                args = args.lower()
                ratio = 0
                line_num = 0
                ## The basic architecture of the search is that it iterates through every quote
                ## and picks the one with the best "ratio", which is fuzzywuzzy's word for 
                ## "probability that this is what you're looking for". If no quote comes back with 
                ## a ratio over 65, then report that no results were found. You can mess with that 
                ## magic number if you want, but testing seems to bear out that any result under 65
                ## probability with a search string isn't actually what they're looking for.
                ##
                ## Right now, this will only return the most matchingest quote, rather than every
                ## quote over the magic ratio. This is because I can't think of a good way to 
                ## return multiple results without opening the door to spamming or gaming the 
                ## module. 
                for x in range(1, totlines + 1):
                    line = linecache.getline(os.path.join(expldir, "quotes.txt"), x).strip("\n").lower()
                    diff = fuzz.token_set_ratio(line, args)
                    if diff > ratio:
                        ratio = diff
                        line_num = x
                if ratio < 65:
                    log.info("Input: %s | match ratio: %s" % (args, ratio))
                    bot.say(channel, "No matches found.")
                    return

                return_line = linecache.getline(os.path.join(expldir, "quotes.txt"), line_num).strip("\n")
                log.info("Input: %s | match ratio: %s | Output: %s" % (args, ratio, return_line))
                bot.say(channel, "Search result \x02\x036|\x03\x02 Quote \x02%s/%s\x02 \x02\x036|\x03\x02 " % (line_num, totlines) + return_line)
            else:
                log.info("Please install fuzzywuzzy for search support. https://github.com/seatgeek/fuzzywuzzy")
                bot.say(channel, "Fuzzy matching support not installed. Admin(s), check log for more information.")
        return
    ## This block is if somebody asks for a specific quote. We do a quick check to make sure
    ## they're asking for a quote that exists (ie, query_int < num_total_quotes), 
    ## and if it's there, say it to the channel. 
    if int(argy[0]) <= totlines:
        linecache.clearcache()
        return_line = linecache.getline(os.path.join(expldir, "quotes.txt"), (int(argy[0]))).strip("\n")
        bot.say(channel, "Quote \x02%s/%s\x02 \x02\x036|\x03\x02 " % (argy[0], totlines) + return_line)
        return
    else:
        bot.say(channel, "That quote doesn't exist.")
        return

def command_qlist(bot, user, channel, args):
    """
    You say this in a channel, it will pastebin that channel's quotes list.
    """
    import urllib
    import datetime
    try:
        import requests
    except ImportError:
        log.warning("You need the requests module! Go install it, then try again")
        return

    try:
        expldir = os.path.join(sys.path[0], "expl/qdb", channel)
    except TypeError:
        return

    ## Get datetime object representing RIGHT NOW, then extract time and date 
    ## out of it and combine them together so that I can format it into a 
    ## pretty date string.
    now = datetime.datetime.now()
    time = now.time()
    date = now.date()
    td = datetime.datetime.combine(date, time).strftime("%B %d, %Y %X")

    totlines = file_len(os.path.join(expldir, "quotes.txt"))

    lines = "===================================Quote list for channel " + channel + " as of " + td + " Eastern===================================\n"

    ## Build massive string to POST to the pastebin
    for x in range(1, totlines+1):
        lines = lines + "Quote " + str(x) + ': ' + urllib.quote(linecache.getline(os.path.join(expldir, "quotes.txt"), x))

    ## POST
    urlRequest = requests.post("http://sprunge.us", "sprunge=%s" % lines)
    url = urlRequest.content.encode('utf-8') # will return url of paste

    bot.say(channel, url.strip())
    return
