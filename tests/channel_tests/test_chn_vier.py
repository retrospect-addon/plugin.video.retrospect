# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import os
import unittest

from . channeltest import ChannelTest


@unittest.skipIf("CI" in os.environ, "Skipping in CI due to broken api")
class TestVierBeChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestVierBeChannel, self).__init__(methodName, "channel.be.vier", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list_vier(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    def test_tv4_tv_shows(self):
        url = "https://www.goplay.be/programmas/"
        items = self._test_folder_url(url, 20)
        # Should be significantly less than the total list of about 500.
        self.assertLess(len(items), 150)

    def test_go_play_tv_shows(self):
        self._switch_channel("goplay")
        url = "https://www.goplay.be/programmas/"
        self._test_folder_url(url, 200)

    def test_search(self):
        media_items = self.channel.search_site(needle="cops")
        self.assertGreater(len(media_items), 5)

    def test_show_seasons_listing(self):
        url = "https://www.goplay.be/komen-eten-celebs"
        self._test_folder_url(url, 1)

    def test_season_listing(self):
        url = "https://www.goplay.be/bake-off-vlaanderen-kerst"
        self._test_folder_url(url, 1)

    @unittest.skip("Requires a log in.")
    def test_resolve_via_url(self):
        url = "https://www.goplay.be/video/hetisingewikkeld/hetisingewikkeld-seizoen-1/hetisingewikkeld-s1-aflevering-8"
        self._test_video_url(url)

    @unittest.skip("Requires a log in.")
    def test_resolve_via_url_2(self):
        url = "https://www.goplay.be/video/junior-bake-off-vlaanderen/junior-bake-off-vlaanderen-s5/junior-bake-off-vlaanderen-s5-aflevering-6"
        self._test_video_url(url)

    def test_epg_listing(self):
        day = datetime.datetime.now() - datetime.timedelta(days=2)
        url = "https://www.goplay.be/tv-gids/vier/{:04d}-{:02d}-{:02d}".format(
            day.year, day.month, day.day)
        self._test_folder_url(url, 2)
