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

    # We first determine whether this bit of media is humongous or not.
    # If it is, we have the bot output the content-type and size of the
    # file and return. Else, we proceed with the HTML parsing.

    data = requests.get(url)
    try:
        regex = re.findall(r'video/*|audio/*|image/*', data.headers['content-type'])
        if (len(regex) > 0):
            log.info("This is media content, deferring to other handler")
            return
    except KeyError:
        log.warning("Unknown data type, ignoring as it is possible security risk")
        return

    # try to find a specific handler for the URL
    for handler, ref in handlers:
        pattern = ref.__doc__.split()[0]
        log.debug("Pattern is " + pattern)
        if fnmatch.fnmatch(url, pattern):
            title = ref(url)
            if title:
                # handler found, abort
                return _title(bot, channel, title, True)

    try:
        bs = BeautifulSoup(data.content.encode('utf-8'), "lxml")
    except UnicodeDecodeError:
        return
    except UnicodeEncodeError:
        return


    # no title attribute
    if not bs.title:
        return

    title = bs.title.text

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
def _import_yaml_data(directory=os.curdir, service="twitter"):
    if os.path.exists(directory):
        settings_path = os.path.join(directory, "modules", "{}.settings".format(service.lower()))
        return yaml.load(file(settings_path))
    else:
        log.error("Settings file for Twitter not set up; please create a Twitter API account and modify the example settings file.")
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
    auth_dict = json.loads(auth_return.content)

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
    json1 = json.loads(twitapi.content)

    #reads dict
    ##You can modify the fields below or add any fields you want to the returned string
    try:
        text = json1['text']
        user = json1['user']['screen_name']
        name = json1['user']['name']
        time = json1['created_at']
        tweet = "Tweet by \x02%s\x02 (\x02@%s\x02) \x02\x0310|\x03\x02 %s \x02\x0310|\x03\x02 %s" % (name, user, text, time)
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

def _handle_youtube_shorturl(url):
    """http*://youtu.be/*"""
    return _handle_youtube_gdata(url)


def _handle_youtube_gdata_new(url):
    """http*://youtube.com/watch#!v=*"""
    return __handle_youtube_gdata(url)


def _handle_youtube_gdata(url):
    """http*://*youtube.com/watch?*v=*"""
    settings = _import_yaml_data(service="google")
    log.info(settings)
    gdata_url = "https://www.googleapis.com/youtube/v3/videos"
    match = re.match("https?://youtu.be/(.*)", url)
    if not match:
        match = re.match("https?://.*?youtube.com/watch\?.*?v=([^&]+)", url)
    if match:
	try:
            thing = match.group(1)
	    yt_index = thing.index('?')
            yt_id = thing[:yt_index]
        except ValueError:
            yt_id = match.group(1)
        params = {'id': yt_id,
                   'part': 'snippet,contentDetails,statistics',
                   'fields': 'items(id,snippet,contentDetails,statistics)',
                   'key': settings['google']['key']}

        r = requests.get(gdata_url, params=params)
        if not r.status_code == 200:
            error = r.json().get('error')
            if error:
                log.warning("Youtube API Error: {}".format(error))
            else:
                log.warning("Youtube API Error: {}".format(r2.status_code))
            return

        items = r.json()['items']
        if len(items) == 0: return
        entry = items[0]

        author = entry['snippet']['channelTitle']
        try:
            views = "{:,}".format(int(entry['statistics']['viewCount']))
        except KeyError:
            views = "no"

        rating = entry['contentDetails'].get('contentRating', None)
        if rating:
            rating = rating.get('ytRating', None)

        if rating and rating == 'ytAgeRestricted':
            racy = True
        else:
            racy = False
        
        title = entry['snippet']['title']
        length = entry['contentDetails']['duration'][2:].lower()
        
        if racy:
            adult = " \x034|\x03 \x02NSFW\x02"
        else:
            adult = ""
        return "%s \x034|\x03 uploaded by %s \x034|\x03 %s views%s \x034|\x03 %s" % (title, author, views, adult, length)

#def _handle_vimeo(url):
#    """*vimeo.com/*"""
#    data_url = "http://vimeo.com/api/v2/video/%s.xml"
#    match = re.match("http://.*?vimeo.com/(\d+)", url)
#    if match:
#        infourl = data_url % match.group(1)
#        bs = getUrl(infourl, True).getBS()
#        title = bs.first("title").string
#        user = bs.first("user_name").string
#        likes = bs.first("stats_number_of_likes").string
#        plays = bs.first("stats_number_of_plays").string
#        return "%s by %s [%s likes, %s views]" % (title, user, likes, plays)


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
    #TODO: Actually fix the url parsing to strip parameters
    try:
        api_return = json.load(content)
    except ValueError:
        return
    ## logic to handle comments vs content
    match = re.search(r'http.*reddit\.com\/r\/.*\/comments\/\w*\/.*\/(\w*)\/\.json', json_url)
    if match:
        return __handle_reddit_comment_permalink(api_return[1])
    else:
        return __handle_reddit_content(api_return[0])

def __handle_reddit_comment_permalink(content):
    if not content:
        log.error("No content received from reddit API")
        return "No content received from Reddit API."
    body = content['data']['children'][0]['data']['body']
    author = content['data']['children'][0]['data']['author']
    score = content['data']['children'][0]['data']['score']
    gilded = content['data']['children'][0]['data']['gilded']

    maxLen = 316
    truncLen = 316
    ## 75 is a magic number corresponding to how many non-variable characetrs
    ## there are in the string.
    textLen = len(body) + len(author) + len(str(score)) + len(str(gilded)) + 75
    if textLen > maxLen:
        truncLen = maxLen - textLen
        while True:
            if body[trunclen] == " ":
                break
            else:
                truncLen = truncLen - 1
                continue
    body = body[:truncLen] + "..."
    result = '\x02Comment by /u/%s \x037|\x03\x02 "%s" \x02\x037|\x03\x02 Gilded %s times, %s upvotes' % (author, body, gilded, score)
    return result


def __handle_reddit_content(content):
    if not content:
        log.error("No content received")
        return "No content received from Reddit API."
    try:
        data = content['data']['children'][0]['data']
        title = data['title']
        subreddit = data['subreddit']
        if data['domain'][:4] == "self":
            link = ""
        else:
            link = "\x037\x02|\x02\x03 " + data['url']
        score = data['score']
        num_comments = data['num_comments']
        over_18 = data['over_18']
        result = "\x02r/%s\x02 \x037\x02|\x02\x03 %s - %d pts \x037\x02|\x02\x03 %d comments %s" % (subreddit, title, score, num_comments, link)
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

    return __handle_reddit_content(api_return)

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
    j = json.loads(r.content)

    j = j['gfyItem']

    views = j['views']
    gifsize = float(j['gifSize'])
    mp4size = float(j['mp4Size'])
    subreddit = j['redditId']
    username = j['userName']
    nsfw = int(j['nsfw'])

    if subreddit:
        subredditstr = " \x039\x02|\x02\x03 http://redd.it/%s" % subreddit
    else:
        subredditstr = ""

    if nsfw == 1:
        nsfwstr = " \x039\x02|\x02\x03 \x02NSFW\x02"
    else:
        nsfwstr = ""

    reduction = str(round(gifsize / mp4size, 1)) + u"×" # trying this
    returnstr = u"Gfycat by \x02%s\x02%s \x039\x02|\x02\x03 %s smaller \x039\x02|\x02\x03 %s views%s" % (username, subredditstr, reduction, views, nsfwstr)

    return returnstr

def _handle_mediacrush(url):
    """*mediacru.sh/*"""

    match = re.search(r'(?<=mediacru.sh/)[\w_-]+', url)

    r = requests.get("http://mediacru.sh/%s.json" % match.group(0))
    j = json.loads(r.content)

    try:
        compression = str(j['compression']) + u"×"
    except KeyError:
        compression = ""

    if j['type'] == "application/album":
        album_len = len(j['files'])
        returnstr = "Mediacrush album \x03\x02|\x02\x03 %s files" % album_len

    elif j['blob_type'] == "video":
        # length = j['metadata']['duration']
        # m, s = divmod(length, 60)
        # h, m = divmod(m, 60)
        # duration_str = "%d:%02d:%02d" % (h, m, s)

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

        returnstr = "Mediacrush video \x039\x02|\x02\x03 %s%s" % (audio_str, nsfwstr)
    elif j['blob_type'] == "audio":
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

