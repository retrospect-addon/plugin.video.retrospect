# SPDX-License-Identifier: GPL-3.0-or-later
import unittest

from . channeltest import ChannelTest


@unittest.skip("Broken for now.")
class TestAmtChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestAmtChannel, self).__init__(methodName, "channel.videos.amt", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 5)

    def test_movie_trailer_list(self):
        url = "https://trailers.apple.com/trailers/wb/the-batman/"
        self._test_folder_url(url, expected_results=1)

    def test_trailers(self):
        url = "https://trailers.apple.com/trailers/wb/the-batman/"
        items = self._test_folder_url(url, expected_results=1)
        self.assertGreater(len(items), 0)
        self.assertTrue(items[0].has_streams())
