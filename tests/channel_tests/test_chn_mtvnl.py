# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from . channeltest import ChannelTest


class TestMtvNlChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestMtvNlChannel, self).__init__(methodName, "channel.nick.nickelodeon", "mtvnl")

    def test_channel_mtv_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_mtv_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 25)

    def test_folder(self):
        url = "https://www.mtv.nl/shows/teen-mom-young-pregnant"
        self._test_folder_url(url, expected_results=3)

    def test_video(self):
        url = "https://www.mtv.nl/clip/4jnx08/teen-mom-young-pregnant-teen-mom-young-pregnant-ik-denk-niet-dat-ze-er-klaar-voor-is"
        self._test_video_url(url)
