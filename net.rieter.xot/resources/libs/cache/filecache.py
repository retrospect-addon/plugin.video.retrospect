#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import os
import datetime
import threading

# lock object to use.
cacheLock = threading.RLock()


def LockedReadWrite(origfunc):
    """ Decorator to execute function with a lock to prevent threading issues. """

    def ExecuteLocked(*args, **kwargs):
        """ The method that is called when the Decorator is executed.

        Arguments:
        *args     : List[Object] - A list of arguments that will be used to
                                   substitute parameters in the message.

        Keyword Arguments:
        **kwargs  : Dictionary   - List of additional keyword arguments. Possible
                                   values are: "error = True"

        """

        cacheLock.acquire()
        try:
            return origfunc(*args, **kwargs)
        finally:
            cacheLock.release()

    return ExecuteLocked


class FileCache:
    """ Cache object that caches data on a file system. """

    def __init__(self, cachePath, maxExpiredTime=3600, logger=None):
        """ Initialise the FileCache

        Arguments:
        cachePath : String - Path were the cache will be stored.

        Keyword Arguments:
        maxExpiredTime : Integer - The number of seconds a cached item will be
                                   valid. Defaults to 3600 seconds (1 hour).
        logger         : Logger  - The logger to use to log to. If the logger
                                   is not provided then a default "print" is
                                   done.

        Returns nothing.

        """

        # Set the logger.
        self.__logger = logger

        # Set the maximum expiration time.
        self.__Log("Setting ExpireTimeout to '%s'", maxExpiredTime)
        self.maxExpiredTime = maxExpiredTime

        # Create the path were the cache files are stored.
        self.__Log("Setting CachePath to '%s'", cachePath)
        if not os.path.exists(cachePath):
            os.makedirs(cachePath)
        self.cachePath = cachePath
        self.__CleanUpCache()

        return

    @LockedReadWrite
    def Set(self, key, value):
        """ Sets a cache value

        Arguments:
        key   : String - The key to store the cache.
        value : String - The value to store into the cache.

        """

        fileHandle = file(self.__GetFilePath(key), "wb")
        fileHandle.write(str(value))
        fileHandle.close()
        return

    @LockedReadWrite
    def Get(self, key):
        """ Returns the value corresponding to the given key

        Arguments:
        key : String - The key to use to retrieve the cache.

        Returns the cached value.

        """

        if self.HasKey(key):
            fileHandle = file(self.__GetFilePath(key), "rb")
            content = fileHandle.read()
            fileHandle.close()
        else:
            content = None
        return content

    def IsExpired(self, key, seconds, log=True):
        """ Checks if the cache value corresponding to the given key is expired.

        Arguments:
        key     : String  - The key to use to check the cache values
        seconds : Integer - The number of seconds request is considered actual.

        Keyword Arguments:
        log     : Boolean - Indicates if we need to log.

        If seconds > self.maxExpiredTime then the self.maxExpiredTime is used.

        Returns True or False.

        """

        if not self.HasKey(key):
            return True

        # determine the seconds to add
        expireSeconds = min(seconds, self.maxExpiredTime)
        storeTime = datetime.datetime.fromtimestamp(os.path.getmtime(self.__GetFilePath(key)))
        # validUntil = datetime.datetime.fromtimestamp(os.path.getmtime(self.__GetFilePath(key)) + expireSeconds)
        validUntil = storeTime + datetime.timedelta(seconds=expireSeconds)

        if log:
            self.__Log("%s (%s) vs %s", storeTime, validUntil, datetime.datetime.now())
        if validUntil > datetime.datetime.now():
            return False
        else:
            return True

    def HasKey(self, key):
        """ Returns if a key is present (expired or not) in the cache.

        Arguments:
        key     : String  - The key to use to check the cache values

        Returns True or False

        """

        return os.path.exists(self.__GetFilePath(key))

    @LockedReadWrite
    def Remove(self, key):
        """ removes a cached item from the cache.

        Arguments:
        key     : String  - The key of the cache value to delete from the cache.

        """

        if self.HasKey(key):
            os.remove(self.__GetFilePath(key))
        return

    @LockedReadWrite
    def __CleanUpCache(self, detailLog=False):
        """ Cleans the cache """

        self.__Log("Cleaning up cache")
        count = 0
        for key in os.listdir(self.cachePath):
            if self.IsExpired(key, self.maxExpiredTime, log=False):
                if detailLog:
                    self.__Log("Cleaning up: %s", key)
                self.Remove(key)
                count += 1
        self.__Log("Clean up %s items in the HTTP FileCache", count)

    def __Log(self, message, *args, **kwargs):
        """ Used to log a debug message. Message will be passed on to active
        logger.

        Arguments:
        message   : String       - The message to log
        *args     : List[Object] - A list of arguments that will be used to
                                   substitute parameters in the message.

        Keyword Arguments:
        **kwargs  : Dictionary   - List of additional keyword arguments.

        """

        message = "FileCache :: %s" % (message,)
        if self.__logger:
            self.__logger.Debug(message, *args, **kwargs)
        else:
            print message % args

    def __GetFilePath(self, key):
        """ Converts a cache Key into a filepath value."""

        return os.path.join(self.cachePath, key)

    def __str__(self):
        """ Returns a string representation of the cache object and it's
        content.

        """

        return "\n".join(os.listdir(self.cachePath))
