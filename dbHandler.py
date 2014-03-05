import sqlite3
import logging

log = logging.getLogger("dbHandler")

class dbHandler(object):
    """handles database connections for modules."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.db_conn = sqlite3.connect(db_path)
        self.db_cur = self.db_conn.cursor()


    def __del__(self):
        self.db_conn.commit()
        self.db_conn.close()


    def get(self, module, user):
        user = user.lower()
        try:
            userid = self._get_userid(user) # to be implemented
        except IDNotFoundError:
            log.debug("get(): _get_userid() raised IDNotFoundError")
            return None
        handler_method = getattr(self, "_handle_%s" % module, None)

        if handler_method is not None:
            log.debug("Passing control from get() to handle_%s" % module)
            try:
                data = handler_method(userid)
            except IDNotFoundError:
                data = None
            return data

    def set(self, module, user, args):
        user = user.lower()
        try:
            log.debug("set(): Passing control to _get_userid()")
            userid = self._get_userid(user)
        except IDNotFoundError:
            log.debug("set(): _get_userid() raised IDNotFoundError")
            userid = self._set_userid(user)

        log.debug("set(): Found userid " + str(userid))
        handler_method = getattr(self, "_handle_%s" % module, None)

        log.debug("Found handler method _handle_%s()" % module)

        if handler_method is not None:
            log.debug("set(): Passing control from set() to handle_%s" % module)
            handler_method(userid, user, args)
            self.db_conn.commit()

    def _search(self, nick):
        """
        Searches the Users table for the userid matching the nick param.
        Returns None if the nick can't be matched.
        """
        log.debug("_search(): looking for nick " + nick)
        result = self.db_cur.execute("SELECT userid FROM Users WHERE nick LIKE ?", 
            (nick,))
        try:
            uid = result.fetchone()[0]
            log.debug("_search(): userid for nick %s found as %s" % (nick, uid))
            return uid
        except TypeError:
            log.debug("_search(): userid for nick %s not found" % nick)
            return None

    def _get_userid(self, user):
        """
        Handles the logic behind reliably matching a full hostname string to a userid
        that may or may not be entirely theirs.

        Accepts full nick!ident@host as param "user". Returns either an integer
        representing the userid or raises IDNotFoundError.
        """
        log.debug("_get_userid(): Looking for userid for user %s " % user)
        try:
            result = self.db_cur.execute("SELECT userid FROM Users WHERE User LIKE ?", 
                (user,))
            uid = result.fetchone()[0]
            return uid
        except TypeError:
            # Here is the rationale behind this seemingly ridiculous code.
            # There are three parts to a userstring: the nick, the ident, and the host.
            # This makes eight possible combinations of matches between two userstrings'
            # parts. i.e., "both nicks match, both idents match, hosts don't match" or
            # "nicks don't match, idents match, hosts match", etc. There are eight possible
            # combinations in total.
            # 
            # Now, only three of these eight combinations are likely to be the same person.
            # One of those three is that all three parts match, which has already been
            # handled. So we only have two cases to deal with here:
            # 1) nicks don't match, but idents and hosts do (011)
            # 2) nicks and idents match,  but hosts don't. (110)
            # 
            # This code goes through and finds those possibilities, and returns userids
            # in both cases. Otherwise, it raises an Error to be caught up above.
            log.debug("_get_userid(): user did not match full userstring")
            nick = user.split("!", 1)[0]

            log.debug("_get_userid(): passing control to _search()")
            search_userid = self._search(nick)
            log.debug("_get_userid(): Control returned from _search()")
            if search_userid is not None:
                return search_userid
            else:
                try:
                    #1
                    result = self.db_cur.execute("SELECT userid FROM Users WHERE nick LIKE ?",
                        (nick,))
                    uid = result.fetchone()[0]
                    try:
                        #11
                        ident = user.split("!", 1)[1].split("@", 1)[0]
                        result = self.db_cur.execute("SELECT userid FROM Users WHERE ident LIKE ?",
                            (ident,))
                        uid = result.fetchone()[0]
                        return uid
                    except TypeError:
                        #10
                        raise IDNotFoundError
                except TypeError:
                    try:
                        ident = user.split("!", 1)[1].split("@", 1)[0]
                        try:
                            #01
                            result = self.db_cur.execute("SELECT userid FROM Users WHERE ident LIKE ?",
                                (ident,))
                            uid = result.fetchone()[0] 
                            try:
                                #011
                                host = user.split("@", 1)[1]
                                result = self.db_cur.execute("SELECT userid FROM Users WHERE host  LIKE ?",
                                    (host,))
                                return result.fetchone()[0]
                            except TypeError:
                                #010
                                raise IDNotFoundError
                        except TypeError:
                            #00
                            raise IDNotFoundError
                    except IndexError:
                        raise IDNotFoundError


    def _set_userid(self, user):
        """
        This is a very naive function. Give it a userstring, and it will
        insert it into the database, no questions asked or needed.
        """
        nick = user.split("!", 1)[0]
        ident = user.split("!", 1)[1].split("@", 1)[0]
        host = user.split("@", 1)[1]

        self.db_cur.execute("INSERT INTO Users VALUES (?, ?, ?, ?, ?)", 
            (None, user, nick, ident, host))

    
    def _handle_lastfm(self, userid, user=None, args=None):
        """
        The lastfm handler is a sort of demo implementation, since the backing
        database table is about as simple as it gets. As such, this docstring 
        will serve as a tutorial on how to write a handler, for further reference.
        Every handler function must follow the naming convention _handle_<modulename>,
        and must ask for three arguments: userid, user=None and args=None. userid is an integer
        representing that user in the database, as discovered by _get_userid(). args 
        is an optional argument, passed only by set(). user is also passed by set() just
        in case you need it, if not, then don't use it. You can use the existence
        of args to determine whether you need to execute getter or setter logic.

        What you want to return for your getter and setter logic is entirely up to you.
        What I'll be demoing here is getting and setting a single value associated with 
        a userid. Anything more complicated is up to you.

        Don't worry about commit() or close(), those are handled outside of handlers.
        """ 
        if args is None:
            ## This is the getter logic
            try:
                testresult = self.db_cur.execute("SELECT lastid FROM lastfm WHERE userid=?", 
                    (userid,))
                return testresult.fetchone()[0]
            except TypeError:
                raise IDNotFoundError
        else:
            ## This is the setter logic
            if userid is None:
                ## This means that the user and entry are brand-new
                uid = self._get_userid(user) # get our new userid

                self.db_cur.execute("INSERT INTO lastfm VALUES (?, ?)", 
                    (uid, args))
            else:
                # This means just the entry is brand-new, but that the user already
                # exists in the Users table.
                try:
                    # We first test whether the userid is already in the table, 
                    # and, if so, we update the entry.
                    testresult = self.db_cur.execute("SELECT userid FROM lastfm WHERE userid=(?)",
                        (userid,))
                    testresult.fetchone()[0]
                    self.db_cur.execute("UPDATE lastfm SET lastid=(?) WHERE userid=(?)",
                        (args,userid))
                except TypeError:
                    # If the userid is not present in the table, we drop down here,
                    # and create an entirely new row in the table for that user.
                    self.db_cur.execute("INSERT INTO lastfm VALUES (?, ?)",
                        (userid, args))
        return

    def _handle_weather(self, userid, user=None, args=None):
        """
        Handler for weather module.
        """
        if args is None:
            # This is the getter logic
            try:
                userdata = self.db_cur.execute("SELECT temp_type,location,forecast_type FROM weather WHERE userid=(?)", 
                    (userid,))
                return userdata.fetchone()
            except TypeError:
                raise IDNotFoundError
        else:
            # This is the setter logic
            if userid is None:
                # This means that the user and entry are brand-new
                uid = self._get_userid(user)

                self.db_cur.execute("INSERT INTO weather VALUES (?, ?, ?, ?)", 
                    (uid, args[0], args[1], args[2]))
            else:
                # This means just the entry is brand-new, but that the user already
                # exists in the Users table.
                try:
                    # We first test whether the userid is already in the table,
                    # and, if so, we update the entry.
                    testresult = self.db_cur.execute("SELECT userid FROM weather WHERE userid=(?)", 
                        (userid,))
                    testresult.fetchone()
                    self.db_cur.execute("UPDATE weather SET temp_type=(?), location=(?), forecast_type=(?) WHERE userid=(?)",
                        (args[1], args[0], args[2], userid))
                except TypeError:
                    # If the userid is not present in the table, we drop down here,
                    # and create an entrirely new row in the table for that user.
                    self.db_cur.execute("INSERT INTO weather VALUES (?, ?, ?, ?)", 
                        (userid, args[0], args[1], args[2]))
        return

class IDNotFoundError(Exception):
    pass