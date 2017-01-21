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


def get_reddit_api(data, kind, time=None):
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

        if time:
            if time == "all":
                time_period = " of all time"
            else:
                time_period = " in the past %s" % (time)
        else:
            time_period = ""
        result = "\x02Top post in r/%s%s\x02 \x037\x02|\x02\x03 %s by \x02%s\x02 %s %s" % (subreddit, time_period, title, author, url, link)

        if over_18 is True:
            result = result + " \x037\x02|\x02\x03 \x02NSFW\x02"
    return result

def _reddit_api_user(data):
    data = json.loads(data)

    if data['kind'] == "t2":
        return _parse_t2(data)
    elif data['kind'] == 'Listing':
        return _parse_listing(data)
    else:
        return ""

def _parse_t2(data):
    data = data['data']
    name = data['name']
    comment_karma = data['comment_karma']
    link_karma = data['link_karma']

    return "%s | %s link karma, %s comment karma | http://reddit.com/u/%s" % (name, link_karma, comment_karma, name)

def _parse_listing(data):
    data = data['data']['children'][0]



def command_user(bot, user, channel, args):
    """Looks up reddit users and displays their information if available."""
    headers = {'User-Agent': 'Lazybot/Claire by /u/Happy_Man'}

    args = args.split(":", 1)

    try:
        if args[1] in ['comments', 'submitted']:
            request_url = "http://www.reddit.com/user/%s/%s/.json" % (args[0], args[1])
            if args[2] in ['hour', 'day', 'week', 'month', 'year', 'all']:
                request_url = "http://www.reddit.com/user/%s/%s/.json?t=%s&sort=top&limit=1&raw_json=1" % (args[0], args[1], args[2])
        else:
            request_url = "http://www.reddit.com/user/%s/about.json" % (args[0])
    except IndexError:
        request_url = "http://www.reddit.com/user/%s/about.json" % (args[0])

    data = requests.get(request_url, headers=headers)

    if data.status_code != 200:
        bot.say(channel, "User information unavailable.")
        return

    parsed_data = _reddit_api_user(data.content)

    bot.say(channel, parsed_data.encode('utf-8'))


def command_reddit(bot, user, channel, args):
    """Give it a subreddit, it will give you the current top post in that subreddit. If you give it an argument, for example .reddit funny:{hour, day, week, month, year, all} it will give you the top post in the subreddit in that time period."""

    headers = {'User-Agent': 'Lazybot/Claire by /u/Happy_Man'}

    args = args.split(":", 1)

    try:
        if args[1] in ["hour", "day", "week", "month", "year", "all"]:
            request_url = "http://www.reddit.com/r/%s/top/.json?t=%s&raw_json=1" % (args[0], args[1])
            time_flag = True
        else:
            request_url = "http://www.reddit.com/r/%s/.json?raw_json=1" % (args[0])
            time_flag = False
    except IndexError:
        request_url = "http://www.reddit.com/r/%s/.json?raw_json=1" % (args[0])
        time_flag = False

    data = requests.get(request_url, headers=headers)

    if data.status_code == 403:
        bot.say(channel, "This subreddit is private. Sorry, I can't get in.")
        return
    if data.status_code == 429:
        log.info("Reddit returned 429, we're being rate-limited for some reason.")
        return

    try:
        data = json.loads(data.content.encode('utf-8'))
    except ValueError:
        bot.say(channel, "This subreddit or user doesn't exist, sorry.")
        return

    try:
        posts = data['data']['children']
        if len(posts) < 1:
            bot.say(channel, "This subreddit doesn't exist, sorry.")
            return
        for post in posts:
            if post['data']['stickied'] is not True:
                topPost = post['data']
                break
    except IndexError:
        # I have to duplicate myself because apparently the json module
        # doesn't even know when json is or isn't valid html. 
        #
        # ???
        bot.say(channel, "This subreddit doesn't exist, sorry.")
        return
    if time_flag:
        returnstr = get_reddit_api(topPost, "t3", args[1])
    else:
        returnstr = get_reddit_api(topPost, "t3")

    bot.say(channel, returnstr.encode('utf-8'))
    return

def command_r(bot, user, channel, args):
    return command_reddit(bot, user, channel, args)
