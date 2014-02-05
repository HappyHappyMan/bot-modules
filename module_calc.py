# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import os.path
import urllib
import logging

log = logging.getLogger('calc')

try:
    import requests, yaml  
except ImportError as e:
    log.error("Error importing modules: %s" % e.strerror)

def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "wolframalpha.settings")
        return yaml.load(file(settings_path))
    except OSError:
            log.warning("Settings file for wolframalpha not set up; please create a wolframalpha API account and modify the example settings file.")
            return

def command_wa(bot, user, channel, args):
    """Queries WolframAlpha for the answer to your question."""
    if not args:
        return

    settings = _import_yaml_data()

    api_url = "http://api.wolframalpha.com/v2/query?input=%s&appid=%s"

    retdata = requests.get(api_url % (urllib.quote(args), settings['appid']))
    data = retdata.content.encode('utf-8')
    root = ET.fromstring(data)

    if root[0].tag == "didyoumeans":
        dym_list = []
        if int(root[0].attrib['count']) > 1:
            for x in range(len(root[0])):
                dym_list.append('"' + root[0][x].text.encode('utf-8') + '"')
            dym_str = ", ".join(map(str, dym_list[:-1])) + " or "
        else:
            dym_list = root[0][0].text.encode('utf-8').split(",")
            for x in range(len(dym_list)):
                dym_list[x] = '"' + dym_list[x].strip() + '"'
            dym_str = ", ".join(map(str, dym_list[:-1])) + " or "

        bot.say(channel, user.split('!', 1)[0] + ", did you mean %s%s? If so, try again with that specific query." % (dym_str, dym_list[-1]))
        return

    if root[0].tag == "tips":
        bot.say(channel, user.split('!', 1)[0] + ", " + root[0][0].attrib['text'])

    question = root.findall("*[@id='Input']")[0][0][0].text.encode('utf-8')
    answer = root.findall("*[@primary]")[0][0][0].text.encode('utf-8')

    if len(answer) > 250:
        answer = answer[:250] + "..."

    bot.say(channel, "WolframAlpha | %s = %s" % (question, answer))

def command_calc(bot, user, channel, args):
    return command_wa(bot, user, channel, args)