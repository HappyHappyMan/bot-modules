"""
Module that, when called, insults people.

Can also be modified with minimal effort to just read a random line from a file.

Because honestly, what bot isn't complete without the ability for users to insult others?
"""
import linecache
import random
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
        return i + 1

def command_insult(bot, user, channel, args):
    linecount = file_len("/home/sri/bots/testbot/modules/insults.txt")
    return_line = linecache.getline("/home/sri/bots/testbot/modules/insults.txt", random.randint(0, linecount))
    nick = user.split('!', 1)[0]

    bot.say(channel, str(args) + ", " + str(nick) + " would like you to know that " + str(return_line))