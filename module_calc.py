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

    api_url = "http://api.wolframalpha.com/v2/query?input={}&appid={}"
    validation_url = "http://api.wolframalpha.com/v2/validatequery?input={}&appid={}"
    parsed_url = urllib.quote(args)

    # if the validation comes back false, we can just send back a response instead
    # of crashing or silently erroring out
    retdata = requests.get(validation_url.format(parsed_url, settings['appid']))
    root = ET.fromstring(retdata.content)
    
    if root.attrib['success'] != "true":
        bot.say(channel, "{}, WolframAlpha is unable to understand your query.".format(bot.factory.getNick(user)))
        return

    retdata = requests.get(api_url.format(parsed_url, settings['appid']))
    data = retdata.content
    root = ET.fromstring(data)

    ## WA returns a bunch of "did you mean" possibilities, this block outputs them 
    ## to the channel.
    if root[0].tag == "didyoumeans": 
        dym_list = []
        ## Do some checking so that we can alter the response for more than one
        ## possibility.
        ## TODO: Tidy up/fix map() output
        if int(root[0].attrib['count']) > 1:
            for x in range(len(root[0])):
                dym_list.append('"' + root[0][x].text.encode('utf-8') + '"')
            dym_str = ", ".join(map(str, dym_list[:-1])) + " or " # trying to be clever about using map(). It doesn't work
        else:
            dym_list = root[0][0].text.encode('utf-8').split(",")
            for x in range(len(dym_list)):
                dym_list[x] = '"' + dym_list[x].strip() + '"'
            dym_str = ", ".join(map(str, dym_list[:-1])) + " or " # trying to be clever about using map(). It doesn't work

        bot.say(channel, bot.factory.getNick(user) + ", did you mean %s%s? If so, try again with that specific query." % (dym_str, dym_list[-1]))
        return

    ## It also likes to return tips sometimes, so we helpfully pass them along to the person who invoked the command.
    if root[0].tag == "tips":
        bot.say(channel, bot.factory.getNick(user) + ", " + root[0][0].attrib['text'])

    ## Search through for the question and answer
    question = root.findall("*[@id='Input']")[0][0][0].text.encode('utf-8')
    answer = root.findall("*[@primary]")[0][0][0].text.encode('utf-8')

    ## truncates response if it's too long so we avoid getting floodkicked.
    if len(answer) > 250:
        answer = answer[:250] + "..."

    bot.say(channel, "\x02WolframAlpha result\x02 \x02\x038|\x03\x02 %s \x02\x038|\x03\x02 %s" % (question, answer))
    return

def command_calc(bot, user, channel, args):
    command_wa(bot, user, channel, args)
    return

