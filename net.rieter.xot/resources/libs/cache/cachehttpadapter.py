import requests
import requests.cookies
import requests.utils
from requests.adapters import HTTPAdapter, DEFAULT_POOLSIZE, DEFAULT_RETRIES, DEFAULT_POOLBLOCK

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
            return response

        response = super(CacheHTTPAdapter, self).send(request, stream, timeout, verify, cert, proxies)
        self.__cache_response(request, response)
        return response

    def __get_cached_response(self, req):
        bodyKey, metaKey = self.__get_cache_keys(req)
        if not self.cacheStore.has_key(metaKey) or not \
                self.cacheStore.has_key(bodyKey):
            return None

        if self.cacheStore.is_expired(metaKey, 3600):
            return None

        with self.cacheStore.get(metaKey) as fd:
            meta = json.load(fd)

        resp = requests.Response()
        resp.raw = self.cacheStore.get(bodyKey)
        resp.status_code = meta["status"]

        self.cacheStore.cacheHits += 1
        return resp

    def __cache_response(self, req, res):
        if res.status_code != 200:
            return

        bodyKey, metaKey = self.__get_cache_keys(req)

        with self.cacheStore.set(bodyKey) as fp:
            for chunk in res.iter_content(chunk_size=128):
                fp.write(chunk)

        # reset the raw and _content_consumed attributes
        res.raw = self.cacheStore.get(bodyKey)
        res._content_consumed = False

        data = {
            "body": bodyKey,
            "headers": dict(
                (k, v) for k, v in res.headers.items()
            ),
            "status": res.status_code,
            "encoding": res.encoding
        }

        with self.cacheStore.set(metaKey) as fp:
            json.dump(data, fp, encoding='utf-8', indent=2)

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
