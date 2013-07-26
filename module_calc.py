# -*- coding: utf-8 -*-

import urllib2
import re


def parseGoogleJSON(text):
    ret_text = re.sub('\\\\x26#215;', "*", text)
    ret_text = re.sub("\\\\x3csup\\\\x3e", "^", ret_text)
    ret_text = re.sub("\\\\x3c/sup\\\\x3e", "", ret_text)
    return ret_text


def command_calc(bot, user, channel, args):
    if not args:
        return
    else:
        url = "http://www.google.com/ig/calculator?hl=en&q=%s"
        newurl = url % str(args).replace(" ", "%20").replace("+", "%2B").replace("x", "*")
        sub = urllib2.urlopen(newurl).read()
        lhs = re.search('lhs: "(.*?)"', sub)
        rhs = re.search('rhs: "(.*?)"', sub)
        if len(lhs.group(1)) > 0:
            rhs_return = parseGoogleJSON(rhs.group(1))
            return_line = "%s = %s" % (lhs.group(1), rhs_return)
        else:
            return_line = "no result"

    return bot.say(channel, return_line)
