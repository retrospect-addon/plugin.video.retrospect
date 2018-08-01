#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons 
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a 
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California 94105, USA.
#===============================================================================

import datetime


class MemoryCache:
    """ Cache object that caches data in memory. A dictionary is used to cache
    the objects. If the script exits, the cache is lost! """
    
    def __init__(self, maxExpiredTime=3600, logger=None):
        """ Initialise the MemoryCache
        
        Keyword Arguments:
        maxExpiredTime : Integer - The number of seconds a cached item will be
                                   valid. Defaults to 3600 seconds (1 hour).
        logger         : Logger  - The logger to use to log to. If the logger 
                                   is not provided then a default "print" is 
                                   done.
        
        Returns nothing.
        
        """
        
        self.__cacheObject = dict()
        
        # Set the logger.
        self.__logger = logger
        
        # Set the maximum expiration time.
        self.__Log("Setting ExpireTimeout to '%s'", maxExpiredTime)
        self.maxExpiredTime = maxExpiredTime

        # Store the cache hit count
        self.cacheHits = 0

    def Set(self, key, value):
        """ Sets a cache value
        
        Arguments:
        key   : String - The key to store the cache.
        value : String - The value to store into the cache. 
        
        """
        
        self.__cacheObject[key] = (datetime.datetime.now(), value)
        
    def Get(self, key):
        """ Returns the value corresponding to the given key
        
        Arguments:
        key : String - The key to use to retrieve the cache.
        
        Returns the cached value.
        
        """
        
        if self.HasKey(key):
            return self.__cacheObject[key][1]
        else:
            return None
    
    def IsExpired(self, key, seconds):
        """ Checks if the cache value corresponding to the given key is expired.
        
        Arguments:
        key     : String  - The key to use to check the cache values
        seconds : Integer - The number of seconds request is considered actual.
        
        If seconds > self.maxExpiredTime then the self.maxExpiredTime is used.   
        
        Returns True or False.
        
        """
        
        if not self.HasKey(key):
            return True
        
        # determine the seconds to add
        expireSeconds = min(seconds, self.maxExpiredTime)
        storeTime = self.__cacheObject[key][0]
        validUntil = storeTime + datetime.timedelta(seconds=expireSeconds)
        
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
        
        return key in self.__cacheObject
    
    def Remove(self, key):
        """ removes a cached item from the cache.
        
        Arguments:
        key     : String  - The key of the cache value to delete from the cache.
        
        """
        
        self.__cacheObject.pop(key)
        return
    
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
        
        message = "MemoryCache :: %s" % (message,)
        if self.__logger:
            self.__logger.Debug(message, *args, **kwargs)
        else:
            print(message % args)

    def __str__(self):
        """ Returns a string representation of the cache object and it's 
        content.
                
        """
        
        return "\n".join(self.__cacheObject.keys())
