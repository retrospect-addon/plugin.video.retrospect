# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import unittest

from . channeltest import ChannelTest


class TestNickelodeonChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNickelodeonChannel, self).__init__(methodName, "channel.nick.nickelodeon", "nickelodeon")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    def test_show_list_more_pages(self):
        url = "https://www.nickelodeon.nl/shows/65kecx/de-legende-van-korra"
        self._test_folder_url(url, expected_results=5)

    def test_show_list_with_seasons(self):
        url = "https://www.nickelodeon.nl/shows/76ypv4/spongebob"
        items = self._test_folder_url(url, expected_results=2)
        seasons = [i for i in items if i.type == "folder"]
        self.assertGreaterEqual(len(seasons), 1)

    def test_season_listing(self):
        url = "https://www.nickelodeon.nl/shows/spongebob/sdpe3c/seizoen-seasonnumber-8"
        self._test_folder_url(url, expected_results=5)

    @unittest.skipIf("CI" in os.environ, "Skipping in CI due to Geo-Restrictions")
    def test_video(self):
        url = "https://www.nickelodeon.nl/video/sfl1gm/spongebob-spongebobs-gouden-moment-4"
        self._test_video_url(url)
