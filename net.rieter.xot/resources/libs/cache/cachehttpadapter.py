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
        self.cacheStore = cache_store        # type: StreamCache

        super(CacheHTTPAdapter, self).__init__(pool_connections, pool_maxsize, max_retries,
                                               pool_block)

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        response = self.__get_cached_response(request)
        if response:
            self.cacheStore.cacheHits += 1
            return response

        # Actually send a request
        response = super(CacheHTTPAdapter, self).send(request, stream, timeout, verify, cert, proxies)

        # Cache it if it was a valid response for a GET.
        if request.method == "GET" and (200 <= response.status_code < 300):
            self.__store_response(request, response)

        elif response.status_code == 304:
            Logger.Debug("304 Response found. Pro-Longing the %s", response.url)
            self.cacheStore.cacheHits += 1
            response = self.__get_cached_response(request, no_check=True)

        return response

    def __get_cached_response(self, req, no_check=False):
        bodyKey, metaKey = self.__get_cache_keys(req)
        if not self.cacheStore.has_cache_key(metaKey) or not \
                self.cacheStore.has_cache_key(bodyKey):
            Logger.Debug("No-Cache-Hit: %s", req.url)
            return None

        with self.cacheStore.get(metaKey) as fd:
            meta = json.load(fd)
        headers = CaseInsensitiveDict(data=meta["headers"])
        cache_data = meta.get("cache_data")

        resp = requests.Response()
        resp.raw = self.cacheStore.get(bodyKey)
        resp.status_code = meta["status"]
        resp.headers = headers
        resp.encoding = meta["encoding"]

        if no_check:
            return resp

        # Determine the maximum age and then check if the cache if valid or not.
        valid_in_seconds = 3600
        if 'max-age' in cache_data:
            valid_in_seconds = cache_data['max-age']
        if self.cacheStore.is_expired(metaKey, valid_in_seconds):
            Logger.Debug("Expired Cache-Hit: %s", req.url)
            return None

        if self.__must_revalidate(cache_data):
            Logger.Debug("Stale-Cache hit found. Revalidating")
            req.headers["If-None-Match"] = headers["etag"]
            return None

        Logger.Debug("Cache-Hit: %s", req.url)
        return resp

    def __store_response(self, req, res):
        if res.status_code != 200 or req.method != "GET":
            return

        bodyKey, metaKey = self.__get_cache_keys(req)

        # Store the body as a binary file and reset the raw and _content_consumed attributes
        # of the response so we can reuse it again
        with self.cacheStore.set(bodyKey) as fp:
            for chunk in res.iter_content(chunk_size=128):
                fp.write(chunk)

        res.raw = self.cacheStore.get(bodyKey)
        res._content_consumed = False

        # extract cache related data and store it in a json file
        cache_data = self.__extract_cache_data(res.headers)
        data = {
            "body": bodyKey,
            "headers": dict(
                (k, v) for k, v in res.headers.items()
            ),
            "status": res.status_code,
            "encoding": res.encoding,
            "cache_data": cache_data
        }
        with self.cacheStore.set(metaKey) as fp:
            json.dump(data, fp, encoding='utf-8', indent=2)

        return

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

        Logger.Trace("Found cache-control and etag data: %s", cache_data)
        return cache_data

    def __must_revalidate(self, cache_data):
        """ Checks if a cached response should be revalidated

        Arguments:
        meta_data : dict - the response to check.

        If True is returned the response has a must-revalidate cache parameters
        and an ETAG.

        """

        # No cache data present, so no need to revalidate the thing.
        if not cache_data:
            Logger.Trace("No cache data found for a cached request. No "
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
        hashTool = hashlib.md5()
        hashTool.update(req.url)
        key = hashTool.hexdigest()
        bodyFile = "{0}.body".format(key)
        metaFile = "{0}.meta".format(key)
        return bodyFile, metaFile

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
