"""
Module to emulate Rizon :tw functionality
"""
import json
import urllib2
import yaml
import os
import base64


def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "twitter.settings")
        return yaml.load(file(settings_path))
    except OSError:
            print "Settings file for Twitter not set up; please create a Twitter API account and modify the example settings file."
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

    auth_request = urllib2.Request(auth_url, "grant_type=client_credentials", headers_lib)
    auth_return = urllib2.urlopen(auth_request)
    auth_dict = json.load(auth_return)

    if auth_dict['token_type'] != "bearer":
        return

    #matches for unique tweet id string
    get_url = tweet_url % username
    get_token = "Bearer " + auth_dict['access_token']
    get_request = urllib2.Request(get_url)
    get_request.add_header("Authorization", get_token)
    twitapi = urllib2.urlopen(get_request)

    #loads into dict
    json1 = json.load(twitapi)

    #reads dict
    ##You can modify the fields below or add any fields you want to the returned string
    try:
        if json1['error']:
            tweet = "User not found"
    except TypeError:
        text = json1[0]['text']
        user = json1[0]['user']['screen_name']
        name = json1[0]['user']['name']
        tweet = "Most recent tweet by %s(@%s): %s" % (name, user, text)
    return tweet


def command_tw(bot, user, channel, args):
    """ All we're doing here, is taking .tw and running it out such that we can do things properly with it
    """
    bot.say(channel, _handle_tweet(args).encode('utf-8'))
