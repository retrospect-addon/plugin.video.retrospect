# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

import requests
from requests.adapters import HTTPAdapter, DEFAULT_POOLSIZE, DEFAULT_RETRIES, DEFAULT_POOLBLOCK


class DnsResolverHTTPAdapter(HTTPAdapter):
    def __init__(self, url, pool_connections=DEFAULT_POOLSIZE, pool_maxsize=DEFAULT_POOLSIZE,
                 max_retries=DEFAULT_RETRIES, pool_block=DEFAULT_POOLBLOCK):

        # scheme, netloc, path, params, query, fragment = requests.utils.urlparse(url)
        self.__url_parts = list(requests.utils.urlparse(url))
        self.__original_host_name = self.__url_parts[1]

        # TODO: do a DNS lookup
        self.__url_parts[0] = "https"
        self.__url_parts[1] = "172.217.20.131"

        super(DnsResolverHTTPAdapter, self).__init__(pool_connections, pool_maxsize, max_retries,
                                                     pool_block)

    def get_connection(self, url, proxies=None):

        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        # Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        redirect_url = requests.utils.urlunparse(self.__url_parts)
        conn = super(DnsResolverHTTPAdapter, self).get_connection(redirect_url, proxies=proxies)
        return conn

    def request_url(self, request, proxies):
        requests.url = requests.utils.urlunparse(self.__url_parts)
        return super(DnsResolverHTTPAdapter, self).request_url(request, proxies)

    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **pool_kwargs):
        if self.__url_parts[0] == "https":
            pool_kwargs['assert_hostname'] = self.__original_host_name
        super(DnsResolverHTTPAdapter, self).init_poolmanager(connections, maxsize, block,
                                                             **pool_kwargs)
