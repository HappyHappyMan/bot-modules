# -*- encoding: utf-8 -*-

###TODO###
##Test assumption of line 77##

import os
import os.path
import sys
import re
import random
import fnmatch
import linecache



def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
        return i + 1

# def command_addkpop(bot, user, channel, args):
#     """adds quote to db. Usage: .qadd <quote goes here, don't use any chevrons>"""


#     if not args:
#         return bot.say(user, "Try again please")

#     args = args.split(" ")
#     for arg in args:
#         result = heavy_lifting(arg)
#         if result == 3:
#             bot.say(user, "%s seems to be private!" % (arg))
#         elif result == 0:
#             bot.say(user, "Video %s too recent, no data for it yet!" % (arg))
#         elif result == 5:
#             bot.say(user, "Youtube videos only, please!")
#         else:
#             with open("/home/sri/kpop.txt", "a") as quotestxt:
#                 quotestxt.write(result.encode('utf-8') + "\n")
#             quotestxt.close()
#             bot.say(user, "Video added!")
            

    #bot.say(channel, "Video(s) successfully added")
    #return

def heavy_lifting(url):
    gdata_url = "http://gdata.youtube.com/feeds/api/videos/%s"

    match = re.match("https?://youtu.be/(.*)", url)
    if not match:
        match = re.match("https?://.*?youtube.com/watch\?.*?v=([^&]+)", url)
    if match:
        infourl = gdata_url % match.group(1)
        bs = getUrl(infourl, True).getBS()

        entry = bs.first("entry")


        if not entry:
            #log.info("Video too recent, no info through API yet.")
            #bot.say(user, "video too recent, no info through API yet.")
            return 0
        ##test out this if condition
        if bs.string == "Private Video":
            #log.info("video either doesn't exist or is private, follow up")
            #bot.say(user, infourl + " needs to be checked up on, video either doesn't exist or is private")
            return 3
        else:
            media = entry.first("media:group")
            title = media.first("media:title").string
            return "%s | %s" % (url, title)
    else:
        return 5


# def command_kpop(bot, user, channel, args):
#     """Returns a random video link from the database."""

#     #args = args.split(" ", 1)

#     totlines = file_len("/home/sri/bots/testbot/modules/kpop.txt")

#     randy = random.randint(1, totlines)
#     linecache.clearcache()
#     return_line = linecache.getline("/home/sri/bots/testbot/modules/kpop.txt", randy).strip("\n")
#     #bot.say(channel, "Quote %s/%s: " % (randy, totlines) + return_line)
#     bot.say(channel, return_line)
#     return