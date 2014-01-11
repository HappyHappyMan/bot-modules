# -*- encoding: utf-8 -*-


import os
import os.path
import yaml
import json
import random
import requests



def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "google.settings")
        return yaml.load(file(settings_path))
    except OSError:
            print "Settings file for Google not set up; please create a Google API account and modify the example settings file."
            return

def command_kpop(bot, user, channel, args):
    settings = _import_yaml_data()

    playlist_id = "FLlLK27LylBLwFwGjhzKIwJg"

    request_url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId=%s&key=%s" % (playlist_id, settings['google']['yt_key'])
    request_url = request_url.encode('utf-8')

    result = requests.get(request_url)
    print result.status_code

    result_json = json.loads(result.content.encode('utf-8'))

    choice = random.choice(result_json['items'])
    vidId = choice['snippet']['resourceId']['videoId'].encode('utf-8')
    title = choice['snippet']['title'].encode('utf-8')

    bot.say(channel, "http://www.youtube.com/watch?v=%s \x034|\x03 %s" % (vidId, title))
