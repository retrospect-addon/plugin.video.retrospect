# SPDX-License-Identifier: GPL-3.0-or-later

from .channeltest import ChannelTest


class TestBrabantChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestBrabantChannel, self).__init__(methodName, "channel.regionalnl.brabant", "omroepbrabant")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_mainlist(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 9)

    def test_alpha_sub_listing(self):
        url = "https://api.omroepbrabant.nl/api/media/tv/series/B"
        self._test_folder_url(url, expected_results=10)

    def test_show_listing(self):
        url = "https://api.omroepbrabant.nl/api/media/series/v2/1"
        self._test_folder_url(url, expected_results=4)

    def test_video_resolve(self):
        url = "https://omroepbrabant.bbvms.com/p/default/q/sourceid_string:3419998.json"
        self._test_video_url(url)
