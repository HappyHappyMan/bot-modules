# -*- coding: utf-8 -*-
"""Displays HTML page titles

Smart title functionality for sites which could have clear titles,
but still decide show idiotic bulk data in the HTML title element

$Id: module_urltitle.py 321 2012-02-09 06:20:56Z riku.lindblad $
$HeadURL: http://pyfibot.googlecode.com/svn/trunk/modules/module_urltitle.py $
"""

import fnmatch
import urlparse
import logging
import re
import json
import urllib2
import requests
import yaml
import os
import base64
import HTMLParser

from types import TupleType

#from util.BeautifulSoup import BeautifulStoneSoup
#from util.BeautifulSoup import BeautifulSoup
from bs4 import BeautifulSoup

log = logging.getLogger("urltitle")
config = None


def init(bot):
    global config
    config = bot.config.get("module_urltitle", {})


def handle_url(bot, user, channel, url, msg):
    """Handle urls"""

    if msg.startswith("-"):
        return
    if re.match("http://.*?\.imdb\.com/title/tt([0-9]+)/?", url):
        return  # IMDB urls are handled elsewhere
    if re.match("(http:\/\/open.spotify.com\/|spotify:)(album|artist|track)([:\/])([a-zA-Z0-9]+)\/?", url):
        return  # spotify handled elsewhere

    if channel.lstrip("#") in config.get('disable', ''):
        return

    # hack, support both ignore and ignore_urls for a while
    for ignore in config.get("ignore", []):
        if fnmatch.fnmatch(url, ignore):
            log.info("Ignored URL: %s %s", url, ignore)
            return
    for ignore in config.get("ignore_urls", []):
        if fnmatch.fnmatch(url, ignore):
            log.info("Ignored URL: %s %s", url, ignore)
            return
    for ignore in config.get("ignore_users", []):
        if fnmatch.fnmatch(user, ignore):
            log.info("Ignored url from user: %s, %s %s", user, url, ignore)
            return

    # a crude way to handle the new-fangled shebang urls as per
    # http://code.google.com/web/ajaxcrawling/docs/getting-started.html
    # this can manage twitter + gawker sites for now
    url = url.replace("#!", "?_escaped_fragment_=")

    handlers = [(h, ref) for h, ref in globals().items() if h.startswith("_handle_")]

    # try to find a specific handler for the URL
    for handler, ref in handlers:
        pattern = ref.__doc__.split()[0]
        if fnmatch.fnmatch(url, pattern):
            title = ref(url)
            if title:
                # handler found, abort
                return _title(bot, channel, title, True)

    # We first determine whether this bit of media is humongous or not.
    # If it is, we have the bot output the content-type and size of the
    # file and return. Else, we proceed with the HTML parsing.

    data = requests.get(url)
    try:
        regex = re.findall(r'video/*|audio/*|image/*', data.headers['content-type'])
        if (len(regex) > 0) and (int(data.headers['content-length']) > (5*1024000)):
            log.debug("Media content detected")
            if 'content-type' in data.headers.keys():
                contentType = data.headers['content-type']
            else:
                contentType = "Unknown"
            size = int(data.headers['content-length']) / 1024000
            return _title(bot, channel, "File size: %s MB - Content-Type: %s" % (size, contentType))
        else:
            log.debug("Media content too small")
            return
    except KeyError:
        log.warning("Unknown data type, ignoring as it is possible security risk")
        return

    try:
        bs = BeautifulSoup(data.content.encode('utf-8'), "lxml")
    except UnicodeDecodeError:
        return
    except UnicodeEncodeError:
        return
   
    title = bs.title.text

    # no title attribute
    if not title:
        return

    try:
        # remove trailing spaces, newlines, linefeeds and tabs
        title = title.strip()
        title = title.replace("\n", " ")
        title = title.replace("\r", " ")
        title = title.replace("\t", " ")

        # compress multiple spaces into one
        title = re.sub("[ ]{2,}", " ", title)

        # nothing left in title (only spaces, newlines and linefeeds)
        if not title:
            return

        if _check_redundant(url, title):
            return

        return _title(bot, channel, title)

    except AttributeError:
        # TODO: Nees a better way to handle this. Happens with empty <title> tags
        pass


def _check_redundant(url, title):
    """Returns true if the url and title are similar enough."""
    # Remove hostname from the title
    hostname = urlparse.urlparse(url.lower()).netloc
    hostname = ".".join(hostname.split('@')[-1].split(':')[0].lstrip('www.').split('.'))
    cmp_title = title.lower()
    for part in hostname.split('.'):
        idx = cmp_title.replace(' ', '').find(part)
        if idx != -1:
            break

    if idx > len(cmp_title) / 2:
        cmp_title = cmp_title[0:idx + (len(title[0:idx]) - len(title[0:idx].replace(' ', '')))].strip()
    elif idx == 0:
        cmp_title = cmp_title[idx + len(hostname):].strip()
    # Truncate some nordic letters
    unicode_to_ascii = {u'\u00E4': 'a', u'\u00C4': 'A', u'\u00F6': 'o', u'\u00D6': 'O', u'\u00C5': 'A', u'\u00E5': 'a'}
    for i in unicode_to_ascii:
        cmp_title = cmp_title.replace(i, unicode_to_ascii[i])

    cmp_url = url.replace("-", " ")
    cmp_url = url.replace("+", " ")
    cmp_url = url.replace("_", " ")

    parts = cmp_url.lower().rsplit("/")

    distances = []
    for part in parts:
        if part.rfind('.') != -1:
            part = part[:part.rfind('.')]
        distances.append(_levenshtein_distance(part, cmp_title))

    if len(title) < 20 and min(distances) < 5:
        return True
    elif len(title) >= 20 and len(title) <= 30 and min(distances) < 10:
        return True
    elif len(title) > 30 and len(title) <= 60 and min(distances) <= 21:
        return True
    elif len(title) > 60 and min(distances) < 37:
        return True
    return False


def _levenshtein_distance(s, t):
    d = [[i] + [0] * len(t) for i in xrange(0, len(s) + 1)]
    d[0] = [i for i in xrange(0, (len(t) + 1))]

    for i in xrange(1, len(d)):
        for j in xrange(1, len(d[i])):
            if len(s) > i - 1 and len(t) > j - 1 and s[i - 1] == t[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min((d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + 1))

    return d[len(s)][len(t)]


def _title(bot, channel, title, smart=False):
    """Say title to channel"""

    if not title: return

    #prefix = "Title:"
    info = None
    # tuple, additional info
    if type(title) == TupleType:
        info = title[1]
        title = title[0]
    # crop obscenely long titles
    if len(title) > 300:
        title = title[:300] + "..."

    log.info(title)

    if not info:
        return bot.say(channel, "%s" % (title.encode('utf-8')))
    else:
        return bot.say(channel, "%s [%s]" % (title, info))


# TODO: Some handlers does not have if not bs: return, but why do we even have this for every function
def _handle_iltalehti(url):
    """*iltalehti.fi*html"""
    # Go as normal
    bs = getUrl(url).getBS()
    if not bs:
        return
    title = bs.first('title').string
    # The first part is the actual story title, lose the rest
    title = title.split("|")[0].strip()
    return title


def _handle_iltasanomat(url):
    """*iltasanomat.fi*uutinen.asp*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    title = bs.title.string.rsplit(" - ", 1)[0]
    return title


def _handle_keskisuomalainen_sahke(url):
    """*keskisuomalainen.net*sahkeuutiset/*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    title = bs.first('p', {'class': 'jotsikko'})
    if title:
        title = title.next.strip()
        return title


def _handle_tietokone(url):
    """http://www.tietokone.fi/uutta/uutinen.asp?news_id=*"""
    bs = getUrl(url).getBS()
    sub = bs.first('h5').string
    main = bs.first('h2').string
    return "%s - %s" % (main, sub)


def _handle_itviikko(url):
    """http://www.itviikko.fi/*/*/*/*/*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    return bs.first("h1", "headline").string


def _handle_kauppalehti(url):
    """http://www.kauppalehti.fi/4/i/uutiset/*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    title = bs.fetch("h1")[1].string.strip("\n ")
    return title


def _handle_verkkokauppa(url):
    """http://www.verkkokauppa.com/*/product/*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    product = bs.first('h1', id='productName').string
    price = bs.first('span', {'class': 'hintabig'}).string
    return "%s | %s" % (product, price)


def _handle_mol(url):
    """http://www.mol.fi/paikat/Job.do?*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    title = bs.first("div", {'class': 'otsikko'}).string
    return title

def _import_yaml_data(directory=os.curdir):
    if os.path.exists(directory):
        settings_path = os.path.join(directory, "modules", "twitter.settings")
        return yaml.load(file(settings_path))
    else:
        print "Settings file for Twitter not set up; please create a Twitter API account and modify the example settings file."
        return


def _handle_tweet(url):
    """http*://twitter.com/*/status/*"""
    settings = _import_yaml_data()
    secret_key = settings['twitter']['consumer_secret']
    con_key = settings['twitter']['consumer_key']
    auth_url = "https://api.twitter.com/oauth2/token"
    tweet_url = "https://api.twitter.com/1.1/statuses/show/%s.json"

    test = re.match("https?://w?w?w?\.?twitter\.com\/(\w+)/statuse?s?/(\d+)*", url)
    username = test.group(1)

    # Now to deal with all the ridiculous authentication stuff
    base64_key = base64.b64encode(con_key + ":" + secret_key)

    headers_lib = {}
    headers_lib['Authorization'] = "Basic " + base64_key
    headers_lib['Content-Type'] = "application/x-www-form-urlencoded;charset=UTF-8"

    auth_return = requests.post(auth_url, "grant_type=client_credentials", headers=headers_lib)
    auth_dict = json.loads(auth_return.content.encode('utf-8'))

    if auth_dict['token_type'] != "bearer":
        log.error("token_type was not bearer, something went wrong. Look into it.")
        return

    #matches for unique tweet id string
    get_url = tweet_url % test.group(2)
    get_token = "Bearer " + auth_dict['access_token']
    token_headers_lib = {}
    token_headers_lib["Authorization"] = get_token
    twitapi = requests.get(get_url, headers=token_headers_lib)

    #loads into dict
    json1 = json.loads(twitapi.content.encode('utf-8'))

    #reads dict
    ##You can modify the fields below or add any fields you want to the returned string
    try:
        text = json1['text']
        user = json1['user']['screen_name']
        name = json1['user']['name']
        tweet = "Tweet by \x02%s\x02 (\x02@%s\x02) \x02\x0310|\x03\x02 %s" % (name, user, text)
    except IndexError:
        log.error("Something went wrong with the twitter url handler, look into it.")
    return tweet

def _handle_tweet_2(url):
    """http*://www.twitter.com/*/status/*"""
    return _handle_tweet(url)

def _handle_tweet_3(url):
    """http*://twitter.com/*/statuses/*"""
    return _handle_tweet(url)

def _handle_tweet_4(url):
    """http*://www.twitter.com/*/statuses/*"""
    return _handle_tweet(url)


def _handle_netanttila(url):
    """http://www.netanttila.com/webapp/wcs/stores/servlet/ProductDisplay*"""
    bs = getUrl(url).getBS()
    itemname = bs.first("h1").string.replace("\n", "").replace("\r", "").replace("\t", "").strip()
    price = bs.first("td", {'class': 'right highlight'}).string.split(" ")[0]
    return "%s | %s EUR" % (itemname, price)


def _handle_youtube_shorturl(url):
    """http*://youtu.be/*"""
    return _handle_youtube_gdata(url)


def _handle_youtube_gdata_new(url):
    """http*://youtube.com/watch#!v=*"""
    return _handle_youtube_gdata(url)


def _handle_youtube_gdata(url):
    """http*://*youtube.com/watch?*v=*"""
    from datetime import timedelta
    gdata_url = "http://gdata.youtube.com/feeds/api/videos/%s"

    match = re.match("https?://youtu.be/(.*)", url)
    if not match:
        match = re.match("https?://.*?youtube.com/watch\?.*?v=([^&]+)", url)
    if match:
        infourl = gdata_url % match.group(1)
        bs = getUrl(infourl, True).getBS()

        entry = bs.first("entry")

        if not entry:
            log.info("Video too recent, no info through API yet.")
            return

        author = entry.author.next.string
        # if an entry doesn't have a rating, the whole element is missing
       # try:
       #     rating = float(entry.first("gd:rating")['average'])
       # except TypeError:
       #     rating = 0.0

        #stars = int(round(rating)) * "*"
        statistics = entry.first("yt:statistics")
        if statistics:
            views = format(int(statistics['viewcount']), ",d")
        else:
            views = "no"
        racy = entry.first("yt:racy")
        media = entry.first("media:group")
        title = media.first("media:title").string
        secs = int(media.first("yt:duration")['seconds'])
        
        length = str(timedelta(seconds=secs))
        if racy:
            adult = " \x034|\x03 \x02NSFW\x02"
        else:
            adult = ""
        return "%s \x034|\x03 uploaded by %s \x034|\x03 %s views%s \x034|\x03 %s" % (title, author, views, adult, length)

def _handle_helmet(url):
    """http://www.helmet.fi/record=*fin"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    title = bs.find(attr={'class': 'bibInfoLabel'}, text='Teoksen nimi').next.next.next.next.string
    return title


def _handle_ircquotes(url):
    """http://*ircquotes.fi/[?]*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    chan = bs.first("span", {'class': 'quotetitle'}).next.next.string
    points = bs.first("span", {'class': 'points'}).next.string
    firstline = bs.first("div", {'class': 'quote'}).next.string
    title = "%s (%s): %s" % (chan, points, firstline)
    return title


def _handle_alko2(url):
    """http://alko.fi/tuotteet/fi/*"""
    return _handle_alko(url)


def _handle_alko(url):
    """http://www.alko.fi/tuotteet/fi/*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    name = bs.find('span', {'class': 'tuote_otsikko'}).string
    price = bs.find('span', {'class': 'tuote_hinta'}).string.split(" ")[0] + u"€"
    drinktype = bs.find('span', {'class': 'tuote_tyyppi'}).next
    return name + " - " + drinktype + " - " + price


def _handle_salakuunneltua(url):
    """*salakuunneltua.fi*"""
    return None


def _handle_facebook(url):
    """*facebook.com/*"""
    if not has_json: return
    if re.match("http(s?)://(.*?)facebook\.com/(.*?)id=(\\d+)", url):
        asd = urlparse.urlparse(url)
        id = asd.query.split('id=')[1].split('&')[0]
        if id != '':
            url = "https://graph.facebook.com/%s" % id
            content = getUrl(url, True).getContent()
            if content != 'false':
                data = json.loads(content)
                try:
                    title = data['name']
                except:
                    return
            else:
                title = 'Private url'
    else:
        return
    return title


def _handle_vimeo(url):
    """*vimeo.com/*"""
    data_url = "http://vimeo.com/api/v2/video/%s.xml"
    match = re.match("http://.*?vimeo.com/(\d+)", url)
    if match:
        infourl = data_url % match.group(1)
        bs = getUrl(infourl, True).getBS()
        title = bs.first("title").string
        user = bs.first("user_name").string
        likes = bs.first("stats_number_of_likes").string
        plays = bs.first("stats_number_of_plays").string
        return "%s by %s [%s likes, %s views]" % (title, user, likes, plays)


def _handle_stackoverflow(url):
    """*stackoverflow.com/questions/*"""
    if not has_json: return
    api_url = 'http://api.stackoverflow.com/1.1/questions/%s'
    match = re.match('.*stackoverflow.com/questions/([0-9]+)', url)
    if match is None:
        return
    question_id = match.group(1)
    content = getUrl(api_url % question_id, True).getContent()
    if not content:
        log.debug("No content received")
        return
    try:
        data = json.loads(content)
        title = data['questions'][0]['title']
        tags = "/".join(data['questions'][0]['tags'])
        score = data['questions'][0]['score']
        return "%s - %dpts - %s" % (title, score, tags)
    except Exception, e:
        return "Json parsing failed %s" % e


def _handle_hs(url):
    """*hs.fi*artikkeli*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    title = bs.title.string
    title = title.split("-")[0].strip()
    try:
        # determine article age and warn if it is too old
        from datetime import datetime
        # handle updated news items of format, and get the latest update stamp
        # 20.7.2010 8:02 | PÃ¤ivitetty: 20.7.2010 12:53
        date = bs.first('p', {'class': 'date'}).next
        # in case hs.fi changes the date format, don't crash on it
        if date:
            date = date.split("|")[0].strip()
            article_date = datetime.strptime(date, "%d.%m.%Y %H:%M")
            delta = datetime.now() - article_date

            if delta.days > 365:
                return title, "NOTE: Article is %d days old!" % delta.days
            else:
                return title
        else:
            return title
    except Exception, e:
        log.error("Error when parsing hs.fi: %s" % e)
        return title


def _handle_ksml(url):
    """*ksml.fi/uutiset*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    title = bs.title.string
    title = title.split("-")[0].strip()
    return title


def _handle_mtv3(url):
    """*mtv3.fi*"""
    bs = getUrl(url).getBS()
    title = bs.first("h1", "otsikko").next
    return title


def _handle_yle(url):
    """http://*yle.fi/uutiset/*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    title = bs.title.string
    title = title.split("|")[0].strip()
    return title


def _handle_varttifi(url):
    """http://www.vartti.fi/artikkeli/*"""
    bs = getUrl(url).getBS()
    title = bs.first("h2").string
    return title


def _handle_aamulehti(url):
    """http://www.aamulehti.fi/*"""
    bs = getUrl(url).getBS()
    if not bs:
        return
    title = bs.fetch("h1")[0].string
    return title


def _handle_apina(url):
    """http://apina.biz/*"""
    return None


def _handle_reddit(url):
    """*reddit.com/r/*"""

    if url[-1] != "/":
        ending = "/.json"
    else:
        ending = ".json"
    json_url = url + ending

    headers_lib = {}
    headers_lib["User-Agent"] = "Lazybot/Claire by Happy_Man"
    content_request = urllib2.Request(json_url, None, headers_lib)
    content = urllib2.urlopen(content_request)
    api_return = json.load(content)

    if not content:
        log.debug("No content received")
        return
    try:
        data = api_return[0]['data']['children'][0]['data']
        title = data['title']
        ups = data['ups']
        downs = data['downs']
        subreddit = data['subreddit']
        if data['domain'][:4] == "self":
            link = ""
        else:
            link = "\x037\x02|\x02\x03 " + data['url']
        score = ups - downs
        num_comments = data['num_comments']
        over_18 = data['over_18']
        result = "\x02r/%s\x02 \x037\x02|\x02\x03 %s - %d pts (%d up, %d down) \x037\x02|\x02\x03 %d comments %s" % (subreddit, title, score, ups, downs, num_comments, link)
        if over_18 is True:
            result = result + " \x037\x02|\x02\x03 \x02NSFW\x02"
        return result
    except Exception, e:
        return


def _handle_reddit_2(url):
    """*redd.it/*"""

    match = re.search(r"(?<=it/)[a-z1-9]+", url)

    info_url = "http://www.reddit.com/api/info.json?id=t3_%s"

    headers_lib = {}
    headers_lib["User-Agent"] = "Lazybot/Claire by Happy_Man"
    content_request = urllib2.Request(info_url % match.group(0), None, headers_lib)
    content = urllib2.urlopen(content_request)
    api_return = json.load(content)

    full_url = api_return['data']['children'][0]['data']['permalink']
    return _handle_reddit("http://www.reddit.com" + full_url)

def _handle_reddit_user(url):
    """*reddit.com/user/*"""

    match = re.search(r"(?<=user/)[\w'_-]+", url)
    info_url = "http://www.reddit.com/user/%s/about.json"

    headers_lib = {}
    headers_lib["User-Agent"] = "Lazybot/Claire by Happy_Man"
    content_request = urllib2.Request(info_url % match.group(0), None, headers_lib)
    content = urllib2.urlopen(content_request)
    api_return = json.load(content)

    data = api_return["data"]

    result = "Reddit user \x02%s\x02 \x037\x02|\x02\x03 %d link karma, %d comment karma" % (data["name"], data["link_karma"], data["comment_karma"])

    return result

def _handle_reddit_user_2(url):
    """*reddit.com/u/*"""
    match = re.search(r"(?<=u/)[\w'_-]+", url)

    return _handle_reddit_user("http://www.reddit.com/user/%s" % match.group(0))

def _handle_gfycat(url):
    """*gfycat.com/*"""
    match = re.search(r'(?<=gfycat.com/)[\w]+', url)

    r = requests.get("http://gfycat.com/cajax/get/%s" % match.group(0))
    j = json.loads(r.content.encode('utf-8'))

    j = j['gfyItem']

    views = j['views']
    gifsize = float(j['gifSize'])
    mp4size = float(j['mp4Size'])
    subreddit = j['redditId']
    username = j['userName']

    if subreddit:
        subredditstr = " \x039\x02|\x02\x03 http://redd.it/%s" % subreddit
    else:
        subredditstr = ""

    #if nsfw == 1:
    #    nsfwstr = " \x039\x02|\x02\x03 \x02NSFW\x02"
    #else:
    #    nsfwstr = ""

    reduction = str(round(gifsize / mp4size, 1)) + "×".decode('utf-8')
    returnstr = "Gfycat by \x02%s\x02%s \x039\x02|\x02\x03 %s smaller \x039\x02|\x02\x03 %s views" % (username, subredditstr, reduction, views)

    return returnstr.encode('utf-8')

def _handle_mediacrush(url):
    """*mediacru.sh/*"""

    match = re.search(r'(?<=mediacru.sh/)[\w]+', url)

    r = requests.get("http://mediacru.sh/%s.json" % match.group(0))
    j = json.loads(r.content.encode('utf-8'))

    compression = str(j['compression']) + "×".decode('utf-8')

    if j['blob_type'] == "video":
        length = j['metadata']['duration']
        m, s = divmod(length, 60)
        h, m = divmod(m, 60)
        duration_str = "%d:%02d:%02d" % (h, m, s)

        has_audio = j['metadata']['has_audio']
        if has_audio:
            audio_str = " \x039\x02|\x02\x03 Caution, has audio!" 
        else:
            audio_str = ""

        nsfw = j['flags']['nsfw']
        if nsfw:
            nsfwstr = " \x039\x02|\x02\x03 \x02NSFW\x02"
        else:
            nsfwstr = ""

        returnstr = "Mediacrush video \x039\x02|\x02\x03 %s smaller \x039\x02|\x02\x03 %s%s%s" % (compression, duration_str, audio_str, nsfwstr)
    if j['blob_type'] == "audio":
        try:
            album = " from album " + j['metadata']['album']
            artist = " by " + j['metadata']['artist']
            title = j['metadata']['title']
        except KeyError:
            album = ""
            artist = ""
            title = ""

        length = j['metadata']['duration']
        m, s = divmod(length, 60)
        h, m = divmod(m, 60)
        duration_str = "%d:%02d:%02d" % (h, m, s)

        if j['flags']['nsfw']:
            nsfwstr = " \x039\x02|\x02\x03 \x02NSFW\x02" 
        else:
            nsfwstr = ""

        returnstr = "Mediacrush audio \x039\x02|\x02\x03 %s smaller \x039\x02|\x02\x03 %s%s%s \x039\x02|\x02\x03 %s%s" % (compression, title, artist, album, duration_str, nsfwstr)
    elif j['blob_type'] == "image":
        if j['flags']['nsfw']:
            nsfwstr = " \x039\x02|\x02\x03 \x02NSFW\x02"
        else:
            nsfwstr = ""

        returnstr = "Mediacrush image \x039\x02|\x02\x03 %s smaller%s" % (compression, nsfwstr)

    return returnstr

