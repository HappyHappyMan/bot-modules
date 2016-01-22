# -*- coding: utf-8 -*-

import logging
import json
import os
import time

log = logging.getLogger('github')

try:
    import requests
    import yaml
except ImportError as e:
    log.error("Error importing modules: %s" % e.strerror) 

def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "github.settings")
        return yaml.load(file(settings_path))
    except OSError:
        log.warning(
                "Settings file for Github not set up; please create a Github API account and modify the example settings file.")
    return

def _create_github_issue(bot, user, channel, args, is_feature_req):
    settings = _import_yaml_data()
    args = args.split(':')
    title = args[0].strip()
    body = args[1].strip()
    tag = ['feature-request'] if is_feature_req else ['bug-report']

    # add additional information to the body
    body = "{} <{}> ({}) {}:\n\n".format(
            "Feature request from" if is_feature_req else "Issue reported by",
            bot.factory.getNick(user), user, 
            "in channel {}".format(channel) if channel.startswith('#') else 'via PM' ) + body

    data = {'title': title, 'body': body, 'labels': tag}
    dump = json.dumps(data)
    r = requests.post('https://api.github.com/repos/sriramanujam/bot-modules/issues',
            auth=('sriramanujam', settings['token']), data=dump)
    if r.status_code == requests.codes.created:
        # success
        ret = json.loads(r.content)
        url = ret['html_url']
        return "{}: Github issue created! View it at {}".format(bot.factory.getNick(user), url)
    else:
        log.error(json.loads(r.content))
        return "Github issue creation failed with status code {} at {}. Please pass this information along to my owner.".format(
                r.status_code, time.strftime("%Y-%m-%d %H:%M:%S GMT %z"))

def command_featurerequest(bot, user, channel, args):
    """Use this command to submit feature requests. Usage .featurerequest <title> : <body> Ex.: `.featurerequest Short description of feature : Detailed description of feature, including potential use cases, reason you want it, etc. Basically try to sell me on it.` Caveats: I don't think you can use Markdown, nor will you be able to edit the issue once it's created. If you have a Github account, you can add supplemental information in a comment on the issue if you like."""
    retstr = _create_github_issue(bot, user, channel, args, True)
    # retstr is assumed to be encoded as unicode here
    bot.say(channel, retstr)
    return

def command_bugreport(bot, user, channel, args):
    """Use this command to file bug reports. Usage: .bugreport <title> : <body> Ex.: `.bugreport Short description of bug : Detailed description of the bug, including steps to reproduce it, etc.` Caveats: I don't think you can use Markdown, nor will you be able to edit the bug report once you make it. If you have a Github account, you can add supplemental information in a comment on the issue if you like."""
    retstr = _create_github_issue(bot, user, channel, args, False)
    # retstr is assumed to be encoded as unicode here
    bot.say(channel, retstr)
    return

def command_changelog(bot, user, channel, args):
    """Gets you changelog information on the bot and its modules. Usage: .changelog <number> gets you that number recent changelog. Ex: .changelog 3 returns the third-most recent change. Without arguments, .changelog returns the most recent change."""

    log.debug(args)
    log.debug(type(args))
    try:
        args = int(args) - 1
        log.debug("We have found an int! It is " + str(args))
    except ValueError:
        log.debug("There are no args!")
        args = 0

    r = requests.get("https://api.github.com/repos/SriRamanujam/bot-modules/commits")
    j = json.loads(r.content.encode('utf-8'))


    if args > 29:
        args = 0

    message = j[args]['commit']['message'].encode("utf-8")
    bot.say(channel, "Changelog %s: %s" % (str(args + 1), message))


