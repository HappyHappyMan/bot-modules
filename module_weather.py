# # -*- coding: utf-8 -*-


import urllib2
import json
import yaml
import urllib
import os
import sqlite3
import datetime


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

    result = c.execute("SELECT temp_type,location,forecast_type FROM weather WHERE nick LIKE ?", (nick,))

    userdata = result.fetchone()

    try:
        len(userdata)
        return userdata, True
    except TypeError:
        return userdata, False

def _set_saved_data(nick, location, conn, temp_type, forecast_type):
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
        vartuple = (temp_type, nick, location, forecast_type)

        try:
            c.execute("UPDATE weather SET temp_type=(?), location=(?), forecast_type=(?) WHERE nick=(?)", (vartuple[0],vartuple[2],vartuple[3],vartuple[1]))
        except sqlite3.Error as e:
            print e.args[0]

        DB.commit()
        c.close()
        DB.close()

        return
    else:
        vartuple = (temp_type, nick, location, forecast_type)

        try:
            c.execute("INSERT INTO weather VALUES (?, ?, ?, ?)", vartuple)
        except sqlite3.Error as e:
            print e.args[0]

        DB.commit()
        c.close()
        DB.close()

        return

def _parse_forecast_output(weather_data, city_name, measure_type):

    temp_suffix = [u"°F", u"°C", u"°C", u"°C"]
    icons = {'clear-day':u'☀ ', 'clear-night':u'☾ ', 'rain':u'☂ ', 'snow':u'☃ ', 'fog':u'🌁 ', 'cloudy':u'☁ ', 'partly-cloudy-day':u'⛅ '}

    forecast_list = []

    for x in range(3):
        try:
            icon = icons[weather_data['daily'][x]['icon']]
        except KeyError:
            icon = ""
        date = datetime.datetime.fromtimestamp(int(weather_data['daily']['data'][x]['time'])).strftime("%Y-%m-%d") # to be changed
        summary = weather_data['daily']['data'][x]['summary']
        if measure_type == 4:
            minTemp_f = str(weather_data['daily']['data'][x]['temperatureMin'])
            maxTemp_f = str(weather_data['daily']['data'][x]['temperatureMax'])
            minTemp_c = str(round((weather_data['daily']['data'][x]['temperatureMin'] - 32) * 5/9, 2))
            maxTemp_c = str(round((weather_data['daily']['data'][x]['temperatureMax'] - 32) * 5/9, 2))

            buildstr =  "%s: %s%s High: %s%s (%s%s) Low: %s%s (%s%s)" % (date, icon, summary, minTemp_f, u"°F", minTemp_c, u"°C", maxTemp_f, u"°F", maxTemp_c, u"°C")         
            forecast_list.append(buildstr)

        else:
            minTemp = str(weather_data['daily']['data'][x]['temperatureMin'])
            maxTemp = str(weather_data['daily']['data'][x]['temperatureMax'])

            buildstr = date + ": " + icon + summary + " High: " + maxTemp + temp_suffix[measure_type] + " Low: " + minTemp + temp_suffix[measure_type]
            forecast_list.append(buildstr)

    return forecast_list

def _parse_args(args):
    """Parses an already-split args list and returns a list with location, unit type, and forecast type, in that order."""
    if len(args) > 1: # If there are any optional args at all
        print "there are optional args"
        if args[1] in ["us", "si", "uk", "ca", "both"]: # If the first arg is for units, set up units
            if args[1] == "us":
                args[1] = 0
            elif args[1] == "si":
                args[1] = 1
            elif args[1] == "ca":
                args[1] = 2
            elif args[1] == "uk":
                args[1] = 3
            elif args[1] == "both":
                args[1] = 4

            try:  
                args[2] # If there is a second arg
                if not args[2] in ["brief", "summary"]:
                    args[2] = "summary"
            except IndexError: # If only units were specified, set default forecast arg
                args.append("summary")
        elif args[1] in ["brief", "summary"]: # If the first arg isn't for units, set the forecast arg and default units
            args.append(args[1])
            args[1] = 0
    else: # If no options were specified, set default units and forecast
        args.append(0)
        args.append("summary")

    ## DEBUG ##
    print args[0]
    print args[1]
    print args[2]
    ## END DEBUG ##

    return args

def _parse_weather_output(weather_data, city_name, measure_type):

    temp_suffix = [u"°F", u"°C", u"°C", u"°C"]
    wind_suffix = ["mph","m/s","kph","mph"]

    summary = weather_data['currently']['summary']
    humidity = str(weather_data['currently']['humidity'] * 100) + "%"
    wind_direction = weather_data['currently']['windBearing']
    precipProb = str(weather_data['currently']['precipProbability'] * 100) + "%"

    if measure_type == 4:
        temp_f = str(round(weather_data['currently']['temperature'], 2))
        temp_c = str(round((weather_data['currently']['temperature'] - 32) * 5/9, 2))
        feelslike_f = str(round(weather_data['currently']['apparentTemperature'], 2))
        feelslike_c = str(round((weather_data['currently']['apparentTemperature'] - 32) * 5/9, 2))
        windspeed_mph = str(round(weather_data['currently']['windSpeed'], 2))
        windspeed_ms = str(round(weather_data['currently']['windSpeed'] * .44704, 2))

        weather_string = "Weather for \x02%s\x02 \x02\x033|\x03\x02 %s, %s%s (%s%s) feels like %s%s (%s%s), %s humidity, wind %s %s (%s %s), %s chance of precipitation" % (city_name, summary, temp_f, temp_suffix[0], temp_c, temp_suffix[1], feelslike_f, temp_suffix[0], feelslike_c, temp_suffix[1], humidity, windspeed_mph, wind_suffix[0], windspeed_ms, wind_suffix[1], precipProb)
    else:
        temperature = str(round(weather_data['currently']['temperature'], 2))
        feels_like = str(round(weather_data['currently']['apparentTemperature'], 2))
        wind_speed = str(round(weather_data['currently']['windSpeed'], 2))

        weather_string = "Weather for \x02%s\x02 \x02\x033|\x03\x02 %s, %s%s feels like %s%s, %s humidity, wind %s %s, %s chance of precipitation" % (city_name, summary, temperature, temp_suffix[measure_type], feels_like, temp_suffix[measure_type], humidity, wind_speed, wind_suffix[measure_type], precipProb)

    return weather_string

def command_weather(bot, user, channel, args):
    """Gives weather for location. Follows the same syntax as .wadd."""

    settings = _import_yaml_data()
    measure_type = 0

    API_URL = "https://api.forecast.io/forecast/%s/%s"

    if args:
        args = args.split(":")
        print args
        latlng = _get_latlng(args[0])
        units = ""
        args = _parse_args(args)

        print args[1]

        if args[1] == 1:
            units = "?units=si"
            measure_type = 1
        elif args[1] == 2:
            units = "?units=ca"
            measure_type = 2
        elif args[1] == 3:
            units = "?units=uk"
            measure_type = 3
        elif args[1] == 4:
            units = "?units=us"
            measure_type = 4

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
            elif measure_type == 4:
                units = "?units=us"
            data = urllib2.urlopen(API_URL % (settings["weather"]["key"], latlng[0]) + units)
        else:
            bot.say(channel, "You're not in the database! Set a location with .wadd.")
            return

    weather_data = json.load(data)

    print weather_data["currently"].keys()

    weather_string = _parse_weather_output(weather_data, latlng[1], measure_type)

    bot.say(channel, weather_string.encode('utf-8'))

    return

def command_forecast(bot, user, channel, args):
    """Gives you a forecast. To use, add either :brief or :summary to your weather query. :brief will PM you always."""
    API_URL = "https://api.forecast.io/forecast/%s/%s"
    settings = _import_yaml_data()
    nick = user.split('!', 1)[0]

    if args:
        args = args.split(":")
        args = _parse_args(args)
        latlng = _get_latlng(args[0])
        units = ""

        measure_type = args[1]

        if measure_type == 1:
            units = "?units=si"
        elif measure_type == 2:
            units = "?units=ca"
        elif measure_type == 3:
            units = "?units=uk"
        elif measure_type == 4:
            units = "?units=us"
    else:
        db_data, success = _get_saved_data(nick.lower(), settings['weather']['db'])
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
            elif measure_type == 4:
                units = "?units=us"
        else:
            bot.say(channel, "You're not in the database! Set a location with .wadd.")
            return

    data = urllib2.urlopen(API_URL % (settings["weather"]["key"], latlng[0]) + units)

    weather_data = json.load(data)

    city_name = latlng[1].encode('utf-8')

    try:
        ftype = args[2]
    except IndexError:
        ftype = db_data[2]

    if ftype == "summary":
        bot.say(channel, "Forecast summary for \x02%s\x02 \x02\x033|\x03\x02 %s" % (city_name, weather_data['daily']['summary'].encode('utf-8')))
    else:
        forecast_strings = _parse_forecast_output(weather_data, city_name, measure_type)
        bot.say(nick, "Three-day forecast for \x02%s\x02" % city_name)
        for line in forecast_strings:
            bot.say(nick, line.encode('utf-8'))

def command_wadd(bot, user, channel, args):
    """Sets your location. Usage: .wadd location:units:forecast, Units can be any one of us, si, ca, uk, or both. Forecast is either brief or summary. Defaults to us/summary if no unit/forecast is specified."""

    settings = _import_yaml_data()

    args = args.split(":")
    print args
    nick = user.split('!', 1)[0]

    args = _parse_args(args)

    _set_saved_data(nick.lower(), args[0], settings['weather']['db'], args[1], args[2])

    bot.say(nick, "Location set!")

def command_w(bot, user, channel, args):
    """Gives weather for location. Follows the same syntax as .wadd."""
    return command_weather(bot, user, channel, args)

def command_f(bot, user, channel, args):
    """Alias to forecast. Uses the same syntax."""
    return command_forecast(bot, user, channel, args)