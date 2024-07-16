# SPDX-License-Identifier: GPL-3.0-or-later

import os
import unittest

from . channeltest import ChannelTest


@unittest.skip("Broken for now.")
class TestVierBeChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestVierBeChannel, self).__init__(methodName, "channel.be.vier", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list_vier(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    def test_main_list_vijf(self):
        self._switch_channel("vijfbe")
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 10, "No items found in mainlist")

    def test_main_list_zes(self):
        self._switch_channel("zesbe")
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 10, "No items found in mainlist")

    def test_guide_day_list(self):
        import datetime
        day = datetime.datetime.now() - datetime.timedelta(days=1)
        self._test_folder_url(
            "https://www.goplay.be/api/epg/vier/{:04d}-{:02d}-{:02d}".format(day.year, day.month, day.day),
            expected_results=3
        )

    def test_popular(self):
        url = "https://www.goplay.be/api/programs/popular/vier"
        self._test_folder_url(url, expected_results=5)

    def test_video_listing_for_show_with_seasons(self):
        url = "https://www.goplay.be/big-brother"
        self._test_folder_url(url, expected_results=3)

    def test_video_listing_for_show_no_season(self):
        url = "https://www.goplay.be/before-they-were-royal"
        self._test_folder_url(url, expected_results=4)

    @unittest.skipIf("CI" in os.environ, "Skipping in CI due to Geo-Restrictions")
    def test_html_video(self):
        url = "https://www.goplay.be/video/auwch/ben-segers-vreest-dat-dit-een-thaise-massage-met-happy-ending-is"
        self._test_video_url(url)
