#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import urllib2

from cachedhttpresponse import CachedHttpResponse
from cachebase import CacheBase


class CacheHttpHandler(urllib2.BaseHandler, CacheBase):
    """ CacheHttpHandler class that can be used as an httphandler for
    urllib2.build_opener.

    """

    def __init__(self, cacheObject, logger=None):
        """ Initialises the CacheHttpHandler and sets the correct cacheObject.

        Arguments:
        cacheObject : CacheObject - Must be a FileCache or MemoryCache object,
                                    or object with similar signature.

        Keyword Arguments:
        logger      : Logger      - A logger that will be used to log. If not
                                    set a default "print" we be done.

        """

        # call the base class
        CacheBase.__init__(self, logger)

        if self._cacheHttps:
            self.https_response = self.http_response

        self.__cacheObject = cacheObject
        self.__cacheMarker = "X-local-cache"
        return

    def default_open(self, request):
        """Handles GET requests. It check the cache and if a valid one is present
        returns that one if it is still valid. Is called before a request is
        actually done.

        Arguments:
        respone : urllib2.Request - The request that needs to be served.

        Returns a CachedHttpResponse if a cached item is found or None if none is
        found.

        """

        # self.__Log("=============================================")

        url = request.get_full_url()
        self.__Log("HTTP request for url: '%s'", url)

        try:
            (headerKey, bodyKey) = self._GetCacheKeys(url)

            # self.__Log("======= %s", request.get_method())
            # Only cache GET methods.
            if not request.get_method() == "GET":
                # let the next handler try to process the request
                self.__Log("Not caching '%s' requests", request.get_method())
                return None

            # check if a cache response is available
            if self.__cacheObject.HasKey(headerKey) and self.__cacheObject.HasKey(bodyKey):
                # retrieve the values
                headerValue = self.__cacheObject.Get(headerKey)
                bodyValue = self.__cacheObject.Get(bodyKey)
                # and construct a CachedHttpResponse
                cachedResponse = CachedHttpResponse(url, headerValue, bodyValue)
                self.__Log("Found a %s", cachedResponse)

                if not self._IsExpired(self.__cacheObject, headerKey, cachedResponse):
                    # if the current request is not expired, it's a cache hit
                    self.__Log("Cache-Hit")
                    cachedResponse.SetCachFlag(self.__cacheMarker)
                    return cachedResponse

                elif self._MustRevalidate(cachedResponse):
                    # did it have a must re-validate? If so, it could still be OK.
                    self.__Log("Stale-Cache hit found. Revalidating")
                    request.add_header("If-None-Match", cachedResponse.cacheParameters['etag'])
                    return None

                else:
                    # the cache already expired, so it's not a cache hit.
                    self.__Log("Expired Cache-Hit")
                    return None
            else:
                self.__Log("No-Cache-Hit")
                return None
        except:
            # in case of an error, always return None so the next handler gets the request
            self.__Log("Error retrieving HTTP request from cache.", error=True, exc_info=True)
            return None

    def http_response(self, request, response):
        """ Is called after a response is found.

        Arguments:
        request  : urllib2.Request  - The request that was done
        response : urllib2.Response - The found response

        Returns the response that was passed as input

        """

        self.__Log("Processing HTTP response")

        url = headerValue = bodyValue = ""
        try:
            if request.get_method() == "GET" and self._IsCachableCode(response.code):
                # the request was a GET so we might need to cache
                info = response.info()

                # check if the response has the marker and is thus an already cached response.
                if self.__cacheMarker in info:
                    self.__Log("This response came from the cache! No further processing needed.")
                    return response

                url = request.get_full_url()

                # retrieve the keys to store in the cache
                (headerKey, bodyKey) = self._GetCacheKeys(url)

                headerValue = response.info()
                if response.code == 304:
                    bodyValue = self.__cacheObject.Get(bodyKey)
                    headerValue = self.__cacheObject.Get(headerKey)
                    response = CachedHttpResponse(url, headerValue, bodyValue)
                    self.__Log("304 Response found. Pro-Longing the %s", response)

                    # no need to continue, just return the value from the cache as
                    # it was still valid
                    return response
                else:
                    bodyValue = response.read()

                # create a new response object to return
                response = CachedHttpResponse(url, headerValue, bodyValue)
                self.__Log("Creating a %s", response)
                if self._ShouldBeCached(response):
                    self.__Log("Cacheable response found, Caching request for url: '%s'", url)

                    # store both in the cache
                    self.__cacheObject.Set(headerKey, headerValue)
                    self.__cacheObject.Set(bodyKey, bodyValue)
            else:
                self.__Log("Not a GET request or not-cachable HTTP code (%s).", response.code)
        except:
            self.__Log("Error saving HTTP request into cache.", error=True, exc_info=True)
            return CachedHttpResponse(url, headerValue, bodyValue, doProcessing=False)

        return response

    def __Log(self, message, *args, **kwargs):
        """ Used to log a debug message. Message will be passed on to self._log
        with classname added.

        Arguments:
        message   : String       - The message to log
        *args     : List[Object] - A list of arguments that will be used to
                                   substitute parameters in the message.

        Keyword Arguments:
        **kwargs  : Dictionary   - List of additional keyword arguments. Possible
                                   values are: "error = True"

        """

        self._Log("CacheHttpHandler", message, *args, **kwargs)
