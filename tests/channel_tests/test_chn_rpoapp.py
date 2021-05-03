# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestRpoAppChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestRpoAppChannel, self).__init__(methodName, "channel.regionalnl.rpoapp", "rtvutrecht")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list_utrecht(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    def test_video_listing_utrecht(self):
        url = "https://www.rtvutrecht.nl/gemist/uitzending/rtvutrecht/unieuws/"
        self._test_folder_url(url, expected_results=20)

    def test_video_utrecht(self):
        url = "https://www.rtvutrecht.nl/gemist/uitzending/rtvutrecht/unieuws/20210503-1700/"
        self._test_video_url(url)
