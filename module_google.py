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
GOOGLE_KG_URL = "https://kgsearch.googleapis.com/v1/entities:search?query=%s&key=%s&limit=1&indent=True"

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

def _get_shorturl(args):
    settings = _import_yaml_data()
    payload = {"longUrl": GOOGLE_BASE_URL % args.encode('utf-8')}
    shortReq = requests.post(SHORTENER_URL % (settings['google']['key'], settings['google']['cx']), data=json.dumps(payload), headers={'Content-Type': 'application/json'})
    shortData = json.loads(shortReq.content)
    return shortData['id'].encode('utf-8')


def _kgsearch(args):
    settings = _import_yaml_data()
    args = args.decode('utf-8')
    request = requests.get(GOOGLE_KG_URL % (args, settings['google']['key']))
    j = request.json()
    if len(j['itemListElement']) > 0:
        item = j['itemListElement'][0]['result']
        name = item['name']
        blurb = item['detailedDescription']['articleBody']
        blurb_src = item['detailedDescription']['url']
        if 'url' in item.keys():
            item_url = item['url']
        else:
            item_url = ""
        shorturl = _get_shorturl(args)

        resultstr = "\x02Google search result for {}\x02 \x02\x0312|\x03\x02 {} · {} \x02\x0312|\x03\x02 {} \x02\x0312\x03\x02 More results: {}".format(name, blurb, blurb_src, item_url, shorturl)
        return resultstr.decode('utf-8').encode('utf-8')
    else:
        return False

def _googling(args, is_google):
    settings = _import_yaml_data()
    args = args.decode('utf-8')
    request = requests.get(GOOGLE_URL % (settings['google']['key'], settings['google']['cx'], urllib.quote(args.encode('utf-8', 'ignore'))))
    json1 = json.loads(request.content)
    result = {}
    try:
        result["url"] = urllib.unquote(json1['items'][0]['link'].encode('utf-8'))
        result["name"] = HTMLParser.HTMLParser().unescape(json1['items'][0]['title'].encode('utf-8'))
    except KeyError:
        raise GoogleError("No results found")

    if is_google:
        result["snippet"] = json1['items'][0]['snippet'].encode('utf-8')
        result["shortURL"] = _get_shorturl(args)

        str_len = 300
        text_len = 41 + sum([len(result[item]) for item in result])
        if text_len > str_len:
            result['snippet'] = result['snippet'][:-(text_len - str_len)]
            trunclen = len(result['snippet']) - 1
            while True:
                if result['snippet'][trunclen] == " ":
                    break
                else:
                    trunclen = trunclen - 1
                    continue
            result['snippet'] = result['snippet'][:trunclen] + "..."
        
        resultstr = "\x02Google search result for {}\x02 \x02\x0312|\x03\x02 {} · {} \x02\x0312|\x03\x02 {} \x02\x0312|\x02\x03 More results: {}".format(
                args, result['name'], result['snippet'], result['url'], result['shortURL'])
        return resultstr

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
        result = _kgsearch(args)
        if result == False:
            result = _googling(args, True)
    except GoogleError:
        bot.say(channel, "No results found.")
        return

    bot.say(channel, result)
    return

def command_g(bot, user, channel, args):
    return command_google(bot, user, channel, args)

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
    return command_lucky(bot, user, channel, args)

