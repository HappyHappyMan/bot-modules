"""
Warns about large files

$Id: module_urlsize.py 313 2011-06-03 11:22:38Z henri@nerv.fi $
$HeadURL: http://pyfibot.googlecode.com/svn/trunk/modules/module_urlsize.py $
"""


#def handle_url(bot, user, channel, url, msg):
#    """inform about large files (over 5MB)"""
#
#    # TODO: Hard-coded
#    if channel == "#wow":
#        return
#    size = getUrl(url).getSize()
#    headers = getUrl(url).getHeaders()
#    if 'content-type' in headers:
#        contentType = headers['content-type']
#    else:
#        contentType = "Unknown"
#    if not size:
#        return
#    size = size / 1024
#    if size > 5:
#        bot.say(channel, "File size: %s MB - Content-Type: %s" % (size, contentType))
#        return
