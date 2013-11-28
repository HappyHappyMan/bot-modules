# -*- coding: utf-8 -*-

import os
import time
import urllib2
import urllib
import json


def command_time(bot, user, channel, args):
    """Give it a city or zip code, it will give you the local time there"""

    LATLNG_URL = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false"
    TZ_URL = "https://maps.googleapis.com/maps/api/timezone/json?location=%s,%s&timestamp=%s&sensor=false"

    def is_number(args):
        try:
            int(args)
            return True
        except ValueError:
            return False

    if is_number(args) is True:
        print LATLNG_URL % args
        latlng_data = json.load(urllib2.urlopen(LATLNG_URL % args))
    else:
        if args[:2] == "in":
            args = args[2:]
        args = urllib.quote(args)
        print args
        print LATLNG_URL % args
        latlng_data = json.load(urllib2.urlopen(LATLNG_URL % args))

    lat = latlng_data['results'][0]['geometry']['location']['lat']
    lng = latlng_data['results'][0]['geometry']['location']['lng']
    timestamp = time.time()

    tz_data = json.load(urllib2.urlopen(TZ_URL % (lat, lng, timestamp)))
    tzid = tz_data['timeZoneId']
    raw_offset = tz_data['rawOffset']
    dst_offset = tz_data['dstOffset']
    gmt_offset = (raw_offset + dst_offset) / 3600
    gmt_offset_str = str(gmt_offset)
    if gmt_offset > 0:
        gmt_offset_str = "+" + gmt_offset_str

    os.environ['TZ'] = tzid
    time.tzset()
    timestr = time.strftime("%A, %B %d %Y %I:%M:%S %p %Z")
    address = latlng_data['results'][0]['formatted_address']
    os.environ['TZ'] = "America/New_York"  # not sure if necessary
    bot.say(channel, "The time and date in %s is %s, GMT %s" % (address.encode('utf-8'), timestr.encode('utf-8'), gmt_offset_str.encode('utf-8')))
    return
