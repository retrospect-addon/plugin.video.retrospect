# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from resources.lib.logger import Logger
from resources.lib.streams.youtube import YouTube
from resources.lib.urihandler import UriHandler


class TestYoutube(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestYoutube, cls).setUpClass()
        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler(ignore_ssl_errors=False)

    def setUp(self):
        self.__proxy = None  # proxyinfo.ProxyInfo("localhost", 8888)

    def test_stream_extraction_via_add_on(self):
        url = "http://www.youtube.com/watch?v=878-LYQEcPs"
        results = YouTube.get_streams_from_you_tube(url, self.__proxy)
        results.sort(key=lambda x: int(x[1]))
        streams = []
        bitrates = []
        for s, b in results:
            if s.count("://") > 1:
                raise Exception("Duplicate protocol in url: %s", s)
            streams.append(s)
            bitrates.append(b)
            print("%s - %s" % (b, s))
            Logger.info("%s - %s", b, s)

        self.assertEqual(len(streams), 1)

    def test_stream_extraction_internal_01(self):
        url = "http://www.youtube.com/watch?v=878-LYQEcPs"
        results = YouTube.get_streams_from_you_tube(url, self.__proxy, use_add_on=False)
        results.sort(key=lambda x: int(x[1]))
        streams = []
        bitrates = []
        for s, b in results:
            if s.count("://") > 1:
                raise Exception("Duplicate protocol in url: %s", s)
            streams.append(s)
            bitrates.append(b)
            print("%s - %s" % (b, s))
            Logger.info("%s - %s", b, s)

        self.assertGreater(len(streams), 1)

    def test_stream_extraction_internal_02(self):
        url = "https://www.youtube.com/watch?v=S2g0GiCHyJE"
        results = YouTube.get_streams_from_you_tube(url, self.__proxy, use_add_on=False)
        results.sort(key=lambda x: int(x[1]))
        streams = []
        bitrates = []
        for s, b in results:
            if s.count("://") > 1:
                raise Exception("Duplicate protocol in url: %s", s)
            streams.append(s)
            bitrates.append(b)
            print("%s - %s" % (b, s))
            Logger.info("%s - %s", b, s)

        self.assertGreater(len(streams), 1)
