# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from . channeltest import ChannelTest


class TestNpoChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNpoChannel, self).__init__(methodName, "channel.nos.nos2010", "uzgjson")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 8, "No items found in mainlist")

    def test_live_radio(self):
        self._test_folder_url("https://start-api.npo.nl/page/live",
                              headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
                              expected_results=8)

    def test_live_tv(self):
        self._test_folder_url("https://www.npostart.nl/live", 10)

    def test_categories(self):
        self._test_folder_url("https://www.npostart.nl/programmas", 5)

    def test_recent_week_list(self):
        self._test_folder_url("#recent", 7)

    def test_alpha_listing(self):
        self._test_folder_url("#alphalisting", 27)

    def test_alpha_sub_listing(self):
        self._test_folder_url(
            "https://www.npostart.nl/media/series?page=1&dateFrom=2014-01-01&az=A&"
            "tileMapping=normal&tileType=teaser&pageType=catalogue",
            headers={"X-Requested-With": "XMLHttpRequest"},
            expected_results=50
        )

    def test_full_alpha_list(self):
        items = self._test_folder_url(
            "https://start-api.npo.nl/media/series?pageSize=50&page=2&dateFrom=2014-01-01",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=125)

        more = [i for i in items if i.name.startswith("\b")]
        self.assertEqual(len(more), 1)

    def test_full_alpha_sub_list_with_more_pages_downloaded(self):
        items = self._test_folder_url(
            "https://start-api.npo.nl/media/series/BV_101396526/episodes?pageSize=10",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=5
        )

        # More pages should have been downloaded.
        folders = [item for item in items if item.is_folder]
        self.assertGreaterEqual(len(folders), 0)

    def test_tv_show_listing_with_more_page_item(self):
        # A show with multiple pages, but without extra items
        items = self._test_folder_url(
            "https://start-api.npo.nl/media/series/NOSjnlMP/episodes?pageSize=10",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=101, exact_results=True
        )
        # More pages should be present (requested 5, will be more there)
        folders = [item for item in items if item.is_folder]
        self.assertGreaterEqual(len(folders), 1)

    def test_tv_show_listing_with_extras(self):
        # A show with extra items
        items = self._test_folder_url(
            "https://start-api.npo.nl/page/franchise/VPWON_1246712",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=23, exact_results=True
        )
        # There should be links to the full episode list (media/series/*/episodes),
        # to the extras (media/series/*/clips), and to the fragments (media/series/*/fragments)
        all_folders = [item for item in items if item.is_folder and "episodes" in item.url]
        extras_folders = [item for item in items if item.is_folder and "clips" in item.url]
        fragments_folders = [item for item in items if item.is_folder and "fragments" in item.url]
        self.assertEqual(len(all_folders), 1)
        self.assertEqual(len(extras_folders), 1)
        self.assertEqual(len(fragments_folders), 1)

    def test_tv_show_list_extras(self):
        items = self._test_folder_url(
            "https://start-api.npo.nl/media/series/KN_1678993/clips?pageSize=10",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=101, exact_results=True
        )

    def test_tv_show_list_fragments(self):
        items = self._test_folder_url(
            "https://start-api.npo.nl/media/series/POW_04596562/fragments?pageSize=10",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=100
        )

    def test_tv_show_listing_with_multiple_seasons(self):
        # A show with multiple very short seasons
        items = self._test_folder_url(
            "https://start-api.npo.nl/page/franchise/NOS2016inBeeld",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=1
        )
        # There should be a link to the full episode list (media/series/*/episodes)
        all_folders = [item for item in items if item.is_folder and "episodes" in item.url]
        self.assertEqual(len(all_folders), 1)

    def test_tv_show_listing_with_single_episode(self):
        # A show with one episode, no seasons, should not have an "All episodes" folder
        items = self._test_folder_url(
            "https://start-api.npo.nl/page/franchise/POMS_S_NOS_349833",
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=1, exact_results=True
        )

    def test_guide_day_list(self):
        import datetime
        day = datetime.datetime.now() - datetime.timedelta(days=1)
        self._test_folder_url(
            "https://start-api.npo.nl/epg/{:04d}-{:02d}-{:02d}?type=tv".format(day.year, day.month, day.day),
            headers={"apikey": "07896f1ee72645f68bc75581d7f00d54"},
            expected_results=25
        )

    def test_search_extend(self):
        self._test_folder_url(
            "https://www.npostart.nl/search/extended?page=4&query=test&filter=episodes&"
            "dateFrom=2014-01-01&tileMapping=search&tileType=asset&pageType=search",
            expected_results=5,
            headers={"X-Requested-With": "XMLHttpRequest"}
        )

    def test_update_stream_pow(self):
        url = "POW_04508304"
        self._test_video_url(url)

    @unittest.skipIf("CI" in os.environ, "Skipping in CI due to Geo-Restrictions")
    def test_update_stream_live(self):
        url = "https://www.npostart.nl/live/npo-1"
        self._test_video_url(url)
