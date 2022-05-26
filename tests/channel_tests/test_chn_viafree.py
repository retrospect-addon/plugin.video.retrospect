# SPDX-License-Identifier: GPL-3.0-or-later
import unittest

from . channeltest import ChannelTest


@unittest.skip("ViaFree became Pluto.tv")
class TestViaFreeChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestViaFreeChannel, self).__init__(methodName, "channel.mtg.viafree", "viafreese")

    def test_channel_viafree_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_viafree_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 100)

    def test_video_listing(self):
        url = "http://playapi.mtgx.tv/v3/videos?format=11987&order=-airdate&type=program"
        self._test_folder_url(url, expected_results=5)
