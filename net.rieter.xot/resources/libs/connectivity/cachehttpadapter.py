import requests
import requests.cookies
import requests.utils
from requests.adapters import HTTPAdapter, DEFAULT_POOLSIZE, DEFAULT_RETRIES, DEFAULT_POOLBLOCK
from requests.structures import CaseInsensitiveDict

import json
import hashlib

from .streamcache import StreamCache
from logger import Logger


class CacheHTTPAdapter(HTTPAdapter):

    def __init__(self, cache_store, pool_connections=DEFAULT_POOLSIZE, pool_maxsize=DEFAULT_POOLSIZE,
                 max_retries=DEFAULT_RETRIES, pool_block=DEFAULT_POOLBLOCK):
        """ Creates a Caching HTTP Adapter for the Requests module.

        @param cache_store:
        @param pool_connections:
        @param pool_maxsize:
        @param max_retries:
        @param pool_block:
        """
        self.cache_store = cache_store        # type: StreamCache

        super(CacheHTTPAdapter, self).__init__(pool_connections, pool_maxsize, max_retries,
                                               pool_block)

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        try:
            if request.method == "GET":
                response = self.__get_cached_response(request)
                if response:
                    self.cache_store.cacheHits += 1
                    return response
        except:
            Logger.error("Error retrieving cache for %s", request.url, exc_info=True)

        # Actually send a request
        Logger.debug("Retrieving data from: %s", request.url)
        response = super(CacheHTTPAdapter, self).send(request, stream, timeout, verify, cert, proxies)

        try:
            # Cache it if it was a cacheable response
            cache_data = self.__extract_cache_data(response.headers)
            if self.__should_cache(response, cache_data):
                self.__store_response(request, response, cache_data)

            if response.status_code == 304:
                Logger.debug("304 Response found. Pro-Longing the %s", response.url)
                self.cache_store.cacheHits += 1
                response = self.__get_cached_response(request, no_check=True)
        except:
            Logger.error("Error storing cache for %s", request.url, exc_info=True)

        return response

    def __get_cached_response(self, req, no_check=False):
        body_key, meta_key = self.__get_cache_keys(req)
        if not self.cache_store.has_cache_key(meta_key) or not \
                self.cache_store.has_cache_key(body_key):
            Logger.debug("No-Cache-Hit: %s", req.url)
            return None

        with self.cache_store.get(meta_key) as fd:
            meta = json.load(fd)
        headers = CaseInsensitiveDict(data=meta["headers"])
        cache_data = meta.get("cache_data")

        resp = requests.Response()
        resp.url = meta.get("url", req.url)
        resp.raw = self.cache_store.get(body_key)
        resp.status_code = meta["status"]
        resp.reason = meta.get("reason")
        resp.headers = headers
        resp.encoding = meta["encoding"]
        resp.request = req

        if no_check:
            return resp

        # Determine the maximum age and then check if the cache if valid or not.
        Logger.trace("Cache-Data: %s", cache_data)
        valid_in_seconds = 3600
        if 'max-age' in cache_data:
            valid_in_seconds = cache_data['max-age']
        if self.cache_store.is_expired(meta_key, valid_in_seconds):
            Logger.debug("Expired Cache-Hit: %s", req.url)
            return None

        if self.__must_revalidate(cache_data):
            Logger.debug("Stale-Cache hit found. Revalidating")
            req.headers["If-None-Match"] = headers["etag"]
            return None

        Logger.debug("Cache-Hit: %s", req.url)
        return resp

    def __extract_cache_data(self, headers):
        cache_data = {}

        if "cache-control" in headers:
            cache_control = headers['cache-control']
            for entry in cache_control.strip().split(","):
                if entry.find("=") > 0:
                    (key, value) = entry.split("=")
                    try:
                        cache_data[key.strip().lower()] = int(value.strip())
                    except ValueError:
                        cache_data[key.strip().lower()] = True
                else:
                    cache_data[entry.strip().lower()] = True

        if "etag" in headers:
            # if len(cache_data) == 0:
            #     # only an e-tag is present, we should make it stale after some time, less then the 3600 seconds
            #     cache_data['max-age'] = 60
            #     cache_data['must-revalidate'] = True
            cache_data['etag'] = headers['etag']

        if cache_data:
            Logger.debug("Found cache-control and etag data: %s", cache_data)
        return cache_data

    def __should_cache(self, res, cache_data):
        # type: (requests.Response, dict) -> bool
        """ Returns whether a response should be cached for further use. It uses
        the "cache-control" header value and the type of response (https/2xx status)
        to determine if a response should be cached.

        Arguments:
        cache_data     : dict      - Cached data from the request

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

        if res.request.method != "GET":
            Logger.trace("Not a GET method. Not caching.")
            return False

        if res.status_code < 200 or res.status_code >= 300:
            Logger.trace("No 2xx response code. Not caching.")
            return False

        if "no-cache" in cache_data or "no-store" in cache_data:
            Logger.trace("CacheKey No-Cache or No-Store found. Not caching")
            return False

        # must revalidate means that you must revalidate after the cache became
        # stale. So after the cache expired.
        if "must-revalidate" in cache_data or "proxy-revalidate" in cache_data:
            Logger.trace("CacheKey Must-Revalidate or proxy-revalidate found. Caching")
            return True

        if "max-age" in cache_data:
            Logger.trace("Max-Age found (%s). Caching", cache_data['max-age'])
            return True

        Logger.trace("Unknown cache parameters. Let's just cache")
        return True

    def __store_response(self, req, res, cache_data):
        Logger.debug("Storing cache for: %s", res.url)
        body_key, meta_key = self.__get_cache_keys(req)

        # Store the body as a binary file and reset the raw and _content_consumed attributes
        # of the response so we can reuse it again
        with self.cache_store.set(body_key) as fp:
            for chunk in res.iter_content(chunk_size=128):
                fp.write(chunk)

        # we need to restore some original response protected members and the raw content. The
        # latter is an urllib3 response, but we can use an BytesIO as long as we add some required
        # stuff such as _original_response.
        original_response = None
        if hasattr(res.raw, '_original_response'):
            original_response = res.raw._original_response

        # set the raw content so we can use it again
        res.raw = self.cache_store.get(body_key)
        res._content_consumed = False
        if original_response:
            res.raw._original_response = original_response

        # store all headers and cache-data and store it in a json file
        data = {
            "body": body_key,
            "url": res.url,
            "headers": dict(
                (k, v) for k, v in res.headers.items()
            ),
            "status": res.status_code,
            "reason": res.reason,
            "encoding": res.encoding,
            "cache_data": cache_data
        }
        with self.cache_store.set(meta_key) as fp:
            json.dump(data, fp, encoding='utf-8', indent=2)
        Logger.trace(data)

        return

    def __must_revalidate(self, cache_data):
        """ Checks if a cached response should be revalidated

        Arguments:
        meta_data : dict - the response to check.

        If True is returned the response has a must-revalidate cache parameters
        and an ETAG.

        """

        # No cache data present, so no need to revalidate the thing.
        if not cache_data:
            Logger.trace("No cache data found for a cached request. No "
                         "need to revalidate as it's either expired or not.")
            return False

        # Only revalidate if we were told and if we have an etag
        # if "must-revalidate" in cache_data or "proxy-revalidate" in cache_data:
        #     if "etag" in cache_data:
        #         return True

        # always revalidate a etag as many sites don't provide the ....-revalidate option.
        if "etag" in cache_data:
            return True

        return False

    def __get_cache_keys(self, req):
        hash_tool = hashlib.md5()
        hash_tool.update(req.url)
        key = hash_tool.hexdigest()
        body_file = "{0}.body".format(key)
        meta_file = "{0}.meta".format(key)
        return body_file, meta_file

    # def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **pool_kwargs):
    #     Logger.Info("init_poolmanager")
    #     super(CacheHTTPAdapter, self).init_poolmanager(connections, maxsize, block, **pool_kwargs)

    # def proxy_manager_for(self, proxy, **proxy_kwargs):
    #     Logger.Info("proxy_manager_for")
    #     return super(CacheHTTPAdapter, self).proxy_manager_for(proxy, **proxy_kwargs)

    # def cert_verify(self, conn, url, verify, cert):
    #     Logger.Info("cert_verify")
    #     return super(CacheHTTPAdapter, self).cert_verify(conn, url, verify, cert)

    # def build_response(self, req, resp):
    #     Logger.Info("build_response")
    #     return super(CacheHTTPAdapter, self).build_response(req, resp)

    # def get_connection(self, url, proxies=None):
    #     Logger.Info("get_connection")
    #     return super(CacheHTTPAdapter, self).get_connection(url, proxies)

    # def close(self):
    #     Logger.Info("close")
    #     super(CacheHTTPAdapter, self).close()

    # def request_url(self, request, proxies):
    #     Logger.Info("request_url")
    #     return super(CacheHTTPAdapter, self).request_url(request, proxies)

    # def add_headers(self, request, **kwargs):
    #     Logger.Info("add_headers")
    #     super(CacheHTTPAdapter, self).add_headers(request, **kwargs)
    #
    # def proxy_headers(self, proxy):
    #     Logger.Info("proxy_headers")
    #     return super(CacheHTTPAdapter, self).proxy_headers(proxy)
