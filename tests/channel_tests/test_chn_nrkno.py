# SPDX-License-Identifier: GPL-3.0-or-later
import unittest

from . channeltest import ChannelTest


class TestNrkNoChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNrkNoChannel, self).__init__(methodName, "channel.no.nrkno", "nrkno")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 8, "No items found in mainlist")

    def test_abcxyz(self):
        url = "https://psapi.nrk.no/medium/tv/letters?apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=26)

    def test_list_t(self):
        url = "https://psapi.nrk.no/medium/tv/letters/t/indexelements?onlyOnDemandRights=false&apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=10)

    def test_videos_for_show(self):
        url = "https://psapi.nrk.no/tv/catalog/series/team-bachstad?apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=5)

    def test_videos_for_season(self):
        url = "https://psapi.nrk.no/tv/catalog/series/team-bachstad/seasons/8?apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=2)

    def test_update_video(self):
        url = "https://psapi.nrk.no/playback/manifest/program/MUHU13000420?eea-portability=true"
        self._test_video_url(url)

    def test_category_list(self):
        url = "http://psapi-granitt-prod-we.cloudapp.net/medium/tv/categories?apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=2)

    def test_category_content(self):
        url = "http://psapi-granitt-prod-we.cloudapp.net/medium/tv/categories/humor/indexelements?apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=2)

    def test_list_liv_tv(self):
        url = "https://psapi.nrk.no/tv/live?apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=2)

    def test_headliner(self):
        url = "https://psapi.nrk.no/tv/headliners/default?apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=2)

    @unittest.skip("No longer available in the new API.")
    def test_popular(self):
        url = "https://psapi.nrk.no/medium/tv/popularprograms/week?maxnumber=100&startRow=0&apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=2)

    @unittest.skip("Failing with UTC error on their side.")
    def test_recent(self):
        url = "https://psapi.nrk.no/medium/tv/recentlysentprograms?maxnumber=100&startRow=0&apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=2)

    @unittest.skip("No longer available in the new API.")
    def test_recommended(self):
        url = "https://psapi.nrk.no/medium/tv/recommendedprograms?maxnumber=100&startRow=0&apiKey=d1381d92278a47c09066460f2522a67d"
        self._test_folder_url(url, expected_results=2)
