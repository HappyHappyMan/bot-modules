# # -*- coding: utf-8 -*-


import urllib2
import json
import yaml
import urllib
import os
import sqlite3


def _import_yaml_data(directory=os.curdir):
    try:
        settings_path = os.path.join(directory, "modules", "weather.settings")
        return yaml.load(file(settings_path))
    except OSError:
            print "Settings file for Weather Underground not set up; please create a Weather Underground API account and modify the example settings file."
            return

def _get_latlng(city):
    city = urllib.quote(city)
    latlng_data = json.load(urllib2.urlopen("https://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false" % city))
    lat = latlng_data['results'][0]['geometry']['location']['lat']
    lng = latlng_data['results'][0]['geometry']['location']['lng']
    name = latlng_data['results'][0]['formatted_address']
    return (str(lat) + "," + str(lng), name)

def _get_saved_data(nick, conn):
    DB = sqlite3.connect(conn)
    c = DB.cursor()
    userdata = ""

    result = c.execute("SELECT temp_type,location FROM weather WHERE nick LIKE ?", (nick,))

    userdata = result.fetchone()

    try:
        len(userdata)
        return userdata, True
    except TypeError:
        return userdata, False

def _set_saved_data(nick, location, conn, temp_type):
    """Have them specify a temp_type no matter what in the bot code, it's too much hassle trying to predict it when updating."""
    DB = sqlite3.connect(conn)
    c = DB.cursor()

    testresult = c.execute("SELECT temp_type FROM weather WHERE nick LIKE ?", (nick,))

    try:
        db_temp_type = testresult.fetchone()[0]
        worked = True
    except TypeError:
        worked = False

    if worked is True:
        vartuple = (temp_type, nick, location)
        ## DEBUG ##
        print vartuple
        ## END DEBUG ##
        try:
            c.execute("UPDATE weather SET temp_type=(?), location=(?) WHERE nick=(?)", (vartuple[0],vartuple[2],vartuple[1]))
        except sqlite3.Error as e:
            print e.args[0]

        DB.commit()
        c.close()
        DB.close()

        return
    else:
        vartuple = (temp_type, nick, location)
        ## DEBUG ##
        print vartuple
        ## END DEBUG ##
        try:
            c.execute("INSERT INTO weather VALUES (?, ?, ?)", vartuple)
        except sqlite3.Error as e:
            print e.args[0]

        DB.commit()
        c.close()
        DB.close()

        return

def command_weather(bot, user, channel, args):
    """Gives weather for location. Enter a city or zip code"""

    settings = _import_yaml_data()
    measure_type = 0

    API_URL = "https://api.forecast.io/forecast/%s/%s"

    if args:
        args = args.split(":")
        latlng = _get_latlng(args[0])
        units = ""

        if len(args) > 1:
            if args[1] == "si":
                units = "?units=si"
                measure_type = 1
            elif args[1] == "ca":
                units = "?units=ca"
                measure_type = 2
            elif args[1] == "uk":
                units = "?units=uk"
                measure_type = 3

        print latlng
        print type(latlng)
        url = API_URL % (settings["weather"]["key"], latlng[0]) + units
        print url

        data = urllib2.urlopen(url)
    else:
        nick = user.split('!', 1)[0]
        db_data, success = _get_saved_data(nick.lower(), settings['weather']['db'])
        print success
        if success is True:
            units = ""
            latlng = _get_latlng(db_data[1])
            measure_type = db_data[0]
            if measure_type == 1:
                units = "?units=si"
            elif measure_type == 2:
                units = "?units=ca"
            elif measure_type == 3:
                units = "?units=uk"
            data = urllib2.urlopen(API_URL % (settings["weather"]["key"], latlng[0]) + units)
        else:
            bot.say(channel, "You're not in the database! Set a location with .wadd.")
            return

    weather_data = json.load(data)

    print weather_data["currently"].keys()

    city_name = latlng[1]
    temperature = str(weather_data['currently']['temperature'])
    feels_like = str(weather_data['currently']['apparentTemperature'])
    summary = weather_data['currently']['summary']
    humidity = str(weather_data['currently']['humidity'] * 100) + "%"
    wind_direction = weather_data['currently']['windBearing']
    precipProb = str(weather_data['currently']['precipProbability'] * 100) + "%"
    wind_speed = str(weather_data['currently']['windSpeed'])

    temp_suffix = [u"°F", u"°C", u"°C", u"°C"]
    wind_suffix = ["mph","m/s","kph","mph"]

    weather_string = "Weather for \x02%s\x02 \x02\x033|\x03\x02 %s, %s%s feels like %s%s, %s humidity, wind %s %s, %s chance of precipitation" % (city_name, summary, temperature, temp_suffix[measure_type], feels_like, temp_suffix[measure_type], humidity, wind_speed, wind_suffix[measure_type], precipProb)

    bot.say(channel, weather_string.encode('utf-8'))

    return

def command_wadd(bot, user, channel, args):
    """Sets your location. Usage: .wadd location:units, where units can be any one of us, si, ca, uk. Defaults to us if no unit is specified."""

    settings = _import_yaml_data()

    args = args.split(":")
    print args
    nick = user.split('!', 1)[0]
    try:
        if args[1] == "us":
            args[1] = 0
        elif args[1] == "si":
            args[1] = 1
        elif args[1] == "ca":
            args[1] = 2
        elif args[1] == "uk":
            args[1] = 3
    except IndexError:
        args.append(0)

    print nick
    print args[0]
    print settings["weather"]["key"]
    print args[1]

    _set_saved_data(nick.lower(), args[0], settings['weather']['db'], args[1])

    bot.say(nick, "Location set!")

def command_w(bot, user, channel, args):
    return command_weather(bot, user, channel, args)