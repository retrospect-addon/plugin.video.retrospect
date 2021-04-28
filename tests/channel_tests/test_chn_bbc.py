# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestBbcIplayerChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestBbcIplayerChannel, self).__init__(methodName, "channel.uk.bbc", "bbciplayer")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 2)

    def test_alpha_listing(self):
        url = "#alphalisting"
        self._test_folder_url(url, expected_results=26)

    def test_alpha_show_listing(self):
        url = "https://www.bbc.co.uk/iplayer/a-z/a"
        self._test_folder_url(url, expected_results=26)

    def test_show_content(self):
        url = "http://www.bbc.co.uk/iplayer/episode/m000dl8n/baby-chimp-rescue-series-1-3-a-new-beginning"
        self._test_folder_url(url, expected_results=2)

    def test_show_content_https(self):
        url = "https://www.bbc.co.uk/iplayer/episode/m000dl8n/baby-chimp-rescue-series-1-3-a-new-beginning"
        self._test_folder_url(url, expected_results=2)

