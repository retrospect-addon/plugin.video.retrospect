#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons 
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a 
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California 94105, USA.
#===============================================================================
from cachebase import CacheBase
from cachedhttpresponse import CachedHttpResponse


class CacheHandler(CacheBase):
    """ CacheHandler that can be used as a Decorative cache object.
    
    The @CacheHandler can be added on top of a URL opening method to
    automatically cache the output. The output must a CachedHttpResponse object.
    
    """
    
    def __init__(self, cacheObject=None, logger=None):
        """ Initiate an instance of the CacheHandler
        
        Keyword Arguments:
        cacheObject : CacheObject - Must be a FileCache or MemoryCache object, 
                                    or object with similar signature.   
        logger      : Logger      - A logger that will be used to log. If not 
                                    set a default "print" we be done.
        
        """
        
        # call the base class to initiate stuff
        CacheBase.__init__(self, logger) 
        
        # set the CacheObject
        self.__Log("Init cache handler decorator")
        self.__Log(cacheObject.__class__)
        if cacheObject is None:
            self.__cacheObject = dict()
        else:
            self.__cacheObject = cacheObject        
        return
    
    def __call__(self, wrappedFunction):
        """ Called only once to intiate the Wrapper. 
        
        wrappedFunction : function - The method that is wrapped and should be
                                     executed in the inner function.
        
        This method defines an __InnerWrapperFunction that will be called 
        instead of the actual method. That __InnerWrapperFunction is returned
        by __call__ so Python know what method to use. 
        
        Because the @CacheHandler has parameters, we need to do it this way. 
        for more information see this page:
        
        http://www.artima.com/weblogs/viewpost.jsp?thread=240845
        
        """
        
        self.__Log("Initialising CacheHandler decorator in Decorator.__call__()")
        
        def __InnerWrappedFunction(*args, **kwargs):
            """ The method that is called when the Decorator is executed.
        
            Arguments:
            *args     : List[Object] - A list of arguments that will be used to 
                                       substitute parameters in the message. 
            
            Keyword Arguments:
            **kwargs  : Dictionary   - List of additional keyword arguments. Possible
                                       values are: "error = True"
            
            """
            
            #self.__Log("=============================================")
            self.__Log("Executing CacheHandler Decorator Function(*args, **kwargs)")
            
            try:
                # find the parameters we need
                url = args[0]
                
                if "params" in kwargs:
                    params = kwargs["params"]
                else:
                    params = ""
                
                # now get the cache keys
                self.__Log("Url: '%s', Params: '%s'", url, params)
                (headerKey, bodyKey) = self._GetCacheKeys(url)
                
                # see if we have cache values (only if both keys are available and no POST parameters)
                if self.__cacheObject.HasKey(headerKey) and self.__cacheObject.HasKey(bodyKey) and params == "":
                    headerValue = self.__cacheObject.Get(headerKey)                                
                    bodyValue = self.__cacheObject.Get(bodyKey)
                    cachedResponse = CachedHttpResponse(url, headerValue, bodyValue)
                    self.__Log("Found a %s", cachedResponse)
                    
                    if not self._IsExpired(self.__cacheObject, headerKey, cachedResponse):                    
                        self.__Log("Cache-Hit")             
                        return cachedResponse

                    # it's difficult to set headers with a Decorator function. So we do not do this.                    
                    #elif self._MustRevalidate(cachedResponse):
                    #    # did it have a must re-validate? If so, it could still be OK. 
                    #    self.__Log("Stale-Cache hit found. Revalidating")
                    #    request.add_header("If-None-Match", cachedResponse.cacheParameters['etag'])                 
                    
                    else:
                        self.__Log("Expired Cache-Hit")
                else:
                    self.__Log("No-Cache-Hit")
            except:
                self.__Log("Error retrieving request from cache.", error=True, exc_info=True)
                
            # now call the real method and if needed cache the result.
            response = wrappedFunction(*args, **kwargs)
            self.__Log("After URL Fetch")
            
            try:
                # create a new response object to return
                headerValue = response.info()
                bodyValue = response.read()
                
                # it's difficult to set headers with a Decorator function. So we do not do this.                    
                #if response.code == 304:
                #    proLong = True                        
                #    bodyValue = self.__cacheObject.Get(bodyKey)
                #else:
                #    proLong = False                        
                #    bodyValue = response.read()
                
                # noinspection PyUnboundLocalVariable
                response = CachedHttpResponse(url, headerValue, bodyValue)
                self.__Log("Creating a %s", response)
                
                # it's difficult to set headers with a Decorator function. So we do not do this.                    
                #if proLong:
                #    self.__Log("304 Response found. Pro-Longing the %s", response)
                #else:
                #    self.__Log("Creating a %s", response)
                
                if not response.info() == "" and not response.read() == "" and self._ShouldBeCached(response):
                    self.__Log("Cacheable response found, Caching request for url: '%s'", url)
                    
                    # store both in the cache
                    # noinspection PyUnboundLocalVariable
                    self.__cacheObject.Set(headerKey, headerValue)
                    # noinspection PyUnboundLocalVariable
                    self.__cacheObject.Set(bodyKey, bodyValue)
                
            except:
                self.__Log("Error saving HTTP request into cache.", error=True, exc_info=True)
                
            return response
                    
        return __InnerWrappedFunction
    
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
        
        self._Log("CacheHandler", message, *args, **kwargs)
