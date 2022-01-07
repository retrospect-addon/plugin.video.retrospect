# SPDX-License-Identifier: GPL-3.0-or-later
import unittest

from . channeltest import ChannelTest


@unittest.skip("No longer available.")
class TestNickJrChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNickJrChannel, self).__init__(methodName, "channel.nick.nickjr", "nickse")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    @unittest.skip("Not present in 2022")
    def test_folder_with_videos_and_pages(self):
        url = "http://www.nickelodeon.se/data/propertyStreamPage.json?&urlKey=svampbob-fyrkant&apiKey=sv_SE_Nick_Web&adfree=&excludeIds=&repeatPattern=&page=1"
        items = self._test_folder_url(url, expected_results=2)
        self.assertGreaterEqual(len([i for i in items if not i.is_playable]), 1)

    def test_video_hls(self):
        url = "http://media.mtvnservices.com/pmt/e1/access/index.html?uri=mgid:arc:video:nickjr.tv:b80cc8ea-e12f-11e3-9765-0026b9414f30&configtype=edge"
        self._test_video_url(url)
