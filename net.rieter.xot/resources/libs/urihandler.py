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
import cookielib
import time
from collections import namedtuple

import requests
import requests.cookies
import requests.utils

from connectivity.cachehttpadapter import CacheHTTPAdapter
from connectivity.dnshttpadapter import DnsResolverHTTPAdapter
from connectivity.streamcache import StreamCache
from logger import Logger

UriStatus = namedtuple('UriStatus', [
    'code',
    'reason',
    'url',
    'error'
])


class UriHandler(object):
    __handler = None
    __error = "UriHandler not initialized. Use UriHandler.CreateUriHandler ======="

    @staticmethod
    def CreateUriHandler(cacheDir=None, webTimeOut=30, cookieJar=None, ignoreSslErrors=False):
        """Initialises the UriHandler class

        Keyword Arguments:
        @param cacheDir:          string  - a path for http caching. If specified, caching will be used.
        @param webTimeOut:        integer - timeout for requests in seconds
        @param cookieJar:         string  - the path to the cookie jar (in case of file storage)

        """

        # Only create a new handler if we did not have, or if the user options changed
        if UriHandler.__handler is None or \
                UriHandler.Instance().ignoreSslErrors != ignoreSslErrors:

            handler = UriHandler.__RequestsHandler(
                cacheDir=cacheDir, webTimeOut=webTimeOut, cookieJar=cookieJar,
                ignoreSslErrors=ignoreSslErrors
            )

            UriHandler.__handler = handler
            Logger.Info("Initialised: %s", handler)
        else:
            Logger.Info("Re-using existing UriHandler: %s", UriHandler.__handler)
        return UriHandler.__handler

    @staticmethod
    def Instance():
        """ return the logger instance """
        return UriHandler.__handler

    @staticmethod
    def Download(uri, filename, folder, progressCallback=None, proxy=None,
                 params="", data="", json="", referer=None, additionalHeaders=None):
        """Downloads a remote file

        Arguments
        @param uri:                 - String        - the URI to download
        @param filename:            - String        - the filename that should be used to store the file.

        Keyword Arguments:
        @param params:              - [opt] string    - data to send with the request (open(uri, params))
        @param data:                - [opt] string    - data to send with the request (open(uri, data))
        @param json:                - [opt] dict      - json to send with the request (open(uri, params))
        @param proxy:               - [opt] ProxyInfo - The address and port (proxy.address.ext:port) of
                                                        a proxy server that should be used.
        @param referer:             - [opt] string    - the http referer to use
        @param additionalHeaders:   - [opt] dict      - the optional headers
        @param progressCallback:    - Function        - the callback for progress update. The format is

        @rtype : The full path of the downloaded file.

        """

        return UriHandler.Instance().Download(uri, filename, folder, progressCallback, proxy,
                                              params, data, json, referer, additionalHeaders)

    @staticmethod
    def Open(uri, proxy=None, params="", data="", json="",
             referer=None, additionalHeaders=None, noCache=False):
        """ Open an URL Async using a thread

        Arguments:
        uri      : string - the URI to download

        Arguments
        @param uri:                 - String          - the URI to download

        Keyword Arguments:
        @param params:              - [opt] string    - data to send with the request (open(uri, params))
        @param data:                - [opt] string    - data to send with the request (open(uri, data))
        @param json:                - [opt] dict      - json to send with the request (open(uri, params))
        @param proxy:               - [opt] ProxyInfo - The address and port (proxy.address.ext:port) of
                                                        a proxy server that should be used.
        @param referer:             - [opt] string    - the http referer to use
        @param additionalHeaders:   - [opt] dict      - the optional headers
        @param noCache:             - [opt] boolean   - disables the cache

        @return: The data that was retrieved from the URI.

        """

        return UriHandler.Instance().Open(uri, proxy, params, data, json,
                                          referer, additionalHeaders, noCache)

    @staticmethod
    def Header(uri, proxy=None, referer=None, additionalHeaders=None):
        # type: (str, object, str, dict) -> (object, str)
        """ Retrieves header information only

        Arguments:
        uri      : string - the URI to download

        Arguments
        @param uri:                 - String          - the URI to download

        Keyword Arguments:
        @param proxy:               - [opt] ProxyInfo - The address and port (proxy.address.ext:port) of
                                                        a proxy server that should be used.
        @param referer:             - [opt] string    - the http referer to use
        @param additionalHeaders:   - [opt] dict      - the optional headers

        Returns:
        Data and the URL to which a redirect could have occurred.

        """

        return UriHandler.Instance().Header(uri, proxy, referer,
                                            additionalHeaders)

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
        UriHandler.Instance().cookieJar.set_cookie(c)
        return c

    # noinspection PyProtectedMember,PyTypeChecker
    @staticmethod
    def GetCookie(name, domain, path="/", matchStart=False):
        # type: (str, str, str, bool) -> cookielib.Cookie
        if domain not in UriHandler.Instance().cookieJar._cookies or \
                path not in UriHandler.Instance().cookieJar._cookies[domain]:
            return None

        cookies = UriHandler.Instance().cookieJar._cookies[domain][path]
        if not matchStart:
            if name in cookies:
                return cookies[name]
            return None

        # do a startswith search
        cookies = filter(lambda c: c.name.startswith(name), cookies.itervalues())
        if not cookies:
            return None
        else:
            Logger.Trace("Found cookie '%s'", cookies[0].name)
            return cookies[0]

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

    class __RequestsHandler(object):

        def __init__(self, cacheDir=None, webTimeOut=30, cookieJar=None, ignoreSslErrors=False):
            """Initialises the UriHandler class

            Keyword Arguments:
            @param cacheDir:          string  - a path for http caching. If specified, caching will be used.
            @param webTimeOut:        integer - timeout for requests in seconds
            @param cookieJar:         string  - the path to the cookie jar (in case of file storage)

            """

            self.id = int(time.time())

            if cookieJar:
                self.cookieJar = cookielib.MozillaCookieJar(cookieJar)
                if not os.path.isfile(cookieJar):
                    self.cookieJar.save()
                self.cookieJar.load()
                self.cookieJarFile = True
            else:
                self.cookieJar = cookielib.CookieJar()
                self.cookieJarFile = False

            self.cacheDir = cacheDir
            self.cacheStore = None
            if cacheDir:
                self.cacheStore = StreamCache(cacheDir)
                Logger.Debug("Opened %s", self.cacheStore)
            else:
                Logger.Debug("No cache-store provided. Cached disabled.")

            self.userAgent = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)"
            self.webTimeOut = webTimeOut                # max duration of request
            self.ignoreSslErrors = ignoreSslErrors      # ignore SSL errors
            if self.ignoreSslErrors:
                Logger.Warning("Ignoring all SSL errors in Python")

            # status of the most recent call
            self.status = UriStatus(code=0, url=None, error=False, reason=None)

        def Download(self, uri, filename, folder, progressCallback=None, proxy=None, params="",
                     data="", json="", referer=None, additionalHeaders=None):
            """Downloads a remote file

            Arguments
            @param uri:                 - String        - the URI to download
            @param filename:            - String        - the filename that should be used to store the file.

            Keyword Arguments:
            @param params:              - [opt] string    - data to send with the request (open(uri, params))
            @param data:                - [opt] string    - data to send with the request (open(uri, data))
            @param json:                - [opt] dict      - json to send with the request (open(uri, params))
            @param proxy:               - [opt] ProxyInfo - The address and port (proxy.address.ext:port) of
                                                            a proxy server that should be used.
            @param referer:             - [opt] string    - the http referer to use
            @param additionalHeaders:   - [opt] dict      - the optional headers
            @param progressCallback:    - Function        - the callback for progress update. The format is

            @rtype : The full path of the downloaded file.

            """

            if not folder or not filename:
                raise ValueError("Destination folder and filename should be specified")
            if not os.path.isdir(folder):
                raise ValueError("Destination folder is not a valid location")
            if not progressCallback:
                raise ValueError("A callback must be specified")

            downloadPath = os.path.join(folder, filename)
            if os.path.isfile(downloadPath):
                Logger.Info("Url already downloaded to: %s", downloadPath)
                return downloadPath

            Logger.Info("Creating Downloader for url '%s' to filename '%s'", uri, downloadPath)
            r = self.__Requests(uri, proxy=proxy, params=params, data=data, json=json,
                                referer=referer, additionalHeaders=additionalHeaders,
                                noCache=True, stream=True)
            if r is None:
                return ""

            with open(downloadPath, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=128):
                    fd.write(chunk)
            return downloadPath

        def Open(self, uri, proxy=None, params="", data="", json="",
                 referer=None, additionalHeaders=None, noCache=False):

            r = self.__Requests(uri, proxy, params, data, json, referer, additionalHeaders, noCache)
            if r is None:
                return ""

            return r.text if r.encoding else r.content

        def Header(self, uri, proxy=None, referer=None, additionalHeaders=None):
            s = requests.session()
            s.cookies = self.cookieJar
            s.verify = not self.ignoreSslErrors

            proxies = self.__GetProxies(proxy, uri)
            headers = self.__GetHeaders(referer, additionalHeaders)

            Logger.Info("Performing a HEAD for %s", uri)
            r = s.head(uri, proxies=proxies, headers=headers, allow_redirects=True,
                       timeout=self.webTimeOut)

            contentType = r.headers.get("Content-Type", "")
            realUrl = r.url

            self.status = UriStatus(code=r.status_code, url=uri, error=not r.ok, reason=r.reason)
            if self.cookieJarFile:
                # noinspection PyUnresolvedReferences
                self.cookieJar.save()

            if r.ok:
                Logger.Info("%s resulted in '%s %s' (%s) for %s",
                            r.request.method, r.status_code, r.reason, r.elapsed, r.url)
                return contentType, realUrl
            else:
                Logger.Error("%s failed with in '%s %s' (%s) for %s",
                             r.request.method, r.status_code, r.reason, r.elapsed, r.url)
                return "", ""

        # noinspection PyUnusedLocal
        def __Requests(self, uri, proxy=None, params="", data="", json="",
                       referer=None, additionalHeaders=None, noCache=False,
                       progressCallback=None, stream=False):

            # TODO: add DNS proxy
            # TODO: callback

            s = requests.session()
            s.cookies = self.cookieJar
            s.verify = not self.ignoreSslErrors
            if self.cacheStore and not noCache:
                Logger.Trace("Adding the %s to the request", self.cacheStore)
                s.mount("https://", CacheHTTPAdapter(self.cacheStore))
                s.mount("http://", CacheHTTPAdapter(self.cacheStore))

            proxies = self.__GetProxies(proxy, uri)
            if proxies is not None and "dns" in proxies:
                s.mount("https://", DnsResolverHTTPAdapter(uri, proxies["dns"],
                                                           logger=Logger.Instance()))

            headers = self.__GetHeaders(referer, additionalHeaders)

            if params:
                # Old UriHandler behaviour. Set form header to keep compatible
                if "content-type" not in headers:
                    headers["content-type"] = "application/x-www-form-urlencoded"

                Logger.Info("Performing a POST with '%s' for %s", headers["content-type"], uri)
                r = s.post(uri, data=params, proxies=proxies, headers=headers,
                           stream=stream, timeout=self.webTimeOut)
            elif data:
                # Normal Requests compatible data object
                Logger.Info("Performing a POST with '%s' for %s", headers.get("content-type", "<No Content-Type>"), uri)
                r = s.post(uri, data=data, proxies=proxies, headers=headers,
                           stream=stream, timeout=self.webTimeOut)
            elif json:
                Logger.Info("Performing a json POST with '%s' for %s", headers.get("content-type", "<No Content-Type>"), uri)
                r = s.post(uri, json=json, proxies=proxies, headers=headers,
                           stream=stream, timeout=self.webTimeOut)
            else:
                Logger.Info("Performing a GET for %s", uri)
                r = s.get(uri, proxies=proxies, headers=headers,
                          stream=stream, timeout=self.webTimeOut)

            if r.ok:
                Logger.Info("%s resulted in '%s %s' (%s) for %s",
                            r.request.method, r.status_code, r.reason, r.elapsed, r.url)
            else:
                Logger.Error("%s failed with '%s %s' (%s) for %s",
                             r.request.method, r.status_code, r.reason, r.elapsed, r.url)

            self.status = UriStatus(code=r.status_code, url=r.url, error=not r.ok, reason=r.reason)
            if self.cookieJarFile:
                # noinspection PyUnresolvedReferences
                self.cookieJar.save()
            return r

        def __GetHeaders(self, referer, additionalHeaders):
            headers = {}
            if additionalHeaders:
                for k, v in additionalHeaders.iteritems():
                    headers[k.lower()] = v

            if "user-agent" not in headers:
                headers["user-agent"] = self.userAgent
            if referer and "referer" not in headers:
                headers["referer"] = referer

            return headers

        def __GetProxies(self, proxy, url):
            if proxy is None:
                return None

            elif not proxy.UseProxyForUrl(url):
                Logger.Debug("Not using proxy due to filter mismatch")

            elif proxy.Scheme == "http":
                Logger.Debug("Using a http(s) %s", proxy)
                proxyAddress = proxy.GetProxyAddress()
                return {"http": proxyAddress, "https": proxyAddress}

            elif proxy.Scheme == "dns":
                Logger.Debug("Using a DNS %s", proxy)
                return {"dns": proxy.Proxy}

            Logger.Warning("Unsupported Proxy Scheme: %s", proxy.Scheme)
            return None

        def __str__(self):
            return "UriHandler [id={0}, useCaching={1}, ignoreSslErrors={2}]"\
                .format(self.id, self.cacheStore, self.ignoreSslErrors)
