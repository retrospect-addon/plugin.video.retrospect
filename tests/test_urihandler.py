# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later


from future.utils import PY2

import unittest
import os
import json
import tempfile
import shutil
import time

if PY2:
    # noinspection PyUnresolvedReferences
    from urllib import quote
else:
    # noinspection PyUnresolvedReferences,PyCompatibility
    from urllib.parse import quote

from resources.lib.backtothefuture import basestring
from resources.lib.urihandler import UriHandler
from resources.lib.logger import Logger


class TestUriHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestUriHandler, cls).setUpClass()
        Logger.create_logger(None, str(cls), min_log_level=0)

    @classmethod
    def tearDownClass(cls):
        Logger.instance().close_log()

    def setUp(self):
        UriHandler._UriHandler__handler = None
        self.output_folder = tempfile.mkdtemp(prefix="retro_test_")
        Logger.info("Using temp path: %s", self.output_folder)
        self.proxy = None  # ProxyInfo("localhost", 8888)
        self.cancel_download = False

    def tearDown(self):
        shutil.rmtree(self.output_folder)

    def test_get(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/get"
        data = UriHandler.open(url, proxy=self.proxy)
        data_object = json.loads(data)
        self.assertIsNotNone(data_object)
        self.assertTrue("headers" in data_object)
        self.assertEqual(data_object["headers"]["Host"], 'httpbin.org')
        self.assertEqual(200, UriHandler.instance().status.code)

    def test_post(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/post"
        post_data = "dit is een test"
        post_data_encoded = quote(post_data)
        params = "test={0}".format(post_data_encoded)

        data = UriHandler.open(url, params=params, proxy=self.proxy)
        self.assertIsNot(data, "")
        data_object = json.loads(data)
        self.assertIsNotNone(data_object)
        self.assertTrue("headers" in data_object)
        self.assertEqual(data_object["headers"]["Host"], 'httpbin.org')
        self.assertTrue("form" in data_object)
        self.assertEqual(data_object["form"]["test"], post_data)
        self.assertEqual(200, UriHandler.instance().status.code)

    def test_post_bytes(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/post"
        post_data = "dit is een test"
        post_data_encoded = quote(post_data)

        data = UriHandler.open(url, params="test={0}".format(post_data_encoded).encode(),
                               proxy=self.proxy)
        self.assertIsNot(data, "")
        data_object = json.loads(data)
        self.assertIsNotNone(data_object)
        self.assertTrue("headers" in data_object)
        self.assertEqual(data_object["headers"]["Host"], 'httpbin.org')
        self.assertTrue("form" in data_object)
        self.assertEqual(data_object["form"]["test"], post_data)
        self.assertEqual(200, UriHandler.instance().status.code)

    def test_gzip(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/gzip"
        data = UriHandler.open(url, proxy=self.proxy)
        self.assertIsNot(data, "")
        data_object = json.loads(data)
        self.assertIsNotNone(data_object)
        self.assertTrue("gzipped" in data_object)
        self.assertTrue(data_object["gzipped"])
        self.assertEqual(200, UriHandler.instance().status.code)

    def test_deflate(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/deflate"
        data = UriHandler.open(url, proxy=self.proxy)
        self.assertIsNot(data, "")
        data_object = json.loads(data)
        self.assertIsNotNone(data_object)
        self.assertTrue("deflated" in data_object)
        self.assertTrue(data_object["deflated"])
        self.assertEqual(200, UriHandler.instance().status.code)

    def test_head_404(self):
        UriHandler.create_uri_handler()

        content_type, url = UriHandler.header("http://httpbin.org/status/404", proxy=self.proxy)
        self.assertEqual(404, UriHandler.instance().status.code)
        self.assertTrue(UriHandler.instance().status.error)
        self.assertEqual("", url)
        self.assertEqual("", content_type)

    @unittest.skip("Error in httpbin.org causes 404: https://github.com/postmanlabs/httpbin/issues/617")
    def test_head_redirect(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/redirect-to?url=http%3A%2F%2Fhttpbin.org%2Fget"
        content_type, url = UriHandler.header(url, proxy=self.proxy)
        self.assertEqual(content_type, 'application/json')
        self.assertEqual(url, 'http://httpbin.org/get')
        self.assertEqual(200, UriHandler.instance().status.code)

    @unittest.skip("Error in httpbin.org causes 404: https://github.com/postmanlabs/httpbin/issues/617")
    def test_head_double_redirect(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/redirect-to?url=http%3A%2F%2Fhttpbin.org%2Fredirect-to%3Furl%3Dhttp%253A%252F%252Fhttpbin.org%252Fget"
        content_type, url = UriHandler.header(url, proxy=self.proxy)
        self.assertEqual(content_type, 'application/json')
        self.assertEqual(url, 'http://httpbin.org/get')
        self.assertEqual(200, UriHandler.instance().status.code)

    def test_head(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/get"
        data = UriHandler.header(url, proxy=self.proxy)
        self.assertEqual(data[0], 'application/json')
        self.assertEqual(data[1], 'http://httpbin.org/get')
        self.assertEqual(200, UriHandler.instance().status.code)

    def test_head_error(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/status/500"
        UriHandler.header(url, proxy=self.proxy)
        self.assertEqual(500, UriHandler.instance().status.code)

    def test_content_type_header(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/headers"
        header_name = "Content-Type"
        header_value = "application/json"
        headers = {header_name: header_value}
        data = UriHandler.open(url, proxy=self.proxy, additional_headers=headers)
        self.assertIsNot("", data)
        data = json.loads(data)
        self.assertEqual(data["headers"][header_name], header_value)
        self.assertEqual(200, UriHandler.instance().status.code)

    def test_user_agent(self):
        UriHandler.create_uri_handler()
        url = "http://httpbin.org/headers"
        header_name = "User-Agent"

        # standard header first, the one from code
        header_value = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)"
        data = UriHandler.open(url, proxy=self.proxy)
        self.assertIsNot("", data)
        data = json.loads(data)
        self.assertEqual(data["headers"][header_name], header_value)
        self.assertEqual(200, UriHandler.instance().status.code)

        header_value = "UserAgent/5.0"
        headers = {header_name: header_value}
        data = UriHandler.open(url, proxy=self.proxy, additional_headers=headers)
        self.assertIsNot("", data)
        data = json.loads(data)
        self.assertEqual(data["headers"][header_name], header_value)
        self.assertEqual(200, UriHandler.instance().status.code)

    def test_referer(self):
        UriHandler.create_uri_handler()

        url = "http://httpbin.org/headers"
        header_name = "Referer"
        header_value = "http://httpbin.org"
        headers = {header_name: header_value}
        data = UriHandler.open(url, proxy=self.proxy, additional_headers=headers)
        self.assertIsNot("", data)
        data = json.loads(data)
        self.assertEqual(data["headers"][header_name], header_value)
        self.assertEqual(200, UriHandler.instance().status.code)

        data = UriHandler.open(url, proxy=self.proxy, referer=header_value)
        self.assertIsNot("", data)
        data = json.loads(data)
        self.assertEqual(data["headers"][header_name], header_value)
        self.assertEqual(200, UriHandler.instance().status.code)

    def test_cache_create(self):
        expected_path = os.path.join(self.output_folder, "www")

        UriHandler.create_uri_handler(cache_dir=self.output_folder)
        self.assertTrue(os.path.isdir(expected_path))
        self.assertIsNotNone(UriHandler.instance().cacheStore)
        self.assertEqual(expected_path, UriHandler.instance().cacheStore.cachePath)

    def test_cache(self):
        url = "http://httpbin.org/cache/30"
        UriHandler.create_uri_handler(cache_dir=self.output_folder)

        data = UriHandler.open(url, proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        data_object_1 = json.loads(data)
        self.assertEqual(2, len(os.listdir(UriHandler.instance().cacheStore.cachePath)))

        data = UriHandler.open(url, proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        data_object_2 = json.loads(data)

        self.assertEqual(1, UriHandler.instance().cacheStore.cacheHits)
        self.assertEqual(data_object_1, data_object_2)

    def test_cache_post(self):
        url = "http://httpbin.org/post"
        UriHandler.create_uri_handler(cache_dir=self.output_folder)

        data = UriHandler.open(url, data={"test": "ok"}, proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        json.loads(data)
        self.assertEqual(0, UriHandler.instance().cacheStore.cacheHits)

    def test_cache_no_cache(self):
        url = "http://httpbin.org/cache/30"
        UriHandler.create_uri_handler(cache_dir=self.output_folder)

        data = UriHandler.open(url, proxy=self.proxy, no_cache=True)
        self.assertEqual(200, UriHandler.instance().status.code)
        data_object = json.loads(data)
        self.assertIsNotNone(data_object)
        self.assertTrue("headers" in data_object)
        self.assertEqual(data_object["headers"]["Host"], 'httpbin.org')

        self.assertEqual(0, UriHandler.instance().cacheStore.cacheHits)
        self.assertEqual(0, len(os.listdir(UriHandler.instance().cacheStore.cachePath)))

    def test_cache_no_cache_store(self):
        url = "http://httpbin.org/cache/30"
        UriHandler.create_uri_handler()

        data = UriHandler.open(url, proxy=self.proxy, no_cache=True)
        self.assertEqual(200, UriHandler.instance().status.code)
        data_object = json.loads(data)
        self.assertIsNotNone(data_object)
        self.assertTrue("headers" in data_object)
        self.assertEqual(data_object["headers"]["Host"], 'httpbin.org')

        self.assertIsNone(UriHandler.instance().cacheStore)

    def test_cache_etag(self):
        url = "http://httpbin.org/etag/33a64df551425fcc55e4d42a148795d9f25f89d4"
        UriHandler.create_uri_handler(cache_dir=self.output_folder)

        data = UriHandler.open(url, proxy=self.proxy)
        data_object_1 = json.loads(data)
        self.assertEqual(2, len(os.listdir(UriHandler.instance().cacheStore.cachePath)))
        self.assertEqual(200, UriHandler.instance().status.code)
        self.assertEqual(0, UriHandler.instance().cacheStore.cacheHits)

        data = UriHandler.open(url, proxy=self.proxy)
        data_object_2 = json.loads(data)
        self.assertEqual(200, UriHandler.instance().status.code)
        self.assertEqual(1, UriHandler.instance().cacheStore.cacheHits)
        self.assertEqual(data_object_1, data_object_2)

    def test_cache_revalidate(self):
        url = "http://httpbin.org/etag/33a64df551425fcc55e4d42a148795d9f25f89d4"
        UriHandler.create_uri_handler(cache_dir=self.output_folder)

        data = UriHandler.open(url, proxy=self.proxy)
        data_object_1 = json.loads(data)
        self.assertEqual(2, len(os.listdir(UriHandler.instance().cacheStore.cachePath)))
        self.assertEqual(200, UriHandler.instance().status.code)

        data = UriHandler.open(url, proxy=self.proxy)
        data_object_2 = json.loads(data)
        self.assertEqual(200, UriHandler.instance().status.code)

        self.assertEqual(1, UriHandler.instance().cacheStore.cacheHits)
        self.assertEqual(data_object_1, data_object_2)

    def test_cache_expire_1_second(self):
        sleep_time = 1
        url = "http://httpbin.org/cache/{0}".format(sleep_time)
        UriHandler.create_uri_handler(cache_dir=self.output_folder)

        data = UriHandler.open(url, proxy=self.proxy)
        data_object_1 = json.loads(data)
        self.assertEqual(2, len(os.listdir(UriHandler.instance().cacheStore.cachePath)))
        self.assertEqual(200, UriHandler.instance().status.code)

        data = UriHandler.open(url, proxy=self.proxy)
        data_object_2 = json.loads(data)
        self.assertEqual(200, UriHandler.instance().status.code)

        self.assertEqual(1, UriHandler.instance().cacheStore.cacheHits)
        self.assertEqual(data_object_1, data_object_2)

        time.sleep(sleep_time)
        UriHandler.open(url, proxy=self.proxy)
        self.assertEqual(1, UriHandler.instance().cacheStore.cacheHits)

    def test_utf_8(self):
        url = "http://httpbin.org/encoding/utf8"
        UriHandler.create_uri_handler()
        data = UriHandler.open(url, proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        self.assertIsNot(data, "")
        self.assertTrue(u"⠺⠊⠇⠇ ⠹⠻⠑⠋⠕⠗⠑ ⠏⠻⠍⠊⠞ ⠍⠑ ⠞⠕ ⠗⠑⠏⠑⠁⠞⠂ ⠑⠍⠏⠙⠁⠞⠊⠊⠁⠇⠇⠹⠂ ⠹⠁⠞" in data)

    def test_return_string(self):
        UriHandler.create_uri_handler()

        # no encoding present in this URL
        url = "http://httpbin.org/robots.txt"
        data = UriHandler.open(url, proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        self.assertTrue(isinstance(data, basestring), msg="No <string> type returned.")
        self.assertIsNotNone(data)
        self.assertIsNot("", data)

    # cookies
    def test_set_cookie(self):
        UriHandler.create_uri_handler()

        cookie_name = "cookie_test"
        cookie_value = "test data"
        cookie_domain = "httpbin.org"
        url = "http://{0}/cookies/set?{1}={2}".format(cookie_domain, cookie_name, quote(cookie_value))

        # pre check that there are none
        cookie = UriHandler.get_cookie(cookie_name, cookie_domain)
        self.assertIsNone(cookie)

        # load the url and receive cookies
        data = UriHandler.open(url, proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        self.assertIsNot("", data)
        cookie = UriHandler.get_cookie(cookie_name, cookie_domain)
        self.assertIsNotNone(cookie)
        self.assertEqual(cookie.value.strip("\""), cookie_value)

        # verify the values from the json data
        data = json.loads(data)
        cookie_value_retrieved = data["cookies"][cookie_name]
        self.assertEqual(cookie_value, cookie_value_retrieved)

    def test_set_cookie_with_cache(self):
        UriHandler.create_uri_handler(cache_dir=self.output_folder,
                                      cookie_jar=os.path.join(self.output_folder, "cookies.txt"))

        cookie_name = "cookie_test"
        cookie_value = "test data"
        cookie_domain = "httpbin.org"
        # we need to not redirect, because that would not cause the caching
        cookie_string = "{0}={1}; Path=/".format(cookie_name, cookie_value)
        url = "http://{0}/response-headers?set-cookie={1}".format(cookie_domain, quote(cookie_string))

        # pre check that there are none
        cookie = UriHandler.get_cookie(cookie_name, cookie_domain)
        self.assertIsNone(cookie)

        # load the url and receive cookies
        data = UriHandler.open(url, proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        self.assertIsNot("", data)
        cookie = UriHandler.get_cookie(cookie_name, cookie_domain)
        self.assertIsNotNone(cookie)
        self.assertEqual(cookie.value.strip("\""), cookie_value)

    # cookies
    def test_set_cookie_file(self):
        cookie_name = "cookie_test"
        cookie_value = "test data"
        cookie_domain = "httpbin.org"
        url = "http://{0}/cookies/set?{1}={2}".format(cookie_domain, cookie_name, quote(cookie_value))

        # create a file cookiejar
        UriHandler.create_uri_handler(cookie_jar=os.path.join(self.output_folder, "cookies.txt"))

        # pre check that there are none
        cookie = UriHandler.get_cookie(cookie_name, cookie_domain)
        self.assertIsNone(cookie)

        # load the url and receive cookies
        data = UriHandler.open(url, proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        self.assertIsNot("", data)

        # find the cookie
        cookie = UriHandler.get_cookie(cookie_name, cookie_domain)
        self.assertIsNotNone(cookie)
        self.assertEqual(cookie.value.strip("\""), cookie_value)

        # partial match
        cookie = UriHandler.get_cookie(cookie_name, cookie_domain, match_start=True)
        self.assertIsNotNone(cookie)
        self.assertEqual(cookie.name, cookie_name)
        self.assertEqual(cookie.value.strip("\""), cookie_value)

        # do a quick check
        self.assertIsNotNone(UriHandler.get_cookie(cookie_name, domain=cookie_domain))

        # verify the values from the json data
        data = json.loads(data)
        cookie_value_retrieved = data["cookies"][cookie_name]
        self.assertEqual(cookie_value, cookie_value_retrieved)

    def test_cookie_persist(self):
        cookie_name = "cookie_test"
        cookie_value = "test data"
        cookie_domain = "httpbin.org"

        # create a file cookiejar
        UriHandler.create_uri_handler(cookie_jar=os.path.join(self.output_folder, "cookies.txt"))

        UriHandler.set_cookie(name=cookie_name, domain=cookie_domain, value=cookie_value)
        UriHandler.instance().cookieJar.save()

        # Create a new UriHandler and try again
        UriHandler._UriHandler__handler = None
        UriHandler.create_uri_handler(cookie_jar=os.path.join(self.output_folder, "cookies.txt"))

        # pre check that there are none
        cookie = UriHandler.get_cookie(cookie_name, cookie_domain)
        self.assertIsNotNone(cookie, msg="Cookie was not persisted on disk")

    def test_clear_cookies(self):
        UriHandler.create_uri_handler()
        UriHandler.set_cookie(name="ipsum", domain="domain.com")
        UriHandler.set_cookie(name="ipsum2", domain="domain2.com")
        self.assertGreaterEqual(len(UriHandler.instance().cookieJar._cookies), 2)
        UriHandler.clear_cookies()
        self.assertDictEqual(UriHandler.instance().cookieJar._cookies, {})

    def test_no_cookies(self):
        UriHandler.create_uri_handler()

        # first check without cookies. Fails on missing domain
        cookie = UriHandler.get_cookie("lorem", domain="domain.com")
        self.assertFalse(cookie)

        # we need a cookie for this domain
        UriHandler.set_cookie(name="ipsum", domain="domain.com")

        cookie = UriHandler.get_cookie("lorem", domain="domain.com")
        self.assertFalse(cookie)
        cookie = UriHandler.get_cookie("lorem", "domain.com")
        self.assertIsNone(cookie)
        cookie = UriHandler.get_cookie("lore", "domain.com", match_start=True)
        self.assertIsNone(cookie)

    def test_error(self):
        UriHandler.create_uri_handler()

        data = UriHandler.open("http://httpbin.org/status/500", proxy=self.proxy)
        self.assertEqual("", data)
        self.assertEqual(500, UriHandler.instance().status.code)

    def test_404(self):
        UriHandler.create_uri_handler()

        data = UriHandler.open("http://httpbin.org/status/404", proxy=self.proxy)
        self.assertEqual("", data)
        self.assertEqual(404, UriHandler.instance().status.code)

    def test_gif(self):
        UriHandler.create_uri_handler()
        gif = UriHandler.open("http://httpbin.org/image/png", proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        self.assertTrue(isinstance(gif, bytes))

    def test_download(self):
        UriHandler.create_uri_handler()
        file_name = "test.png"

        self.cancel_download = False
        download_path = UriHandler.download("http://www.ovh.net/files/1Mb.dat", file_name,
                                            self.output_folder, self.__download_callback,
                                            proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        self.assertTrue(os.path.isfile(download_path))
        self.assertTrue(os.path.getsize(download_path) > 0)

    def test_download_cancel(self):
        UriHandler.create_uri_handler()
        file_name = "test.png"

        self.cancel_download = True
        download_path = UriHandler.download("http://www.ovh.net/files/10Mb.dat", file_name,
                                            self.output_folder, self.__download_callback,
                                            proxy=self.proxy)
        self.assertEqual(200, UriHandler.instance().status.code)
        self.assertEqual("", download_path)

    # noinspection PyUnusedLocal
    def __download_callback(self, retrieved_size, total_size, perc, completed, status):
        print(status)
        if perc > 75:
            return self.cancel_download
        return False
