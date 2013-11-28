# -*- coding: utf-8 -*-

import json
import urllib2
import urllib
import HTMLParser
import os
import yaml

GOOGLE_URL = "https://www.googleapis.com/customsearch/v1?key=%s&q=%s"
SHORTENER_URL = "http://v.gd/create.php?format=json&url=%s"
GOOGLE_BASE_URL = "http://www.google.com/#output=search&q=%s"


def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "google.settings")
        return yaml.load(file(settings_path))
    except OSError:
            print "Settings file for Google not set up; please create a Google API account and modify the example settings file."
            return


def _googling(args):
    settings = _import_yaml_data()
    args = args.decode('utf-8')
    json1 = json.load(urllib2.urlopen(GOOGLE_URL % (settings['google']['key'], urllib.quote(args.encode('utf-8', 'ignore')))))
    result = {}
    result["url"] = urllib.unquote(json1['items'][0]['link'].encode('utf-8'))
    result["name"] = HTMLParser.HTMLParser().unescape(json1['items'][0]['title'].encode('utf-8'))
    result["snippet"] = json1['items'][0]['snippet'].encode('utf-8')
    shortReq = urllib2.urlopen(SHORTENER_URL % urllib.quote(GOOGLE_BASE_URL % args.encode('utf-8')))
    shortData = json.load(shortReq)
    print shortData.keys()
    result["shortURL"] = shortData['shorturl'].encode('utf-8')

    return result


def command_google(bot, user, channel, args):
    usersplit = user.split('!', 1)[0]
    result_dict = _googling(args)

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


def command_lucky(bot, user, channel, args):
    usersplit = user.split('!', 1)[0]
    result_dict = _googling(args)

    if channel == user:
        channel = usersplit

    bot.say(channel, "%s \x02\x0312|\x03\x02 %s" % (result_dict['name'], result_dict['url']))


def command_l(bot, user, channel, args):
    command_lucky(bot, user, channel, args)
