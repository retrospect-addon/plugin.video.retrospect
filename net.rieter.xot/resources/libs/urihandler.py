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

            handler = _RequestsHandler(
                cache_dir=cacheDir, web_time_out=webTimeOut, cookie_jar=cookieJar,
                ignore_ssl_errors=ignoreSslErrors
            )

            UriHandler.__handler = handler
            Logger.info("Initialised: %s", handler)
        else:
            Logger.info("Re-using existing UriHandler: %s", UriHandler.__handler)
        return UriHandler.__handler

    @staticmethod
    def Instance():
        """ return the logger instance """
        return UriHandler.__handler

    @staticmethod
    def Download(uri, filename, folder, progressCallback=None, proxy=None,
                 params=None, data=None, json=None, referer=None, additionalHeaders=None):
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
                                                        function(retrievedSize, totalSize, perc, completed, status)
        @rtype : The full path of the downloaded file.

        """

        return UriHandler.Instance().download(uri, filename, folder, progressCallback, proxy,
                                              params, data, json, referer, additionalHeaders)

    @staticmethod
    def Open(uri, proxy=None, params=None, data=None, json=None,
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

        return UriHandler.Instance().open(uri, proxy, params, data, json,
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

        return UriHandler.Instance().header(uri, proxy, referer,
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

        Logger.debug("Setting a cookie with this data:\n"
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
            Logger.trace("Found cookie '%s'", cookies[0].name)
            return cookies[0]

    # noinspection PyProtectedMember,PyTypeChecker
    @staticmethod
    def delete_cookie(name=None, domain=None):
        cookie_jar = UriHandler.Instance().cookieJar
        if domain not in cookie_jar._cookies:
            Logger.debug("No cookies were found for '%s'", domain)
            return

        if name is None:
            cookie_jar.clear(domain=domain)
        else:
            cookie_jar.clear(name=name, domain=domain)

        if UriHandler.Instance().cookieJarFile:
            cookie_jar.save()

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


class _RequestsHandler(object):

    def __init__(self, cache_dir=None, web_time_out=30, cookie_jar=None,
                 ignore_ssl_errors=False):
        """Initialises the UriHandler class

        Keyword Arguments:
        @param cache_dir:         string  - a path for http caching. If specified, caching will be used.
        @param web_time_out:      integer - timeout for requests in seconds
        @param cookie_jar:        string  - the path to the cookie jar (in case of file storage)

        """

        self.id = int(time.time())

        if cookie_jar:
            self.cookieJar = cookielib.MozillaCookieJar(cookie_jar)
            if not os.path.isfile(cookie_jar):
                self.cookieJar.save()
            self.cookieJar.load()
            self.cookieJarFile = True
        else:
            self.cookieJar = cookielib.CookieJar()
            self.cookieJarFile = False

        self.cacheDir = cache_dir
        self.cacheStore = None
        if cache_dir:
            self.cacheStore = StreamCache(cache_dir)
            Logger.debug("Opened %s", self.cacheStore)
        else:
            Logger.debug("No cache-store provided. Cached disabled.")

        self.userAgent = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)"
        self.webTimeOut = web_time_out                # max duration of request
        self.ignoreSslErrors = ignore_ssl_errors      # ignore SSL errors
        if self.ignoreSslErrors:
            Logger.warning("Ignoring all SSL errors in Python")

        # status of the most recent call
        self.status = UriStatus(code=0, url=None, error=False, reason=None)

        # for download animation
        self.__animationIndex = -1

    def download(self, uri, filename, folder, progress_callback=None, proxy=None, params="",
                 data="", json="", referer=None, additional_headers=None):
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
        @param additional_headers:  - [opt] dict      - the optional headers
        @param progress_callback:   - Function        - the callback for progress update. The format is
                                                        function(retrievedSize, totalSize, perc, completed, status)

        @rtype : The full path of the downloaded file.

        """

        if not folder or not filename:
            raise ValueError("Destination folder and filename should be specified")
        if not os.path.isdir(folder):
            raise ValueError("Destination folder is not a valid location")
        if not progress_callback:
            raise ValueError("A callback must be specified")

        download_path = os.path.join(folder, filename)
        if os.path.isfile(download_path):
            Logger.info("Url already downloaded to: %s", download_path)
            return download_path

        Logger.info("Creating Downloader for url '%s' to filename '%s'", uri, download_path)
        r = self.__requests(uri, proxy=proxy, params=params, data=data, json=json,
                            referer=referer, additional_headers=additional_headers,
                            no_cache=True, stream=True)
        if r is None:
            return ""

        retrieved_bytes = 0
        total_size = int(r.headers.get('Content-Length', '0').strip())
        chunk_size = 1024 if total_size == 0 else total_size / 100
        cancel = False
        with open(download_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)
                retrieved_bytes += len(chunk)

                if progress_callback:
                    cancel = self.__do_progress_callback(progress_callback, retrieved_bytes, total_size, False)
                if cancel:
                    Logger.warning("Download of %s aborted", uri)
                    break

        if cancel:
            if os.path.isfile(download_path):
                Logger.info("Removing partial download: %s", download_path)
                os.remove(download_path)
            return ""

        if progress_callback:
            self.__do_progress_callback(progress_callback, retrieved_bytes, total_size, True)
        return download_path

    def open(self, uri, proxy=None, params=None, data=None, json=None,
             referer=None, additionalHeaders=None, noCache=False):

        r = self.__requests(uri, proxy=proxy, params=params, data=data, json=json,
                            referer=referer, additional_headers=additionalHeaders,
                            no_cache=noCache, stream=False)
        if r is None:
            return ""

        if r.encoding == 'ISO-8859-1' and "text" in r.headers.get("content-type", ""):
            # Requests defaults to ISO-8859-1 for all text content that does not specify an encoding
            Logger.debug("Found 'ISO-8859-1' for 'text' content-type. Using UTF-8 instead.")
            r.encoding = 'utf-8'

        return r.text if r.encoding else r.content

    def header(self, uri, proxy=None, referer=None, additional_headers=None):
        s = requests.session()
        s.cookies = self.cookieJar
        s.verify = not self.ignoreSslErrors

        proxies = self.__get_proxies(proxy, uri)
        headers = self.__get_headers(referer, additional_headers)

        Logger.info("Performing a HEAD for %s", uri)
        r = s.head(uri, proxies=proxies, headers=headers, allow_redirects=True,
                   timeout=self.webTimeOut)

        content_type = r.headers.get("Content-Type", "")
        real_url = r.url

        self.status = UriStatus(code=r.status_code, url=uri, error=not r.ok, reason=r.reason)
        if self.cookieJarFile:
            # noinspection PyUnresolvedReferences
            self.cookieJar.save()

        if r.ok:
            Logger.info("%s resulted in '%s %s' (%s) for %s",
                        r.request.method, r.status_code, r.reason, r.elapsed, r.url)
            return content_type, real_url
        else:
            Logger.error("%s failed with in '%s %s' (%s) for %s",
                         r.request.method, r.status_code, r.reason, r.elapsed, r.url)
            return "", ""

    # noinspection PyUnusedLocal
    def __requests(self, uri, proxy, params, data, json, referer,
                   additional_headers, no_cache, stream):

        s = requests.session()
        s.cookies = self.cookieJar
        s.verify = not self.ignoreSslErrors
        if self.cacheStore and not no_cache:
            Logger.trace("Adding the %s to the request", self.cacheStore)
            s.mount("https://", CacheHTTPAdapter(self.cacheStore))
            s.mount("http://", CacheHTTPAdapter(self.cacheStore))

        proxies = self.__get_proxies(proxy, uri)
        if proxies is not None and "dns" in proxies:
            s.mount("https://", DnsResolverHTTPAdapter(uri, proxies["dns"],
                                                       logger=Logger.instance()))

        headers = self.__get_headers(referer, additional_headers)

        if params is not None:
            # Old UriHandler behaviour. Set form header to keep compatible
            if "content-type" not in headers:
                headers["content-type"] = "application/x-www-form-urlencoded"

            Logger.info("Performing a POST with '%s' for %s", headers["content-type"], uri)
            r = s.post(uri, data=params, proxies=proxies, headers=headers,
                       stream=stream, timeout=self.webTimeOut)
        elif data is not None:
            # Normal Requests compatible data object
            Logger.info("Performing a POST with '%s' for %s", headers.get("content-type", "<No Content-Type>"), uri)
            r = s.post(uri, data=data, proxies=proxies, headers=headers,
                       stream=stream, timeout=self.webTimeOut)
        elif json is not None:
            Logger.info("Performing a json POST with '%s' for %s", headers.get("content-type", "<No Content-Type>"), uri)
            r = s.post(uri, json=json, proxies=proxies, headers=headers,
                       stream=stream, timeout=self.webTimeOut)
        else:
            Logger.info("Performing a GET for %s", uri)
            r = s.get(uri, proxies=proxies, headers=headers,
                      stream=stream, timeout=self.webTimeOut)

        if r.ok:
            Logger.info("%s resulted in '%s %s' (%s) for %s",
                        r.request.method, r.status_code, r.reason, r.elapsed, r.url)
        else:
            Logger.error("%s failed with '%s %s' (%s) for %s",
                         r.request.method, r.status_code, r.reason, r.elapsed, r.url)

        self.status = UriStatus(code=r.status_code, url=r.url, error=not r.ok, reason=r.reason)
        if self.cookieJarFile:
            # noinspection PyUnresolvedReferences
            self.cookieJar.save()
        return r

    def __get_headers(self, referer, additional_headers):
        headers = {}
        if additional_headers:
            for k, v in additional_headers.iteritems():
                headers[k.lower()] = v

        if "user-agent" not in headers:
            headers["user-agent"] = self.userAgent
        if referer and "referer" not in headers:
            headers["referer"] = referer

        return headers

    def __get_proxies(self, proxy, url):
        if proxy is None:
            return None

        elif not proxy.UseProxyForUrl(url):
            Logger.debug("Not using proxy due to filter mismatch")

        elif proxy.Scheme == "http":
            Logger.debug("Using a http(s) %s", proxy)
            proxy_address = proxy.GetProxyAddress()
            return {"http": proxy_address, "https": proxy_address}

        elif proxy.Scheme == "dns":
            Logger.debug("Using a DNS %s", proxy)
            return {"dns": proxy.Proxy}

        Logger.warning("Unsupported Proxy Scheme: %s", proxy.Scheme)
        return None

    def __do_progress_callback(self, progress_callback, retrieved_size, total_size, completed):
        """ Performs a callback, if the progressCallback was specified.

        @param progress_callback:        The callback method
        @param retrieved_size:           Number of bytes retrieved
        @param total_size:               Total number of bytes
        @param completed:               Are we done?
        @rtype : Boolean                Should we cancel the download?

        """

        if progress_callback is None:
            # no callback so it was not cancelled
            return False

        # calculated some stuff
        self.__animationIndex = (self.__animationIndex + 1) % 4
        bytes_to_mb = 1048576
        animation_frames = ["-", "\\", "|", "/"]
        animation = animation_frames[self.__animationIndex]
        retrievedsize_mb = 1.0 * retrieved_size / bytes_to_mb
        totalsize_mb = 1.0 * total_size / bytes_to_mb
        if total_size > 0:
            percentage = 100.0 * retrieved_size / total_size
        else:
            percentage = 0
        status = '%s - %i%% (%.1f of %.1f MB)' % \
                 (animation, percentage, retrievedsize_mb, totalsize_mb)
        try:
            return progress_callback(retrieved_size, total_size, percentage, completed, status)
        except:
            Logger.error("Error in Progress Callback", exc_info=True)
            # cancel the download
            return True

    def __str__(self):
        return "UriHandler [id={0}, useCaching={1}, ignoreSslErrors={2}]"\
            .format(self.id, self.cacheStore, self.ignoreSslErrors)
