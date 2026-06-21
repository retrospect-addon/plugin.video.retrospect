# SPDX-License-Identifier: GPL-3.0-or-later
from resources.lib.regexer import Regexer
from resources.lib.urihandler import UriHandler
import unittest

from . channeltest import ChannelTest


class TestNosChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        self.__build_version = None
        super(TestNosChannel, self).__init__(methodName, "channel.nos.nosnl", "nosnl")

    @property
    def build_version(self) -> str:
        if not self.__build_version:
            data = UriHandler.open("https://nos.nl/")
            try:
                build_version = Regexer.do_regex(r"<script src=\"[^\"]+/([^/]+)/_buildManifest.js\"", data)[0]
            except:
                raise
            self.__build_version = build_version

        return self.__build_version

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 0, "No items found in mainlist")

    def test_video_update(self):
        url = "https://nos.nl/video/2544381"
        from resources.lib.mediaitem import MediaItem
        item = self._test_video_url(url)    # type: MediaItem

        for stream in [s for s in item.streams if "hls" in s.Url]:
            self.assertTrue("cdn.streamgate.nl" in stream.Url)

    def test_video_listing(self):
        url = f"https://nos.nl/_next/data/{self.build_version}//nieuws/binnenland.json"
        self._test_folder_url(url, expected_results=20)

    @unittest.skip("GEO Blocked.")
    def test_resolver_update(self):
        url = "https://resolver.streaming.api.nos.nl/stream?stream=nos-npo-2&profile=hls_unencrypted&policy=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJjb3JlLm5vcy5ubCIsInN1YiI6Im5vcy1ucG8tMiIsImF1ZCI6WyJyZXNvbHZlci5zdHJlYW1pbmcuYXBpLm5vcy5ubCJdLCJpYXQiOjE2NzUxMTAzNTQsImFsbG93ZWRBcmVhcyI6WyJOTCIsIkFXIiwiQ1ciLCJTWCIsIkJRIl0sImlzR2VvcHJvdGVjdGVkIjp0cnVlfQ.KPRYyZ1hde_lohz-5joacR3YwJljU0vr-Aqr7S_aqWk"
        item = self._test_video_url(url)
        for stream in [s for s in item.streams if "hls" in s.Url]:
            self.assertTrue(".streamgate." in stream.Url)
