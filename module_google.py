# -*- coding: utf-8 -*-

import json
import urllib
import HTMLParser
import os
import logging
import random

log = logging.getLogger('google')

try:
    import requests, yaml
except ImportError as e:
    log.error("Error importing modules: %s" % e.strerror)

GOOGLE_URL = "https://www.googleapis.com/customsearch/v1?key=%s&cx=%s&q=%s"
SHORTENER_URL = "https://www.googleapis.com/urlshortener/v1/url?key=%s&cx=%s"
GOOGLE_BASE_URL = "www.google.com/search?q=%s"


def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "google.settings")
        return yaml.load(file(settings_path))
    except OSError:
            log.warning("Settings file for Google not set up; please create a Google API account and modify the example settings file.")
            return

class GoogleError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def _googling(args, is_google):
    settings = _import_yaml_data()
    args = args.decode('utf-8')
    request = requests.get(GOOGLE_URL % (settings['google']['key'], settings['google']['cx'], urllib.quote(args.encode('utf-8', 'ignore'))))
    json1 = json.loads(request.content)
    result = {}
    try:
        result["url"] = urllib.unquote(json1['items'][0]['link'].encode('utf-8'))
        result["name"] = HTMLParser.HTMLParser().unescape(json1['items'][0]['title'].encode('utf-8'))
        if is_google:
            result["snippet"] = json1['items'][0]['snippet'].encode('utf-8')
            payload = {"longUrl": GOOGLE_BASE_URL % args.encode('utf-8')}
            shortReq = requests.post(SHORTENER_URL % (settings['google']['key'], settings['google']['cx']), data=json.dumps(payload), headers={'Content-Type': 'application/json'})
            shortData = json.loads(shortReq.content)
            result["shortURL"] = shortData['id'].encode('utf-8')

        return result
    except KeyError:
        raise GoogleError('No results found')

def command_yt(bot, user, channel, args):
    """Searches youtube for your search. What else would it do?"""
    settings = _import_yaml_data()
    gdata_url = "https://www.googleapis.com/youtube/v3/search"

    args = args.decode('utf-8')

    params = {'part': 'snippet',
                'q': args,
                'key': settings['google']['key'],
                'safesearch': 'none'}

    r = requests.get(gdata_url, params=params)
    if not r.status_code == 200:
        error = r.json().get('error')
        if error:
            error = '{}: {}'.format(error['code'], error['message'])
        else:
            error = r.status_code
        log.warning('Youtube API error: {}'.format(error))
        return

    items = r.json()['items']
    if len(items) == 0:
        bot.say(channel, "No results found.")
        return

    entry = items[0]

    title = entry['snippet']['title'].encode('utf-8')
    id = entry['id']['videoId']

    bot.say(channel, '\x02YouTube search result\x02 \x034|\x03 {} \x034|\x03 https://youtube.com/watch?v={}'.format(
        title, id))


def command_gis(bot, user, channel, args):
    settings = _import_yaml_data()
    args = args.decode('utf-8')

    request_url = GOOGLE_URL % (settings['google']['key'], settings['google']['cx'], urllib.quote(args.encode('utf-8', 'ignore')))
    request_url += '&searchType=image&fields=items(link)'

    response = json.loads(requests.get(request_url).content)

    if ('items' in response.keys() and len(response['items']) > 0):
        bot.say(channel, response['items'][0]['link'].encode('utf-8'))
    else:
        bot.say(channel, "No results found.")

def command_animate(bot, user, channel, args):
    """Finds a gif for your query."""
    settings = _import_yaml_data()
    args = args.decode('utf-8')

    if args[:3] == "me ":
        args = args[3:]

    request_url = GOOGLE_URL % (settings['google']['key'], settings['google']['cx'], urllib.quote(args.encode('utf-8', 'ignore')))
    request_url = request_url + '&searchType=image&fileType=gif&hq=animate&fields=items(link)'

    response = json.loads(requests.get(request_url).content)

    if ('items' in response.keys() and len(response['items'])) > 0:
        bot.say(channel, random.choice(response['items'])['link'].encode('utf-8'))
    else:
        bot.say(channel, "No results found.")

def command_google(bot, user, channel, args):
    usersplit = user.split('!', 1)[0]
    try:
        result_dict = _googling(args, True)
    except GoogleError:
        bot.say(channel, "No results found.")
        return

    str_len = 300
    text_len = 41 + sum([len(result_dict[item]) for item in result_dict])
    if text_len > str_len:
        result_dict['snippet'] = result_dict['snippet'][:-(text_len - str_len)]
        trunclen = len(result_dict['snippet']) - 1
        while True:
            if result_dict['snippet'][trunclen] == " ":
                break
            else:
                trunclen = trunclen - 1
                continue
        result_dict['snippet'] = result_dict['snippet'][:trunclen] + "..."

    if channel == user:
        channel = usersplit

    bot.say(channel, "%s \x02\x0312|\x03\x02 %s \x02\x0312|\x03\x02 %s \x02\x0312|\x03\x02 More results: %s" % (result_dict['name'], result_dict['snippet'], result_dict['url'], result_dict['shortURL']))
    return


def command_g(bot, user, channel, args):
    command_google(bot, user, channel, args)
    return


def command_lucky(bot, user, channel, args):
    usersplit = user.split('!', 1)[0]
    try:
        result_dict = _googling(args, False)
    except GoogleError:
        bot.say("No results found.")
        return

    if channel == user:
        channel = usersplit

    bot.say(channel, "%s \x02\x0312|\x03\x02 %s" % (result_dict['name'], result_dict['url']))
    return

def command_l(bot, user, channel, args):
    command_lucky(bot, user, channel, args)
    return
