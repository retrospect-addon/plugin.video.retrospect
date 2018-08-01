#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons 
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a 
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/ 
# or send a letter to Creative Commons, 171 Second Street, Suite 300, 
# San Francisco, California 94105, USA.
#===============================================================================
import StringIO
import httplib


class CachedHttpResponse(StringIO.StringIO):
    """ An class similar to an urllib2.Response object for cached responses."""

    def __init__(self, url, headerValue, bodyValue, code=200, doProcessing=True):
        """ initialises a new CachedHttpResponse instance 
        
        Arguments:
        url          : String - The URL from which the data comes
        headerValue  : String - The header data that should be cached
        bodyValue    : String - The body value that should be cached
            
        Keyword Arguments:
        code         : Integer - The HTTP return code
        doProcessing : Boolean - [optional] If set to True, cache values are extracted. 
                                 Defaults to True. Use for creating a simple httpresponse
                                 in case a complex one failed.
            
        """

        # noinspection PyTypeChecker
        StringIO.StringIO.__init__(self, bodyValue)

        self.url = url
        self.headerValue = headerValue
        self.bodyValue = bodyValue
        
        # cached responses are always OK
        self.code = code
        self.msg = "OK"
        
        # now we set the header value as StringIO
        self.headers = httplib.HTTPMessage(StringIO.StringIO(headerValue))
            
        if doProcessing:
            self.cacheParameters = self.__ExtractCachHeader(self.headers)        

    def info(self):
        """ Returns headers """
        
        return self.headers

    def geturl(self):
        """ Returns original URL """
        
        return self.url
    
    def SetCachFlag(self, flag, value=True):
        """ Sets additional flags to the Headers 
        
        Arguments: 
        flag  : String - Name of the header attribute
        
        Keyword Arguments:
        value : Object - The value to store. Eventually it will be stored as 
                         an String.
                          
        """
        
        #headerBuffer = "%s%s: True\r\n" % (self.headerValue, flag)
        #print headerBuffer
        self.headers[flag] = str(value)
        self.headers = httplib.HTTPMessage(StringIO.StringIO(str(self.headers)))
        return
    
    def __str__(self):
        """ Returns a text representation of the response """
        return "CachedHttpResponse with status %s (%s) for %s\nCache-Parameters: %s" % (self.code, self.msg, self.url, self.cacheParameters)
    
    def __ExtractCachHeader(self, headers):
        """ Extracts the "Cache-Control" header field and returns it's values
        as a dictionary. 
        
        Arguments
        headers : HTTPHeaders - The headers of a HTTP request/response
        
        Returns a dictionary with the Cache-Control parameters. If a parameter
        does not have a value, the value True is used as in general the 
        availability of a parameter means it is valid.
        
        """
        
        cacheParams = dict()
                
        if "cache-control" in headers:
            headerLine = headers['cache-control']
            for entry in headerLine.strip().split(","):
                #self.__Log("Found Cache Key: '%s'", entry.strip())
                if entry.find("=") > 0:
                    (key, value) = entry.split("=")
                    try:
                        cacheParams[key.strip().lower()] = int(value.strip())
                    except ValueError:
                        cacheParams[key.strip().lower()] = True
                else:
                    cacheParams[entry.strip().lower()] = True
        
        if "etag" in headers:
            #self.__Log("Found Cache Key: '%s'", entry.strip())
            if len(cacheParams) == 0:
                # only an e-tag is present, we should make it stale after some time, less then the 3600 seconds
                cacheParams['max-age'] = 60
                cacheParams['must-revalidate'] = True
            cacheParams['etag'] = headers['etag']

        return cacheParams
