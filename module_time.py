# -*- coding: utf-8 -*-

import os
import time
import requests
import urllib
import json
from modules.dbHandler import dbHandler


def command_time(bot, user, channel, args):
    """Give it a city or zip code, it will give you the local time there"""

    LATLNG_URL = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false"
    TZ_URL = "https://maps.googleapis.com/maps/api/timezone/json?location=%s,%s&timestamp=%s&sensor=false"
    db = dbHandler(bot.factory.getDBPath())

    if args:
        place = db.get("time", args.split(" ", 1))
        if place is not None:
            latlng_data = requests.get(LATLNG_URL % urllib.quote(place))
            latlng_data = json.loads(latlng_data.content.encode('utf-8'))
        else:
            latlng_data = requests.get(LATLNG_URL % urllib.quote(args))
            latlng_data = json.loads(latlng_data.content.encode('utf-8'))
    else:
        place = db.get("time", user)
        if place is not None:
            latlng_data = requests.get(LATLNG_URL % urllib.quote(place))
            latlng_data = json.loads(latlng_data.content.encode('utf-8'))
        else:
            bot.say(channel, "Set your location using .weather add.")
            return

    try:
        lat = latlng_data['results'][0]['geometry']['location']['lat']
        lng = latlng_data['results'][0]['geometry']['location']['lng']
    except IndexError:
        bot.say(channel, "I don't know where %s is. Check that it's on this planet and try again." % (args))
        return

    timestamp = time.time()

    tz_data = requests.get(TZ_URL % (lat, lng, timestamp))
    tz_data = json.loads(tz_data.content.encode('utf-8'))
    tzid = tz_data['timeZoneId']
    raw_offset = tz_data['rawOffset']
    dst_offset = tz_data['dstOffset']
    gmt_offset = (raw_offset + dst_offset) / 3600
    gmt_offset_str = str(float(gmt_offset))
    if gmt_offset > 0:
        gmt_offset_str = "+" + gmt_offset_str

    os.environ['TZ'] = tzid
    time.tzset()
    timestr = time.strftime("%A, %B %d %Y %I:%M:%S %p %Z")
    address = latlng_data['results'][0]['formatted_address']
    os.environ['TZ'] = "America/New_York"  # not sure if necessary
    bot.say(channel, "The time and date in %s is %s, GMT %s" % (address.encode('utf-8'), timestr.encode('utf-8'), gmt_offset_str.encode('utf-8')))
    return
