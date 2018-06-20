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
import urllib2
import cookielib
import httplib
import socket
import re
import time
import gzip
import zlib
import ssl
from cStringIO import StringIO
from httplib import IncompleteRead

from cache import filecache
from cache import cachehttphandler
from logger import Logger


# noinspection PyClassHasNoInit
class UriHandler:
    """Class that handles all the URL downloads"""

    __handler = None
    __error = "UriHandler not initialized. Use UriHandler.CreateUriHandler ======="

    @staticmethod
    def CreateUriHandler(cacheDir=None, useCompression=True, webTimeOut=30, maxFileNameLength=None,
                         blockSize=4096, cookieJar=None, ignoreSslErrors=False):
        """Initialises the UriHandler class

        Keyword Arguments:
        @param blockSize:         integer - The size of a download block.
        @param cacheDir:          string  - a path for http caching. If specified, caching will be used.
        @param useCompression:    boolean - Indicates whether compression is supported or not.
        @param webTimeOut:        integer - timeout for requests in seconds
        @param maxFileNameLength: integer - the max filename length (should be 42 on Xbox)
        @param cookieJar:         string  - the path to the cookie jar (in case of file storage)

        """

        # Only create a new handler if we did not have, or if the user options changed
        if UriHandler.__handler is None \
                or UriHandler.Instance().ignoreSslErrors != ignoreSslErrors:
            handler = UriHandler.CustomUriHandler(cacheDir, useCompression, webTimeOut,
                                                               maxFileNameLength, blockSize,
                                                               cookieJar, ignoreSslErrors)

            # hook up all the methods to pass to the actual UriHandler
            UriHandler.Download = handler.Download
            UriHandler.Open = handler.Open
            UriHandler.Header = handler.Header
            UriHandler.CookieCheck = handler.CookieCheck
            UriHandler.CookiePrint = handler.CookiePrint
            UriHandler.CorrectFileName = handler.CorrectFileName
            UriHandler.GetCookie = handler.GetCookie
            UriHandler.SetCookie = handler.SetCookie
            UriHandler.__handler = handler

            Logger.Info("Initialised: %s", handler)
        else:
            Logger.Info("Re-using existing UriHandler: %s", UriHandler.__handler)
        return UriHandler.__handler

    # In order for the PyDev errors to disappear, we create some fake methods here.

    @staticmethod
    def Instance():
        """ return the logger instance """
        return UriHandler.__handler

    @staticmethod
    def Download(uri, filename, folder, progressCallback, proxy=None, params="", referer=None, additionalHeaders=None):
        """Downloads an file

        Arguments
        @param uri:                 - String        - the URI to download
        @param filename:            - String        - the filename that should be used to store the file.

        Keyword Arguments:
        @param folder:              - [opt] string  - the folder to save to. If "" then a dialog is
                                                      presented to the user.
        @param progressCallback:    - Function      - the callback for progress update. The format is
                                                      function(retrievedSize, totalSize, perc, completed, status)
        @param proxy:               - [opt] string  - The address and port (proxy.address.ext:port) of
                                                      a proxy server that should be used.
        @param params:              - [opt] string  - data to send with the request (open(uri, params))
        @param referer:             - [opt] string  - the http referer to use
        @param additionalHeaders:   - [opt] dict    - the optional headers

        @rtype : The full path of the downloaded file.

        """
        pass

    @staticmethod
    def Open(uri, proxy=None, maxBytes=0, params="", referer=None, additionalHeaders=None, noCache=False, progressCallback=None):
        """Open an URL Async using a thread

        Arguments:
        uri      : string - the URI to download

        Arguments
        @param uri:                 - String        - the URI to download

        Keyword Arguments:
        @param progressCallback:    - Function      - the callback for progress update. The format is
                                                      function(retrievedSize, totalSize, perc, completed, status)
        @param proxy:               - [opt] string  - The address and port (proxy.address.ext:port) of
                                                      a proxy server that should be used.
        @param maxBytes:
        @param params:              - [opt] string  - data to send with the request (open(uri, params))
        @param referer:             - [opt] string  - the http referer to use
        @param additionalHeaders:   - [opt] dict    - the optional headers
        @param noCache:             - [opt] boolean - disables the cache

        @rtype : The data that was retrieved from the URI.

        """
        pass

    @staticmethod
    def Header(uri, proxy=None, params="", additionalHeaders=None, noCache=False):
        pass

    @staticmethod
    def SetCookie(version=0, name='', value='',
                  port=None,  # port_specified=False,
                  domain='',  # domain_specified=True,
                  domain_initial_dot=False,
                  path='/',  # path_specified=True,
                  secure=False,
                  expires=4102444555,
                  # discard=False,
                  # comment=None,
                  # comment_url=None,
                  # rest=None,
                  # rfc2109=False
                  ):
        # type: (int, str, str, str, str, bool, str, bool, int) -> cookielib.Cookie
        pass

    @staticmethod
    def GetCookie(name, domain, path="/", matchStart=False):
        # type: (str, str, str, bool) -> cookielib.Cookie
        pass

    @staticmethod
    def CookieCheck(cookieName):
        pass

    @staticmethod
    def CookiePrint():
        pass

    @staticmethod
    def CorrectFileName(filename):
        pass

    @staticmethod
    def GetExtensionFromUrl(url):
        """ determines the file extension for a certain URL

        Arguments:
        url: String - The URL to search

        Returns an extension or "" if not was found.

        """

        extensions = {".divx": "divx",
                      ".flv": "flv",
                      ".mp4": "mp4",
                      ".m4v": "mp4",
                      ".avi": "avi",
                      "h264": "mp4"}
        for ext in extensions:
            if url.find(ext) > 0:
                return extensions[ext]

        return ""

    class CustomUriHandler:
        """Class that handles all the URL downloads"""

        def __init__(self, cacheDir=None, useCompression=True, webTimeOut=30,
                     maxFileNameLength=None, blockSize=4096, cookieJar=None, ignoreSslErrors=False):
            """Initialises the UriHandler class

            Keyword Arguments:
            @param blockSize:         integer - the size of download blocks.
            @param maxFileNameLength: integer - the max filename length (should be 42 on Xbox)
            @param cacheDir:          string  - a path for http caching. If specified, caching will be used.
            @param useCompression:    boolean - Indicates whether compression is supported or not.
            @param webTimeOut:        integer - timeout for requests in seconds
            @param cookieJar:         string  - the path to the cookie jar (in case of file storage)

            """

            self.id = int(time.time())

            if cookieJar:
                self.cookieJar = cookielib.MozillaCookieJar(cookieJar)
                if not os.path.isfile(cookieJar):
                    # noinspection PyUnresolvedReferences
                    self.cookieJar.save()
                # noinspection PyUnresolvedReferences
                self.cookieJar.load()
                self.cookieJarFile = True
            else:
                self.cookieJar = cookielib.CookieJar()
                self.cookieJarFile = False

            # set caching stuff
            if cacheDir:
                cachePath = os.path.join(cacheDir, "www")
                self.cacheStore = filecache.FileCache(cachePath, logger=Logger.Instance())
            self.useCaching = cacheDir is not None
            self.useCompression = useCompression
            self.maxFileNameLength = maxFileNameLength

            self.blockSize = blockSize
            self.__bytesToMB = 1048576
            self.inValidCharacters = "[^a-zA-Z0-9!#$%&'()-.@\[\]^_`{}]"
            # self.timerTimeOut = 2.0                       # used for the emergency canceler

            self.webTimeOutInterval = webTimeOut            # max duration of request
            self.pollInterval = 0.1                         # time between polling of activity
            self.dnsCache = {"localhost": "127.0.0.1"}      # init with localhost

            self.ignoreSslErrors = ignoreSslErrors  # ignore SSL errors
            if self.ignoreSslErrors:
                Logger.Warning("Ignoring all SSL errors in Python")

        def Download(self, uri, filename, folder, progressCallback, proxy=None, params="", referer=None, additionalHeaders=None):
            """Downloads an file

            Arguments
            @param uri:                 - String        - the URI to download
            @param filename:            - String        - the filename that should be used to store the file.

            Keyword Arguments:
            @param folder:              - [opt] string  - the folder to save to. If "" then a dialog is
                                                          presented to the user.
            @param progressCallback:    - Function      - the callback for progress update. The format is
                                                          function(retrievedSize, totalSize, perc, completed, status)
            @param proxy:               - [opt] string  - The address and port (proxy.address.ext:port) of
                                                          a proxy server that should be used.
            @param params:              - [opt] string  - data to send with the request (open(uri, params))
            @param referer:             - [opt] string  - the http referer to use
            @param additionalHeaders:   - [opt] dict    - the optional headers

            @rtype : The full path of the downloaded file.

            """

            if not uri:
                raise ValueError("URI must be specified")
            if not folder or not filename:
                raise ValueError("Destination folder and filename should be specified")
            if not progressCallback:
                raise ValueError("A callback must be specified")

            destFilename = self.CorrectFileName(filename)
            destFolder = folder

            # if no destination is given, get one via a dialog box
            if not destFolder:
                raise ValueError("destination folder must be specified")

            destComplete = os.path.join(destFolder, destFilename)
            if os.path.exists(destComplete):
                Logger.Info("Url already downloaded to: %s", destComplete)
                return destComplete

            Logger.Info("Creating Downloader for url '%s' to filename '%s'", uri, destComplete)
            destHandle = open(destComplete, 'wb')
            error, canceled, charSet = self.__RetreiveData(destHandle, uri, 2147483648, progressCallback, proxy, 0,
                                                           params, referer, additionalHeaders, True, 32)
            destHandle.close()

            if error:
                return ""
            elif canceled:
                Logger.Info("Download Cancelled")
                if os.path.exists(destComplete):
                    Logger.Info("Removing partly downloaded item: %s", destComplete)
                    os.remove(destComplete)
                return ""
            else:
                return destComplete

        def Open(self, uri, proxy=None, maxBytes=0, params="", referer=None, additionalHeaders=None, noCache=False, progressCallback=None):
            """Open an URL Async using a thread

            Arguments:
            uri      : string - the URI to download

            Arguments
            @param uri:                 - String        - the URI to download

            Keyword Arguments:
            @param progressCallback:    - Function      - the callback for progress update. The format is
                                                          function(retrievedSize, totalSize, perc, completed, status)
            @param proxy:               - [opt] string  - The address and port (proxy.address.ext:port) of
                                                          a proxy server that should be used.
            @param maxBytes:
            @param params:              - [opt] string  - data to send with the request (open(uri, params))
            @param referer:             - [opt] string  - the http referer to use
            @param additionalHeaders:   - [opt] dict    - the optional headers
            @param noCache:             - [opt] boolean - disables the cache

            @rtype : The data that was retrieved from the URI.

            """

            destHandle = StringIO()
            error, canceled, charSet = self.__RetreiveData(destHandle, uri, self.webTimeOutInterval, progressCallback, proxy, maxBytes, params, referer, additionalHeaders, noCache)
            if error:
                return ""

            # no error
            data = destHandle.getvalue()

            # decode the data
            if charSet:
                Logger.Debug("Decoding data using charset HTML Header: %s", charSet)
                data = data.decode(charSet)
            return data

        def Header(self, uri, proxy=None, params="", referer=None, additionalHeaders=None, noCache=False):
            """Retrieves header information only

            Arguments:
            uri      : string - the URI to download

            Keyword Arguments:
            proxy  : [opt] string  - The address and port (proxy.address.ext:port) of
                                     a proxy server that should be used.
            params : [opt] string  - data to send with the request (open(uri, params))

            Returns:
            Data and the URL to which a redirect could have occurred.

            """

            Logger.Info("Retreiving Header info for %s", uri)
            # uri = uri
            # params = params

            if not uri:
                return "", ""

            try:
                if params == "":
                    uriHandle = self.__GetOpener(uri, proxy, disableCaching=noCache, headOnly=True, referer=referer,
                                                 additionalHeaders=additionalHeaders).open(uri)
                else:
                    uriHandle = self.__GetOpener(uri, proxy, disableCaching=noCache, headOnly=True, referer=referer,
                                                 additionalHeaders=additionalHeaders).open(uri, params)

                data = uriHandle.info()
                realUrl = uriHandle.geturl()
                data = data.get('Content-Type')
                uriHandle.close()
                Logger.Debug("Header info retreived: %s for realUrl %s", data, realUrl)
                return data, realUrl
            except:
                Logger.Critical("Header info not retreived", exc_info=True)
                return "", ""

        def SetCookie(self, version=0, name='', value='',
                      port=None,  # port_specified=False,
                      domain='',  # domain_specified=True,
                      domain_initial_dot=False,
                      path='/',  # path_specified=True,
                      secure=False,
                      expires=4102444555,
                      # discard=False,
                      # comment=None,
                      # comment_url=None,
                      # rest=None,
                      # rfc2109=False
                      ):
            # type: (int, str, str, str, str, bool, str, bool, int) -> cookielib.Cookie

            """ Sets a cookie in the UriHandler cookie jar

            @param version:             the cookie version
            @param name:                the name of the cookie
            @param value:               the value of the cookie
            @param port:                String representing a port or a set of ports (eg. '80', or '80,8080'), or None
            @param domain:              the domain for which the cookie should be valid
            @param domain_initial_dot:  if the domain explicitly specified by the server began with a dot ('.').
            @param path:                the path the cookie is valid for
            @param secure:              if cookie should only be returned over a secure connection
            @param expires:             Integer expiry date in seconds since epoch, or None.
            """

            Logger.Debug("Setting a cookie with this data:\n"
                         "name:   '%s'\n"
                         "value:  '%s'\n"
                         "domain: '%s'\n"
                         "path:   '%s'",
                         name, value, domain, path)
            c = cookielib.Cookie(version=version, name=name, value=value,
                                 port=port, port_specified=port is not None,
                                 domain=domain, domain_specified=domain is not None,
                                 domain_initial_dot=domain_initial_dot,
                                 path=path, path_specified=path is not None,
                                 secure=secure,
                                 expires=expires,
                                 discard=False,
                                 comment=None,
                                 comment_url=None,
                                 rest={'HttpOnly': None})  # rfc2109=False)
            # the rfc2109 parameters is not valid in Python 2.4 (Xbox), so we ommit it.
            self.cookieJar.set_cookie(c)
            return c

        # noinspection PyProtectedMember,PyTypeChecker
        def GetCookie(self, name, domain, path="/", matchStart=False):
            if domain not in self.cookieJar._cookies or path not in self.cookieJar._cookies[domain]:
                return None

            cookies = self.cookieJar._cookies[domain][path]
            if not matchStart:
                if name in cookies:
                    return cookies[name]
                return None

            # do a startswith search
            cookies = filter(lambda c: c.name.startswith(name), cookies.itervalues())
            if not cookies:
                return None
            else:
                return cookies[0]

        def CookieCheck(self, cookieName):
            """Checks if a cookie exists in the CookieJar

            Arguments:
            cookieName : string - the name of the cookie

            Returns:
            a boolean indicating whether the cookie existed or not.

            """

            retVal = False

            for cookie in self.cookieJar:
                if cookie.name == cookieName:
                    Logger.Debug("Found cookie: %s", cookie.name)
                    retVal = True
                    break

            return retVal

        def CookiePrint(self):
            """Prints out a list of registered cookies into the logfile"""

            cookies = "Content of the CookieJar:\n"
            for cookie in self.cookieJar:
                cookies = "%s%r\n" % (cookies, cookie)
                Logger.Trace("cookieName=%s; cookieValue=%s; expires:%s; domain: %s", cookie.name, cookie.value,
                             cookie.expires, cookie.domain)
            Logger.Debug(cookies.rstrip())
            return

        def GetDnsEntry(self, host):
            """ Retrieves a DNS entry from the DNS cache

            @param host: The hostname to resolve
            @return:     The IP address for the host if found in the cache, or the hostname, if no entry was found
                         in the cache.

            """

            ip = self.dnsCache.get(host, None)
            # ip = self.dnsCache.pop(host, None)
            if ip is not None:
                Logger.Debug("Found cached DNS address for host '%s': %s", host, ip)
                return ip

            Logger.Warning("Cound not find a cached DNS address for host: %s", host)
            return host

        def CorrectFileName(self, filename):
            """Corrects a filename to prevent XFAT issues and other folder issues

            Arguments:
            filename : string - the original filename

            Returns:
            a filename that is save for the the XFAT and other file systems.

            """
            original = filename

            # filter out the chars that are not allowed
            filename = re.sub(self.inValidCharacters, "", filename)

            # and check for length on Xbox
            if self.maxFileNameLength and len(filename) > self.maxFileNameLength:
                Logger.Debug("Making sure the file lenght does not exceed the maximum allowed on Xbox")
                (base, ext) = os.path.splitext(filename)
                baseLength = self.maxFileNameLength - len(ext)
                # regex = "^.{1,%s}" % (baseLength)
                # base = re.compile(regex).findall(base)[-1]

                if len(base) > baseLength:
                    base = base[0:baseLength - 1]

                filename = "%s%s" % (base, ext)

            Logger.Debug("Corrected from '%s' to '%s'", original, filename)
            return filename

        def __RetreiveData(self, destHandle, uri, timeOutValue, progressCallback=None, proxy=None, maxBytes=0,
                           params="", referer=None, additionalHeaders=None, noCache=False, blockMultiplier=1):
            """Open an URL Async using a thread

            Arguments:
            uri      : string - the URI to download

            Keyword Arguments:
            progressCallback : [opt] boolean - should a progress bar be shown
            proxy            : [opt] string  - The address and port (proxy.address.ext:port) of
                                               a proxy server that should be used.
            bytes            : [opt] integer - the number of bytes to get.
            params           : [opt] string  - data to send with the request (open(uri, params))
            headers          : [opt] dict    - a dictionary of additional headers

            Returns:
            The data that was retrieved from the URI.

            """

            # init parameters
            canceled = False
            timeOut = False
            error = False
            srcHandle = None
            blocksRead = 0
            fileSize = 0
            charSet = None
            blockSize = self.blockSize * blockMultiplier

            try:
                if uri == "":
                    return error, canceled, ""

                if uri.startswith("file:"):
                    index = uri.rfind("?")
                    #index = string.rfind(uri, "?")
                    if index > 0:
                        uri = uri[0:index]

                Logger.Info("Opening requested uri: %s (callback=%s, timeout=%s)",
                            uri, progressCallback is not None, timeOutValue)
                self.__DoCallback(progressCallback, 0, blockSize, 0, False)

                # set the start time in seconds
                startTime = time.time()

                # get an opener and handle
                opener = self.__GetOpener(uri, proxy,
                                          disableCaching=noCache,
                                          referer=referer,
                                          additionalHeaders=additionalHeaders)
                if params == '':
                    srcHandle = opener.open(uri)
                else:
                    srcHandle = opener.open(uri, params)

                # get some metadata
                Logger.Debug("Determining number of bytes to fetch")
                data = srcHandle.info()
                if data.get('Content-length'):
                    fileSize = int(data.get('Content-length'))
                    Logger.Debug('ByteSize is known (fileSize=' + str(fileSize) + ')')
                else:
                    fileSize = -1
                    Logger.Debug('ByteSize is unknown')

                # check for encoding
                charSet = None
                try:
                    contentType = data.get('Content-Type')
                    if contentType:
                        Logger.Trace("Found Content-Type header: %s", contentType)
                        charSetNeedle = 'charset='
                        charSetIndex = contentType.rfind(charSetNeedle)
                        if charSetIndex > 0:
                            charSetEndIndex = contentType.find(";", charSetIndex)
                            if charSetEndIndex > 0:
                                charSet = contentType[charSetIndex + len(charSetNeedle):charSetEndIndex]
                            else:
                                charSet = contentType[charSetIndex + len(charSetNeedle):]
                            Logger.Trace("Found Charset HTML Header: %s", charSet)
                except:
                    charSet = None

                blocksRead = 0
                while True:
                    block = srcHandle.read(blockSize)
                    if block == "":
                        break

                    destHandle.write(block)
                    blocksRead += 1

                    canceled = self.__DoCallback(progressCallback, blocksRead, blockSize, fileSize, False)
                    if canceled:
                        break

                    if time.time() > startTime + timeOutValue:
                        timeOut = True
                        break

                    if 0 < maxBytes < blocksRead * blockSize:
                        Logger.Info('Stopping download because Bytes > maxBytes')
                        break

                srcHandle.close()

            except (IncompleteRead, ValueError):
                # Python 2.6 throws a IncompleteRead on Chuncked data
                # Python 2.4 throws a ValueError on Chuncked data
                Logger.Error("IncompleteRead error opening url %s", uri)
                try:
                    if srcHandle:
                        srcHandle.close()
                except UnboundLocalError:
                    pass

            except:
                Logger.Critical("Error Opening url %s", uri, exc_info=True)
                error = True
                try:
                    if srcHandle:
                        srcHandle.close()
                except UnboundLocalError:
                    pass

            # we are finished now
            self.__DoCallback(progressCallback, blocksRead, blockSize, fileSize, True)

            if timeOut:
                Logger.Critical("The URL lookup did not respond within the TimeOut (%s s)", timeOutValue)
            elif canceled:
                Logger.Warning("Opening of %s was canceled", uri)
            elif not error:
                Logger.Info("Url %s was opened successfully", uri)

            if self.cookieJarFile:
                # noinspection PyUnresolvedReferences
                self.cookieJar.save()
            return error, canceled, charSet

        def __DoCallback(self, progressCallback, blocks, blockSize, totalSize, completed):
            """ Performs a callback, if the progressCallback was specified.

            @param progressCallback:
            @param blocks:
            @param blockSize:
            @param totalSize:
            @param completed:
            @rtype : Boolean

            """

            if progressCallback is None:
                # no callback so it was not cancelled
                return False

            # calculated some stuff
            animationFrames = ["-", "\\", "|", "/"]
            animation = animationFrames[blocks % 4]
            retrievedSize = blocks * blockSize
            retrievedsizeMB = 1.0 * retrievedSize / self.__bytesToMB
            totalsizeMB = 1.0 * totalSize / self.__bytesToMB
            if totalSize > 0:
                perc = 100.0 * retrievedSize / totalSize
            else:
                perc = 0
            status = '%s - %i%% (%.1f of %.1f MB)' % (animation, perc, retrievedsizeMB, totalsizeMB)
            try:
                return progressCallback(retrievedSize, totalSize, perc, completed, status)
            except:
                Logger.Error("Error in Progress Callback", exc_info=True)
                # cancel the download
                return True

        def __GetOpener(self, url, proxy=None, userAgent=None, headOnly=False, disableCaching=False, referer=None,
                        additionalHeaders=None, acceptCompression=True):
            """Get's a urllib2 URL opener with cookie jar

            Arguments:
            url               : string        - The URL to get an opener for

            Keyword Arguments:
            proxy             : [opt] string  - The address and port (proxy.address.ext:port) of
                                                a proxy server that should be used.
            headOnly          : [opt] boolean - Indication that only the header is needed.
            disableCaching    : [opt] boolean - Indication to disable the caching.
            referer           : [opt] string  - The referer URL
            additionalHeaders : [opt] dict    - A dictionary of additional headers

            Returns:
            An urllib2 OpenerDirector object for handling URL requests.

            """

            # create an empty dict, as it cannot be used as a default parameter
            # http://pythonconquerstheuniverse.wordpress.com/category/python-gotchas/
            if not additionalHeaders:
                additionalHeaders = dict()
            else:
                additionalHeaders = dict(additionalHeaders)

            headHandler = HttpHeadHandler()

            cacheHandler = None
            if self.useCaching:
                if disableCaching:
                    Logger.Info("Disabling caching for this request")
                else:
                    cacheHandler = cachehttphandler.CacheHttpHandler(self.cacheStore, logger=Logger.Instance())

            urlHandlers = [urllib2.HTTPCookieProcessor(self.cookieJar)]

            if self.ignoreSslErrors:
                Logger.Warning("Disabling SSL Verification for %s", url)
                # urlHandlers = [urllib2.HTTPCookieProcessor(self.cookieJar), HTTPSHandlerV3]
                # noinspection PyProtectedMember,PyTypeChecker
                urlHandlers.append(urllib2.HTTPSHandler(context=ssl._create_unverified_context()))

            if proxy is None:
                pass

            elif not proxy.UseProxyForUrl(url):
                Logger.Debug("Not using proxy due to filter mismatch")

            elif proxy.Scheme == "http":
                Logger.Debug("Using a http(s) %s", proxy)
                urlHandlers.append(proxy.GetSmartProxyHandler())
                # if there was an http scheme proxy, also add a https one as they will probably work
                if proxy.Scheme == "http":
                    urlHandlers.append(proxy.GetSmartProxyHandler("https"))

            elif proxy.Scheme == "dns":
                Logger.Debug("Using an alternative DNS %s", proxy)
                # noinspection PyTypeChecker
                urlHandlers.append(DnsHTTPHandler)
                # noinspection PyTypeChecker
                urlHandlers.append(DnsHTTPSHandler)

                # now we cache the DNS result
                resolver = DnsQuery(proxy.Proxy)
                host = resolver.GetHost(url)
                results = resolver.ResolveAddress(host)
                Logger.Debug("Resolved DNS %s to %s", host, results)
                result = resolver.ResolveAddress(host, (1,))[-1][1]
                # store it in the cache
                self.dnsCache[host] = result
                Logger.Debug("Cached DNS for %s to %s", host, result)

            # create the opener
            uriOpener = urllib2.build_opener(*urlHandlers)

            if headOnly:
                uriOpener.add_handler(headHandler)

            if "Content-Type" in additionalHeaders:
                uriOpener.add_handler(HttpContentTypeFixHandler(additionalHeaders["Content-Type"]))

            # add the compression handler before the cache in the
            # chain. That way we store decompressed data and save
            # cpu time.
            if acceptCompression and self.useCompression:
                compressionHandler = HttpCompressionHandler()
                uriOpener.add_handler(compressionHandler)

            if cacheHandler:
                uriOpener.add_handler(cacheHandler)

            # let's add some headers
            headers = []

            # change the user agent (thanks to VincePirez @ xbmc forums)
            Logger.Trace(additionalHeaders)
            if 'User-Agent' in additionalHeaders:
                Logger.Info("Using UserAgent from AdditionalHeaders: %s", additionalHeaders['User-Agent'])
            else:
                if userAgent is None:
                    user_agent = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)"
                else:
                    Logger.Info("Using custom UserAgent for url: %s", userAgent)
                    user_agent = userAgent
                # user_agent = "XOT/3.0 (compatible; XBMC; U)"
                # uriOpener.addheaders = [('User-Agent', user_agent)]
                # headers.append(('User-Agent', user_agent))
                additionalHeaders['User-Agent'] = user_agent

            # add the custom referer
            if referer is not None:
                Logger.Info("Adding custom Referer: '%s'", referer)
                headers.append(('referer', referer))

            # if additionalHeaders: -> there always is an user agent
            for header in additionalHeaders:
                headers.append((header, additionalHeaders[header]))

            uriOpener.addheaders = headers

            return uriOpener

        def __str__(self):
            return "UriHandler [id={0}, useCompression={1}, useCaching={2}, ignoreSslErrors={3}]"\
                .format(self.id, self.useCompression, self.useCaching, self.ignoreSslErrors)


class DnsHTTPConnection(httplib.HTTPConnection):
    def connect(self):
        """Connect to the host and port specified in __init__. But uses a custom DNS Lookup."""

        self.sock = socket.create_connection((UriHandler.Instance().GetDnsEntry(self.host), self.port), self.timeout)


class DnsHTTPSConnection(httplib.HTTPSConnection):
    def connect(self):
        """Connect to the host and port specified in __init__. But uses a custom DNS Lookup."""

        sock = socket.create_connection((UriHandler.Instance().GetDnsEntry(self.host), self.port), self.timeout)
        self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file)


class DnsHTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        """ Opens a HTTP request

        @param req: The request
        @return:    An Response
        """

        return self.do_open(DnsHTTPConnection, req)


class DnsHTTPSHandler(urllib2.HTTPSHandler):
    def https_open(self, req):
        """ Opens a HTTP request

        @param req: The request
        @return:    An Response
        """

        return self.do_open(DnsHTTPSConnection, req)


class HttpContentTypeFixHandler(urllib2.BaseHandler):
    def __init__(self, contentType):
        self.contentType = contentType
        return

    def default_open(self, request):
        """H andles requests and replaces the Content-Type: application/x-www-form-urlencoded in
        case we specifed a content-type in the headers

        Returns None
        """

        # just set the head
        Logger.Debug("Setting request content type: %s", self.contentType)
        # headers are .capitalize()-ed in the end
        request.add_unredirected_header("Content-type", self.contentType)
        # request.unredirected_hdrs.pop("Content-type", None)
        return None


class HttpHeadHandler(urllib2.BaseHandler):
    def __init__(self):
        return

    def default_open(self, request):
        """Handles GET requests. It check the cache and if a valid one is present
        returns that one if it is still valid. Is called before a request is
        actually done.

        Arguments:
        respone : urllib2.Request - The request that needs to be served.

        Returns None but sets the HEAD request

        """

        # just set the head
        Logger.Debug("Setting request type to HEAD.")
        request.get_method = lambda: 'HEAD'
        return None


class HttpCompressionHandler(urllib2.BaseHandler):
    def __init__(self):
        return

    def https_request(self, request):
        return self.http_request(request)

    def http_request(self, request):
        request.add_header("Accept-Encoding", "gzip, deflate")
        Logger.Debug("Adding header 'Accept-Encoding: %s'", "gzip, deflate")
        return request

    def https_response(self, request, response):
        return self.http_response(request, response)

    #noinspection PyUnusedLocal
    def http_response(self, request, response):  # @UnusedVariables
        Logger.Trace("Processing HTTP response for possible decompression")
        # Logger.Trace("%s\n%s", response.url, response.info())

        oldResponse = response
        # do the decompression
        contentEncoding = response.headers.get("content-encoding")
        if contentEncoding:
            responseEncoding = contentEncoding
            data = response.read()
            try:
                if "gzip" in contentEncoding:
                    Logger.Debug("Decompressing '%s' response", contentEncoding)
                    # the GzipFileReader expect a StringIO object
                    gzipStream = StringIO(data)
                    fileStream = gzip.GzipFile(fileobj=gzipStream)
                    responseEncoding = "none"

                elif "deflate" in contentEncoding:
                    Logger.Debug("Decompressing '%s' response", contentEncoding)
                    fileStream = StringIO(zlib.decompress(data))
                    responseEncoding = "none"

                elif contentEncoding == "none":
                    Logger.Debug("Nothing to decompress. Content-encoding: '%s'", contentEncoding)
                    # we have already used the response.read() so we need to create
                    # a new filestream with the original data in it.
                    fileStream = StringIO(data)

                else:
                    Logger.Warning("Unknown Content-Encoding: '%s'", contentEncoding)
                    # we have already used the response.read() so we need to create
                    # a new filestream with the original data in it.
                    fileStream = StringIO(data)
            except:
                Logger.Error("Cannot Decompress this response", exc_info=True)
                # we have already used the response.read() so we need to create
                # a new filestream with the original data in it.
                fileStream = StringIO(data)

            response = urllib2.addinfourl(fileStream, oldResponse.headers, oldResponse.url, oldResponse.code)
            response.msg = oldResponse.msg

            # Update the content-encoding header
            response.headers["content-encoding"] = responseEncoding
            return response
        else:
            Logger.Debug("No Content-Encoding header found")
            return oldResponse


class DnsQuery:
    def __init__(self, server):
        self.__server = server

    def GetHost(self, url):
        start = url.index("//")
        start += 2
        end = url.find("/", start)
        if end > 0:
            return url[start:end]
        else:
            return url[start:]

    def ResolveAddress(self, address, types=(1, )):
        s = socket.socket(type=socket.SOCK_DGRAM)
        q = self.__CreateRequest(address)
        s.settimeout(10.0)
        s.sendto(q, (self.__server, 53))
        r = s.recvfrom(1024)
        if types is None:
            return self.__ParseResponse(r[0])
        else:
            return filter(lambda (x, y): x in types, self.__ParseResponse(r[0]))

    def __CreateRequest(self, address):
        # noinspection PyListCreation
        q = []
        q.append("\x00\x01")  # sequence
        q.append("\x01\x00")  # standard request
        q.append("\x00\x01")  # questions
        q.append("\x00\x00")  # answer RRS
        q.append("\x00\x00")  # authority RRS
        q.append("\x00\x00")  # additional RRS

        # queryParts = ("alphabet", "rieter", "net")
        addressParts = address.split(".")
        for p in addressParts:
            q.append(chr(len(p)))
            q.append(p)
        q.append("\x00")
        q.append("\x00\x01")  # Type: A
        q.append("\x00\x01")  # Class: IN
        return "".join(q)

    # noinspection PyUnusedLocal
    def __ParseResponse(self, response):
        results = []
        reader = DnsQuery.__ByteStringReader(response)
        transactionId = reader.ReadInteger()
        flags = reader.ReadInteger()
        questions = reader.ReadInteger()
        answers = reader.ReadInteger()
        authority = reader.ReadInteger()
        additional = reader.ReadInteger()
        while True:
            length = reader.ReadInteger(1)
            if length == 0:
                break
            addressPart = reader.ReadString(length)
            # print addressPart
            continue
        dnsType = reader.ReadInteger()
        direction = reader.ReadInteger()

        for i in range(0, answers):
            name = reader.ReadFullString()
            # print "Name: %s" % (name,)

            answerType = reader.ReadInteger()
            direction = reader.ReadInteger()
            ttl = reader.ReadInteger(4)
            length = reader.ReadInteger()
            address = []
            if answerType == 1:
                for s in range(0, length):
                    address.append(str(reader.ReadInteger(1)))
                address = ".".join(address)
            elif answerType == 5:
                address = reader.ReadFullString()
            else:
                raise Exception("wrong type: %s" % (answerType, ))

            # print ip
            #print ip
            results.append((answerType, address))
        return results

    class __ByteStringReader:
        def __init__(self, byteString):
            self.__byteString = byteString
            self.__pointer = 0
            self.__resumePoint = 0
            # print "Input: %r" % (byteString, )

        def ReadInteger(self, length=2):
            val = self.ReadString(length)
            val = self.__ByteToInt(val)
            # print val
            return val

        def ReadFullString(self):
            value = ""
            while True:
                length = self.ReadInteger(1)
                if length == 0:
                    break
                elif length == 192:  # \xC0
                    # pointer found
                    newPointer = self.ReadInteger(1)
                    oldPointer = self.__pointer
                    self.__pointer = newPointer
                    value += self.ReadFullString()
                    self.__pointer = oldPointer
                    break
                value += self.ReadString(length)
                value += "."
                continue
            return value.strip('.')

        def ReadString(self, length):
            # print "from: %s to %s" % (self.__pointer, self.__pointer + length)
            val = self.__byteString[self.__pointer:self.__pointer + length]
            #print "Value %r" % (val, )
            self.__pointer += length
            return val

        def __ByteToInt(self, byteString):
            return int(byteString.encode('hex'), 16)


if __name__ == "__main__":
    logger = Logger.CreateLogger("c:\\temp\\www.log", "UriHandler Test", 0)

    # noinspection PyUnusedLocal
    def CallBack(retrievedsizeMB, totalsizeMB, perc, completed, status):
        """
        @param retrievedsizeMB:
        @param totalsizeMB:
        @param perc:
        @param completed:
        @param status:
        """
        print "%s - %s %s %s" % (status, totalsizeMB, retrievedsizeMB, perc)
        #if perc > 2:
        #    return True
        return False

    from proxyinfo import ProxyInfo
    p = ProxyInfo("8.8.8.8", 8888, "dns")
    p = ProxyInfo("185.37.37.37", 8888, "dns")    # http://unlocator.com/
    p = ProxyInfo("204.12.225.226", 8888, "dns")  # http://proxydns.co/
    p = ProxyInfo("127.0.0.1", 8888, "http")  # http://proxydns.co/

    from helpers.stopwatch import StopWatch
    s = StopWatch("Downloader", logger)

    d = DnsQuery("8.8.8.8")
    print d.GetHost("http://www.rieter.net/niks")

    # noinspection PyArgumentEqualDefault
    # handler = UriHandler.CreateUriHandler(cacheDir="c:\\temp\\cache\\", useCompression=True, webTimeOut=30, maxFileNameLength=None)
    handler = UriHandler.CreateUriHandler(useCompression=True, webTimeOut=30, maxFileNameLength=None)
    handler.SetCookie(name="test", domain=".google.com", value="test")
    handler.SetCookie(name="test2", domain=".google.com", value="test")
    s.Lap("Created")
    url = "https://www.google.com"
    # url = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/b043bpcn"
    # data = handler.Open("http://download.thinkbroadband.com/5MB.zip", progressCallback=CallBack, proxy=None, bytes=0, params="", referer=None, additionalHeaders=None, noCache=False)
    # data = handler.Download("http://www.google.nl/", "google.html", "c:\\temp", CallBack, proxy=p, params="", referer=None, additionalHeaders=None)
    # print data
    s.Lap("Downloaded")
    data = handler.Open(url, progressCallback=CallBack, proxy=p, maxBytes=0, params="", referer=None, additionalHeaders=None, noCache=False)
    s.Lap("Opened")
    cs = handler.GetCookie("test", ".google.com")
    if cs is None:
        raise Exception("Should not be null")
    cs = handler.GetCookie("test", ".google.com", matchStart=True)
    if cs is None:
        raise Exception("Should not be null")
    cs = handler.GetCookie("test", ".google.com", path='/test/')
    if cs is not None:
        raise Exception("Should not null")
    cs = handler.GetCookie("test3", ".google.com")
    if cs is not None:
        raise Exception("Should be null")
    print data
    logger.CloseLog()
