"""
This module reports when a link is a media file over 5 MB.
"""
import requests
import re
import logging

log = logging.getLogger('urlsize')

def module_url(bot, user, channel, args):
    """Gets the url size if the content is a media file."""
    data = requests.get(args)
    log.debug("Now in urlsize")
    try:
        log.debug("Regexing for media content")
        regex = re.findall(r'video/*|audio/*|image/*', data.headers['content-type'])
        if (len(regex) > 0) and (int(data.headers['content-length']) > (5*1024000)):
            log.debug("Valid media content detected")
            if 'content-type' in data.headers.keys():
                contentType = data.headers['content-type']
            else:
                contentType = "Unknown"
            size = int(data.headers['content-length']) / 1024000
            bot.say(channel, "File size: %s MB - Content-Type: %s" % (size, contentType))
            return
        else:
            log.debug("Media content too small")
            return
    except KeyError:
        log.warning("Unknown data type, ignoring as it is possible security risk")
        return

