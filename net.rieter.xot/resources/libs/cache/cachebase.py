#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
try:
    # noinspection PyCompatibility
    import hashlib
except:
    # noinspection PyDeprecation
    import md5


class CacheBase:
    """ Base class that is used for caching handlers. This class holds all the
    basic stuff that is needed for caching HTTP requests.

    """

    def __init__(self, logger=None):
        """ Initialise the class

        Keyword Arguments:
        logger : Logger - the logger to write to. If ommited a default "print"
                          will be done.

        """

        self.__logger = logger
        self._cacheHttps = True

    def _GetCacheKeys(self, url):
        """ Returns the names of the header and body cache keys.

        Arguments:
        url : String - The URL for which the cachekey should be generated.

        Returns a tupple (headerKey, bodyKey)

        """

        hashKey = self.__EncodeMD5(url)
        return "%s.header" % (hashKey,), "%s.body" % (hashKey,)

    def _IsCachableCode(self, code):
        """ Returns True if the HTTP code should be cached """

        return (200 <= code < 300) or code == 304

    def _ShouldBeCached(self, response, cachePrivate=True, inDoubtCache=True):
        """ Returns whether a response should be cached for further use. It uses
        the "cache-control" header value and the type of response (https/2xx status)
        to determine if a response should be cached.

        Arguments:
        response     : WebResponse - The response that might be cached.

        Keyword Arguments:
        cachePrivate : Boolean     - Also cache Private responses
        inDoubtCache : Boolean     - If no cache parameters were found, should we
                                     cache or not?

        Returns True or False

        These Cache-Control parameters are used:

        * max-age=[seconds] - specifies the maximum amount of time that an
        representation will be considered fresh. Similar to Expires, this
        directive is relative to the time of the request, rather than absolute.
        [seconds] is the number of seconds from the time of the request you wish
        the representation to be fresh for.

        * public - marks authenticated responses as cacheable; normally, if HTTP
        authentication is required, responses are automatically private.

        * private - allows caches that are specific to one user (e.g., in a
        browser) to store the response; shared caches (e.g., in a proxy) may
        not.

        * no-cache - forces caches to submit the request to the origin server for
        validation before releasing a cached copy, every time. This is useful to
        assure that authentication is respected (in combination with public), or
        to maintain rigid freshness, without sacrificing all of the benefits of
        caching.

        * no-store - instructs caches not to keep a copy of the representation
        under any conditions.

        * must-revalidate - tells caches that they must obey any freshness
        information you give them about a representation. HTTP allows caches to
        serve stale representations under special conditions; by specifying this
        header, you're telling the cache that you want it to strictly follow
        your rules.

        * proxy-revalidate - similar to must-revalidate, except that it only
        applies to proxy caches.

        """

        if response.code < 200 or response.code >= 300:
            self.__Log("CacheBase :: No 2xx response code. Not caching.")
            return False

        if response.url.startswith("https:") and not self._cacheHttps:
            self.__Log("HTTP response, but HTTPS. Not caching.")
            return False

        cacheParameters = response.cacheParameters
        if "no-cache" in cacheParameters or "no-store" in cacheParameters:
            self.__Log("CacheKey No-Cache or No-Store found. Not caching")
            return False

        # must revalidate means that you must revalidate after the cache became
        # stale. So after the cache expired.
        if "must-revalidate" in cacheParameters or "proxy-revalidate" in cacheParameters:
            self.__Log("CacheKey Must-Revalidate or proxy-revalidate found. Caching")
            return True

        if "private" in cacheParameters:
            if cachePrivate:
                self.__Log("CacheKey Private found. Caching because 'cachePrivate=%s'", cachePrivate)
            else:
                self.__Log("CacheKey Private found. Not Caching because 'cachePrivate=%s'", cachePrivate)
            return cachePrivate

        if "public" in cacheParameters:
            self.__Log("CacheKey Public found. Caching")
            return True

        if "max-age" in cacheParameters:
            self.__Log("Max-Age found (%s). Caching", cacheParameters['max-age'])
            return True

        if inDoubtCache:
            self.__Log("Unknown cache parameters. Let's just cache. %s", cacheParameters)
            return True
        else:
            self.__Log("Unknown cache parameters. Not Caching. %s", cacheParameters)
            return False

    def _Log(self, className, message, *args, **kwargs):
        """ Logs a debug message to the self.__logger object. The message is
        pre-pended by the ClassName.

        Arguments:
        className : String       - The name of the calling class
        message   : String       - The message to log
        *args     : List[Object] - A list of arguments that will be used to
                                   substitute parameters in the message.

        Keyword Arguments:
        **kwargs  : Dictionary   - List of additional keyword arguments. Possible
                                   values are: "error = True"

        Returns nothing.

        """

        error = "error"in kwargs

        message = "%s :: %s" % (className, message)
        if self.__logger:
            if error:
                self.__logger.Error(message, *args, **kwargs)
            else:
                self.__logger.Debug(message, *args, **kwargs)
        else:
            print message % args

    def _MustRevalidate(self, cachedResponse):
        """ Checks if a CachedResponse should be revalidated

        Arguments:
        cachedResponse : CachedHttpResponse - the response to check.

        If True is returned the response has a must-revalidate cache parameters
        and an ETAG.

        """

        hasMustRevalidate = "must-revalidate" in cachedResponse.cacheParameters or \
                            "proxy-revalidate" in cachedResponse.cacheParameters
        hasETag = "etag" in cachedResponse.cacheParameters
        return hasMustRevalidate and hasETag

    def _IsExpired(self, cacheObject, cacheKey, cachedResponse):
        """ Checks if a cacheKey and corresponding cachedReponse is expired. This
        one takes the Cache-Control 'max-age' into consideration. If that one is
        not present, 3600 seconds (1 hour) is used.

        Arguments:
        cacheObject    : CacheObject        - The object that holds the cache
        cacheKey       : String             - The cacheKey that is validated
        cachedResponse : CachedHttpResponse - The originally cached response, so not
                                              the to-be-cached response.

        The cachedResponse is only used to retrieve the 'max-age'. The CacheObject
        should not know what types of object it caches, so we cannot pass the
        the response object.

        Returns True or False

        """

        self.__Log("Verifying that the cache is not expired.")

        cacheParameters = cachedResponse.cacheParameters

        if 'max-age' in cacheParameters:
            return cacheObject.IsExpired(cacheKey, cacheParameters['max-age'])
        return cacheObject.IsExpired(cacheKey, 3600)

    def __Log(self, message, *args):
        """ Used to log a debug message. Message will be passed on to self._log
        with classname added.

        message   : String       - The message to log
        *args     : List[Object] - A list of arguments that will be used to
                                   substitute parameters in the message.
        """

        self._Log("CacheBase", message, *args)

#    def __ExtractCachHeader(self, headers):
#        """ Extracts the "Cache-Control" header field and returns it's values
#        as a dictionary.
#
#        Arguments
#        headers : HTTPHeaders - The headers of a HTTP request/response
#
#        Returns a dictionary with the Cache-Control parameters. If a parameter
#        does not have a value, the value True is used as in general the
#        availability of a parameter means it is valid.
#
#        """
#
#        cacheParams = dict()
#
#        if headers.has_key("cache-control"):
#            headerLine = headers['cache-control']
#            for entry in headerLine.strip().split(","):
#                self.__Log("Found Cache Key: '%s'", entry.strip())
#                if entry.find("=") > 0:
#                    (key, value) = entry.split("=")
#                    cacheParams[key.strip().lower()] = int(value.strip())
#                else:
#                    cacheParams[entry.strip().lower()] = True
#        return cacheParams

    def __EncodeMD5(self, data, toUpper=True):
        """Encodes the selected string into an MD5 hashTool.

        Arguments:
        data : string - data for which the MD5 should be calculated.

        Keyword Arguments:
        toUpper : [opt] boolean : result should be upper-case. (default: True)

        """

        try:
            hashTool = hashlib.md5()    # @UndefinedVariable
        except:
            # noinspection PyDeprecation
            hashTool = md5.new()

        hashTool.update(data)
        if toUpper:
            return hashTool.hexdigest().upper()
        else:
            return hashTool.hexdigest()
