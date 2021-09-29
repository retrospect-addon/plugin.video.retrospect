# SPDX-License-Identifier: GPL-3.0-or-later

from .channeltest import ChannelTest


class TestGelderlandChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestGelderlandChannel, self).__init__(methodName, "channel.regionalnl.gelderland", "omroepgelderland")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_mainlist(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 20)

    def test_show_list(self):
        url = "https://api.regiogroei.cloud/page/program/83"
        self._test_folder_url(url, expected_results=10)

    def test_news_listing(self):
        url = "https://api.regiogroei.cloud/page/program/31"
        self._test_folder_url(url, expected_results=20)

    def test_single_video(self):
        url = "https://api.regiogroei.cloud/page/program/1078"
        self._test_folder_url(url, expected_results=1)

    def test_video(self):
        url = "https://omroepgelderland.bbvms.com/p/regiogroei_gelderland_web_videoplayer/c/sourceid_string:SREGIOOG_96941.json"
        self._test_video_url(url)

    def test_live_streams(self):
        live_url = "https://api.regiogroei.cloud/page/channel/tv-gelderland?channel=tv-gelderland"
        items = self._test_video_url(live_url)
