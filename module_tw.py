"""
Module to emulate Rizon :tw functionality
"""
import json
import os
import base64
import logging

log = logging.getLogger('tw')

try:
    import requests, yaml  
except ImportError as e:
    log.error("Error importing modules: %s" % e.strerror)

def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "twitter.settings")
        return yaml.load(file(settings_path))
    except OSError:
            log.warning("Settings file for Twitter not set up; please create a Twitter API account and modify the example settings file.")
            return


def _handle_tweet(username):
    settings = _import_yaml_data()
    secret_key = settings['twitter']['consumer_secret']
    con_key = settings['twitter']['consumer_key']
    auth_url = "https://api.twitter.com/oauth2/token"
    tweet_url = "https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=%s"

    # Now to deal with all the ridiculous authentication stuff
    base64_key = base64.b64encode(con_key + ":" + secret_key)

    headers_lib = {}
    headers_lib['Authorization'] = "Basic " + base64_key
    headers_lib['Content-Type'] = "application/x-www-form-urlencoded;charset=UTF-8"

    auth_return = requests.post(auth_url, "grant_type=client_credentials", headers=headers_lib)
    auth_dict = json.loads(auth_return.content.encode('utf-8'))

    if auth_dict['token_type'] != "bearer":
        log.error("token_type was not bearer, something went wrong. look into it.")
        return

    #matches for unique tweet id string
    get_url = tweet_url % username
    get_token = "Bearer " + auth_dict['access_token']
    token_headers_lib = {}
    token_headers_lib["Authorization"] = get_token
    twitapi = requests.get(get_url, headers=token_headers_lib)

    #loads into dict
    json1 = json.loads(twitapi.content.encode('utf-8'))

    #reads dict
    ##You can modify the fields below or add any fields you want to the returned string
    try:
        id_num = json1[0]['id']
        text = json1[0]['text']
        user = json1[0]['user']['screen_name']
        name = json1[0]['user']['name']
        time = json1[0]['created_at']
        tweet = "Most recent tweet by \x02%s\x02 (\x02@%s\x02) \x02\x0310|\x03\x02 %s \x02\x0310|\x03\x02 https://twitter.com/%s/status/%s \x02\x0310|\x03\x02 %s" % (name, user, text, user, id_num, time)
    except IndexError:
        tweet = "User not found."
    return tweet


def command_tw(bot, user, channel, args):
    """
    Gets the most recent tweet tweeted by a twitter tweeter
    """
    bot.say(channel, _handle_tweet(args).encode('utf-8'))
    return
