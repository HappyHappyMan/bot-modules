# -*- coding: utf-8 -*-

"""
$Id: module_weather.py 313 2011-06-03 11:22:38Z henri@nerv.fi $
$HeadURL: http://pyfibot.googlecode.com/svn/trunk/modules/module_weather.py $
"""
import urllib2
import json


def command_weather(bot, user, channel, args):
    """Gives weather for location. Enter a city or zipcode"""
    wunderurl = "http://api.wunderground.com/api/551a8409f5038f1b/conditions/q/%s.json"

    weather_dict = {"Mostly Cloudy":"☁","Clear":"☼","Partly Cloudy":"☁","Light Drizzle":"☂"}

    def is_number(args):
        try:
            int(args)
            return True
        except ValueError:
            return False

    if is_number(args) is True:
        data = urllib2.urlopen(wunderurl % args)
    else:
        args = args.split(',')
        if len(args) > 1:
            construct = args[1].replace(' ', '', 1).replace(' ', '_') + "/" + args[0].replace(' ', '_')
            print wunderurl % construct
            data = urllib2.urlopen(wunderurl % construct)
        else:
            print wunderurl % args[0]
            data = urllib2.urlopen(wunderurl % args[0])

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
