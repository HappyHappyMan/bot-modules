# -*- coding: utf-8 -*-

"""
RSS rotator, improved version.

Only works with Reddit feeds now, but that's okay, since
nobody needs RSS feeds of anything else.
"""

from threading import Thread
import requests
import time
import os
import json
import HTMLParser
import logging
import logging.handlers

try:
    import feedparser
    from twisted.internet import reactor
    import yaml
    init_ok = True
except ImportError, error:
    print("Error starting rss module: %s" % error)
    init_ok = False

log = logging.getLogger('rss') 

### Globals, sigh...###
global timestamp_dict

def event_signedon(bot):
    """Starts rotator, triggered when bot signs on to network"""
    if bot.nickname == "Lazybot_v3":
        return

    settings = _import_yaml_data()
    current_time = time.mktime(time.gmtime(time.time()))

    global timestamp_dict

    timestamp_dict = {}

    for channel in settings['channels'].keys(): # Initialize timestamps to current time
        timestamp_dict[channel] = {}
        for url in settings['channels'][channel]:
            timestamp_dict[channel][url] = current_time
    delay = settings['delay']
    rotator(bot, delay) # Sends the rotator off and spinning

def get_reddit_api(url):

    headers_lib = {}
    headers_lib["User-Agent"] = "Lazybot/Claire by Happy_Man"

    content = requests.get(url, headers=headers_lib)
    api_return = json.loads(content.content.encode('utf-8'))

    if not content:
        log.info("No content received for url " + url)
        return "", 0
    data = api_return[0]['data']['children'][0]['data']
    timestamp = data['created_utc']
    title = HTMLParser.HTMLParser().unescape(data['title'])
    author = data['author']
    subreddit = data['subreddit']
    short = "http://redd.it/" + data['name'][3:]
    link = "\x037\x02|\x02\x03 " + short
    over_18 = data['over_18']
    result = "\x02r/%s/new\x02 \x037\x02|\x02\x03 %s by \x02%s\x02 %s" % (subreddit, title, author, link)
    if over_18 is True:
        result = result + " \x037\x02|\x02\x03 \x02NSFW\x02"
    return result, timestamp

def process_rss(bot):
    log.debug("RSS processing started")

    global timestamp_dict

    settings = _import_yaml_data()
    chans = settings['channels']
    result_dict = {}
    
    for channel in chans.keys():
        result_dict[channel] = []
        ## This handles issues when you add a new feed ##
        for url in chans[channel]:
            try:
                timestamp_dict[channel][url]
            except KeyError:
                timestamp_dict[channel][url] = time.mktime(time.gmtime(time.time()))

            feed_data = feedparser.parse(url)
            log.debug("Now retrieving " + url)

            for entry in feed_data.entries:
                if (time.mktime(entry['updated_parsed']) > timestamp_dict[channel][url]):
                    log.debug("We have a new item! Hooray!")
                    result_str, timestamp = get_reddit_api(entry['link'] + ".json")
                    result_dict[channel].append(result_str)
            ## This line updates the timestamp for the next go-around ## 
            timestamp_dict[channel][url] = time.mktime(feed_data.entries[0]['updated_parsed'])

    for channel in result_dict:
        log.debug(len(result_dict[channel]))
        if len(result_dict[channel]) > 0:
            for x in range(len(result_dict[channel])):
                bot.say(channel, result_dict[channel][x].encode('utf-8'))
                time.sleep(0.75)
    return

def rotator(bot, delay):
    """Starts up the rotator"""
    try:
        t = Thread(target=process_rss, args=(bot,))
        t.daemon = True
        t.start()
        t.join()
        reactor.callLater(delay, rotator, bot, delay)
    except Exception:
        log.error("Rotator error")

def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "rss.settings")
        return yaml.load(file(settings_path))
    except OSError:
        log.error("Settings file for rss not set up; please create an empty rss.settings file.")
        return

def _yaml_dump(settings_file, directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "rss.settings")
        stream = file(settings_path, 'w')
        yaml.dump(settings_file, stream)
    except OSError:
        log.error("Settings file for rss not set up; please create an empty rss.settings file.")
    return

def _add_rss_feed(bot, channel, feed_url):
    """Adds RSS feeds to the database"""
    settings = _import_yaml_data()
    try:
        settings['channels'][channel].append(feed_url)
        _yaml_dump(settings)
    except KeyError:
        settings['channels'][channel] = []
        settings['channels'][channel].append(feed_url)
    return

def _list_rss_feed(bot, channel):
    settings = _import_yaml_data()

    url_list = settings['channels'][channel]
    for x in range(len(url_list)):
        bot.say(channel, "%s: %s" % (x, url_list[x]))
    return

def _del_rss_feed(bot, channel, feed_num):
    settings = _import_yaml_data()
    try:
        feed_num = int(feed_num)
        settings['channels'][channel].remove(settings['channels'][channel][feed_num])
        _yaml_dump(settings)
    except KeyError:
        bot.say(channel, "No RSS feeds in this channel.")
    except ValueError:
        bot.say(channel, "Feed URL not found, please recheck .rss list")
    return


def command_rss(bot, user, channel, args):
    """Usable only by bot mods, rss feed management"""
    args = args.split()
    subcommand = args[0]
    if (isAdmin(user)):
        if (subcommand == "list"):
            _list_rss_feed(bot, channel)
        elif (subcommand == "add"):
            feed_url = args[1]
            _add_rss_feed(bot, channel, feed_url)
        elif (subcommand == "del"):
            feed_num = args[1]
            _del_rss_feed(bot, channel, feed_num)
        return
    else:
        bot.say(channel, "You are not authorized to use this command.")
        return
