# -*- coding: utf-8 -*-

"""
RSS rotator, improved version.

Only works with Reddit feeds now, but that's okay, since
nobody needs RSS feeds of anything else.

Key data structures:

timestamp_dict: dict(str -> dict(str -> float))
                dict(channel name -> dict(full json url -> timestamp))

result_dict:    dict(str -> list(str))
                dict(channel name -> list(formatted strings for output))
"""

import threading
import time
import calendar
import os
import json
import HTMLParser
import logging
import logging.handlers

log = logging.getLogger('rss') 
log.setLevel(20)

## DO NOT use urllib2 with this module! urllib2 is very VERY bad about thread
## safety, you WILL run into at least two kinds of stupid race condition-based
## bugs if you use it! Besides, requests is better than urllib2 in most cases
## so you should be using it anyway. 
try:
    import requests
    from twisted.internet import task
    import yaml
    init_ok = True
except ImportError as e:
    log.warning("Error starting rss module: %s" % e.strerror)
    init_ok = False


### Globals, sigh...###
lock = threading.Lock()
timestamp_dict = {}
client = None

def event_signedon(bot):
    """Starts rotator, triggered when bot signs on to network"""

    global timestamp_dict
    global client
    settings = _import_yaml_data()
    ## This has less accuracy than converting datetime() objects, but since
    ## Reddit doesn't deal with timestamps that accurate, we can get away with it.
    current_time = calendar.timegm(time.gmtime())
    
    timestamp_dict = {}

    client = requests.session()
    headers = {'User-Agent':"Lazybot/Claire by Happy_Man"}
    username = settings['reddit']['username']
    password = settings['reddit']['password']
    dataDict = {'user':username, 'passwd':password, 'api_type':'json'}

    client.headers = headers
    
    auth = client.post('https://ssl.reddit.com/api/login', data=dataDict)
    try:
        authJson = json.loads(auth.content)
        client.headers['X-Modhash'] = authJson['json']['data']['modhash']
    except KeyError:
        log.error("Reddit login unsuccessful, stopping rotator. Please check manually.")
        return


    ## settings['channels'].keys() is every channel we have json links for, ie,
    ## every channel that has requested to have a new posts feed. We initialize 
    ## timestamp_dict[channel] to a second dict, keyed by every url that channel has
    ## requested. Keeping the channel and url as keys to dicts makes life easier
    ## in process_rss(). We then set every url's value to be current_time. 
    for channel in settings['channels'].keys(): # Initialize timestamps to current time
        timestamp_dict[channel] = {}
        for url in settings['channels'][channel]:
            timestamp_dict[channel][url] = current_time

    delay = settings['delay'] # This should be no less than 120, because reddit caches returns for two minutes.
    l = task.LoopingCall(process_rss, bot) 
    l.start(delay)

def get_reddit_api(data, kind):
    """Extracts relevant strings from data, and formats for output. Returns formatted
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
        author = data['author']
        subreddit = data['subreddit']
        short = "http://redd.it/" + data['name'][3:] # This skips the t3_ part of the name, and gets us only the ID for the shortlink
        link = "\x037\x02|\x02\x03 " + short
        over_18 = data['over_18']
        result = "\x02r/%s/new\x02 \x037\x02|\x02\x03 %s by \x02%s\x02 %s" % (subreddit, title, author, link)
        if over_18 is True:
            result = result + " \x037\x02|\x02\x03 \x02NSFW\x02"
    return result

def process_rss(bot):
    log.debug("RSS processing started")

    global timestamp_dict
    global client

    ## Initialize dicts and headers for later on. 
    settings = _import_yaml_data()
    chans = settings['channels']
    result_dict = {}
    
    for channel in chans.keys():
        result_dict[channel] = []

        log.debug(result_dict)

        ## This loop handles initializing a newly added feed's timestamp, by copying
        ## what's done in event_signedon(). 
        for url in chans[channel]:
            try:
                timestamp_dict[channel][url]
            except KeyError:
                timestamp_dict[channel][url] = calendar.timegm(time.gmtime())

            log.debug(timestamp_dict)
            ## For some reason, reddit is sometimes really bad about returning json 
            ## on time. This try block attempts to account for that, because otherwise
            ## the thread hard-crashes and stops looping. Remember to always put a break
            ## in every except, otherwise execution will continue and json.loads() will
            ## try to extract json from nothing!
            try:
                feed = client.get(url, timeout=15)
            except requests.exceptions.Timeout:
                log.error(url + " timed out. Aborting.")
                break
            except requests.exceptions.ConnectionError:
                log.error(url + " was retried too many times. Aborting.")
                break

            ## In keeping with the "reddit is bad at providing an API" thing, non-200
            ## status codes don't result in an error, but all the same, it messes with
            ## assumptions made by the processing block below. So we check for 200 here,
            ## and abort if anything other than a 200 comes through. 
            if (feed.status_code != 200):
                log.error(url + " returned " + str(feed.status_code) + " error. Aborting.")
                break
            
            ## This try may not need to be here, but it's there just in case something 
            ## goes wrong in the GET request and isn't dealt with properly.
            try:
                feed_data = json.loads(feed.content.encode('utf-8'))

                latest_timestamp = 0.0

                ## The actual json processing takes place within two for loops. The first
                ## updates latest_timestamp, a temporary value initialized for every url
                ## that holds the latest entry. This is because sometimes reddit doesn't
                ## return json in properly descending order, so making the assumption
                ## "Oh, I can just automatically save the first entry's timestamp because
                ## it will be the most recent" causes repeat entries to be output on occasion. 
                ## Like, ten or fifteen repeats. So this loop just goes through and ensures
                ## that latest_timestamp is actually the latest timestamp, by manually comparing
                ## every single one. Make no assumptions about the validity of your data!
                for entry in feed_data['data']['children']:
                    log.debug("timestamp_dict timestamp is " + str(timestamp_dict[channel][url]))
                    log.debug("latest_timestamp timestamp is " + str(latest_timestamp))
                    log.debug("Entry timestamp is " + str(entry['data']['created_utc']))

                    if (latest_timestamp < entry['data']['created_utc']):
                        log.debug("We are updating the timestamp in latest_timestamp to " + str(entry['data']['created_utc']))
                        latest_timestamp = entry['data']['created_utc']
                        log.debug("latest_timestamp is now " + str(latest_timestamp))


                ## The second for loop actually handles checking for new items. We 
                ## compare against the last iteration's timestamp, saved in the dict,
                ## and parse any new entries with get_reddit_api(), which formats the
                ## output string (result_str) and returns it. We then take that string 
                ## and put it into result_dict[channel] for a third for loop to process.
                for entry in feed_data['data']['children']:
                    log.debug("Comparing entries. entry timestamp is " + str(entry['data']['created_utc']) + ". timestamp_dict timestamp is " + str(timestamp_dict[channel][url]))
                    if (entry['data']['created_utc'] > timestamp_dict[channel][url]): # This will compare against the last iteration's timestamp
                        log.debug("New item. Timestamp: " + str(entry['data']['created_utc']) + " saved timestamp: " + str(timestamp_dict[channel][url]))
                        result_str = get_reddit_api(entry['data'], entry['kind'])
                        result_dict[channel].append(result_str)

                ## In a perfect world, latest_timestamp should always be greater than 
                ## or equal to the stored value in timestamp_dict. Because reddit is 
                ## absolute shit at providing API services, it sometimes returns entries
                ## from 300k seconds ago, or about three and a half days. Here we check
                ## for that, because it messes with assumptions in the locked code.
                if timestamp_dict[channel][url] <= latest_timestamp:
                        ## This lock is here because writing to a dict is non-atomic, and it's
                        ## better to be safe than sorry with threaded code like this. 
                        with lock:
                            log.debug("Lock acquired")
                            log.debug("Now setting timestamp in timestamp_dict to be " + str(latest_timestamp) + " for url " + url + " in channel " + channel) 
                            timestamp_dict[channel][url] = latest_timestamp
                else:
                    log.warning("Outdated return. Latest timestamp is " + str(latest_timestamp) + ". Stored timestamp is " + str(timestamp_dict[channel][url]) + ".")
            except ValueError:
                pass
    ## This is the output loop. For every channel's output list in result_dict, we 
    ## iterate through and have the bot say() to the appropriate channel. 
    ## TODO: figure out some way to stagger output, apparently sleep() doesn't work as
    ## well as hoped.
    for channel in result_dict:
        log.info(str(len(result_dict[channel])) + " results in " + channel)
        if len(result_dict[channel]) > 0:
            for x in range(len(result_dict[channel])):
                bot.say(channel, result_dict[channel][x].encode('utf-8'))
    return


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

def _yaml_dump(settings_file, directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "rss.settings")
        stream = file(settings_path, 'w')
        yaml.dump(settings_file, stream)
    except OSError:
        log.error("Settings file for rss not set up; please create an empty rss.settings file.")
    return

def _restart_rss_feed(bot):
    """
    This restarts the rss feed manually after an unforeseen crash. Not implemented yet.
    """
    pass

def _add_rss_feed(bot, channel, feed_url):
    """
    Adds RSS feeds to the database. We try to add the url to an already-existing
    channel, and, if that channel doesn't exist, we create it and then add the url 
    to it. Then we dump the updated dict using _yaml_dump().
    """
    settings = _import_yaml_data()
    try:
        settings['channels'][channel].append(feed_url)
        _yaml_dump(settings)
    except KeyError:
        settings['channels'][channel] = []
        settings['channels'][channel].append(feed_url)
        _yaml_dump(settings)
    return

def _list_rss_feed(bot, channel):
    """
    A simple for loop to iterate over that channel's urls and output them.
    """
    settings = _import_yaml_data()

    url_list = settings['channels'][channel]
    for x in range(len(url_list)):
        bot.say(channel, "%s: %s" % (x, url_list[x]))
    return

def _del_rss_feed(bot, channel, feed_num):
    """
    Settings['channels'][channel] is a list, so we use list.remove() to remove 
    the specified entry. We also have a couple error messages just in case somebody
    tries to do something illegal.
    """
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
    """Usable only by bot mods, json feed management"""
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
        elif (subcommand == "restart"):
            _restart_rss_feed(bot)
        return
    else:
        bot.say(channel, "You are not authorized to use this command.")
        return
