# -*- coding: utf-8 -*-

"""
Interacting with reddit. 

I don't know what I'd like this module to be. Right now, I think
all it'll do is get the top post in a subreddit at a given time,
given the name of the subreddit. 
"""
import logging
import os
import json
import HTMLParser

log = logging.getLogger("reddit")

try:
    import requests
    import yaml
except ImportError as e:
    log.error("Error importing modules: %s" % e.strerror)

def _import_yaml_data(directory=os.curdir):
    """
    The standard _import_yaml_data() seen throughout the modules, but with the key 
    difference that this one doesn't look in the modules directory for its settings.
    This is to preserve per-bot differences even if the modules directory is symlinked,
    like my current setup. 
    """
    try:
        settings_path = os.path.join(directory, "rss.settings")
        return yaml.load(file(settings_path))
    except OSError:
        log.error("Settings file for rss not set up; please create an empty rss.settings file.")
        return


def get_reddit_api(data, kind):
    """
    Extracts relevant strings from data, and formats for output. Returns formatted
    string.
    """
    if kind == "t1":
        body = data['body']
        author = data['author']
        post_link = "http://redd.it/" + data['link_id'][3:]
        result = "New comment by \x02%s\x02 \x037\x02|\x02\x03 %s \x037\x02|\x02\x03 %s" % (author, body, post_link)
    else:
        timestamp = data['created_utc']
        title = HTMLParser.HTMLParser().unescape(data['title'])
        if data['is_self'] is False:
            url = "\x037\x02|\x02\x03 %s" % data['url']
        else:
            url = ""
        author = data['author']
        subreddit = data['subreddit']
        short = "http://redd.it/" + data['name'][3:] # This skips the t3_ part of the name, and gets us only the ID for the shortlink
        link = "\x037\x02|\x02\x03 " + short
        over_18 = data['over_18']
        result = "\x02Top post in r/%s\x02 \x037\x02|\x02\x03 %s by \x02%s\x02 %s %s" % (subreddit, title, author, url, link)
        if over_18 is True:
            result = result + " \x037\x02|\x02\x03 \x02NSFW\x02"
    return result


def command_reddit(bot, user, channel, args):
    """Give it a subreddit, it will give you the current top post in that subreddit."""

    headers = {'User-Agent': 'Lazybot/Claire by /u/Happy_Man'}
    data = requests.get("http://www.reddit.com/r/%s/.json" % args.strip(), headers=headers)

    if data.status_code == 403:
        bot.say(channel, "This subreddit is private. Sorry, I can't get in.")
        return
    if data.status_code == 429:
        log.info("Reddit returned 429, we're being rate-limited for some reason.")
        return

    try:
        data = json.loads(data.content.encode('utf-8'))
    except ValueError:
        bot.say(channel, "This subreddit doesn't exist, sorry.")
        return

    if data['data']['children'][0]['data']['stickied'] is True:
        topPost = data['data']['children'][1]['data']
    else:
        topPost = data['data']['children'][0]['data']

    returnstr = get_reddit_api(topPost, "t3")

    bot.say(channel, returnstr.encode('utf-8'))
    return

