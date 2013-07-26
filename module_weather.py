# -*- coding: utf-8 -*-


import urllib2
import json
import yaml
import os


def _import_yaml_data(directory=os.curdir):
    if os.path.exists(directory):
        settings_path = os.path.join(directory, "modules", "weather.settings")
        return yaml.load(file(settings_path))
    else:
        print "Settings file for Weather Underground not set up; please create a Weather Underground API account and modify the example settings file."
        return


def command_weather(bot, user, channel, args):
    """Gives weather for location. Enter a city or zipcode"""

    settings = _import_yaml_data()

    wunderurl = "http://api.wunderground.com/api/%s/conditions/q/%s.json"

    weather_dict = {"Mostly Cloudy":"☁","Clear":"☼","Partly Cloudy":"☁","Light Drizzle":"☂"}

    def is_number(args):
        try:
            int(args)
            return True
        except ValueError:
            return False

    if is_number(args) is True:
        data = urllib2.urlopen(wunderurl % settings["weather"]["key"], args)
    else:
        args = args.split(',')
        if len(args) > 1:
            construct = args[1].replace(' ', '', 1).replace(' ', '_') + "/" + args[0].replace(' ', '_')
            #print wunderurl % construct
            data = urllib2.urlopen(wunderurl % (settings["weather"]["key"], construct))
        else:
            #print wunderurl % args[0]
            data = urllib2.urlopen(wunderurl % (settings["weather"]["key"], args[0]))

    jsondata = json.load(data)

    city = jsondata['current_observation']['display_location']['full']
    temp = jsondata['current_observation']['temperature_string']
    windspeed = jsondata['current_observation']['wind_string']
    feelslike = jsondata['current_observation']['feelslike_string']
    weather = jsondata['current_observation']['weather']
    humidity = jsondata['current_observation']['relative_humidity']

    answer = "Weather for %s: %s, %s feels like %s, %s humidity, wind %s " % (city, weather, temp, feelslike, humidity, windspeed)

    usersplit = user.split('!', 1)[0]
    if channel == user:
        bot.msg(usersplit, answer.encode('utf-8'))
    else:
        bot.msg(channel, answer.encode('utf-8'))
    return
