# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from . channeltest import ChannelTest


class TestUrPlayChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestUrPlayChannel, self).__init__(methodName, "channel.se.urplay", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 6, "No items found in mainlist")

    def test_main_tv_show_list(self):
        url = "#tvshows"
        self._test_folder_url(url, 100)

    @unittest.skipIf("CI" in os.environ, "Not working on CI due to GEO restrictions.")
    def test_video_play(self):
        url = "https://urplay.se/program/181051-pregunta-ya-pascua"
        self._test_video_url(url)

    @unittest.skipIf("CI" in os.environ, "Not working on CI due to GEO restrictions.")
    def test_video_audio(self):
        url = "https://urplay.se/program/216777-ajatuksia-suomeksi-unelmaelama"
        self._test_video_url(url)

    @unittest.skipIf("CI" in os.environ, "Not working on CI due to GEO restrictions.")
    def test_category(self):
        url = "https://urplay.se/api/v1/search?" \
              "main_genre_must_not[]=forelasning&" \
              "main_genre_must_not[]=panelsamtal&" \
              "platform=urplay&" \
              "rows={}&" \
              "sab_category=utbildning%20%26%20media&" \
              "singles_and_series=true&" \
              "start={}&" \
              "view=title"
        item = self._get_media_item("#category", "category")
        item.metaData["url_format"] = url
        items = self.channel.process_folder_list(item)
        self.assertGreaterEqual(len(items), 95)

    @unittest.skipIf("CI" in os.environ, "Not working on CI due to GEO restrictions.")
    def test_popular(self):
        url = "https://urplay.se/api/v1/search?product_type=program&query=&rows=150&start=0&view=most_viewed"
        self._test_folder_url(url, expected_results=10)

    @unittest.skipIf("CI" in os.environ, "Not working on CI due to GEO restrictions.")
    def test_most_recent(self):
        url = "https://urplay.se/api/v1/search?product_type=program&rows=150&start=0&view=published"
        self._test_folder_url(url, expected_results=10)

    @unittest.skipIf("CI" in os.environ, "Not working on CI due to GEO restrictions.")
    def test_last_chance(self):
        url = "https://urplay.se/api/v1/search?product_type=program&rows=150&start=0&view=last_chance"
        self._test_folder_url(url, expected_results=10)

    @unittest.skipIf("CI" in os.environ, "Not working on CI due to GEO restrictions.")
    def test_category_radio(self):
        url = "https://urplay.se/api/v1/search?" \
                "type=programradio&" \
                "platform=urplay&" \
                "rows={}&" \
                "singles_and_series=true&" \
                "start={}&" \
                "view=title"
        self._test_folder_url(url, expected_results=50, exact_results=False)

    @unittest.skipIf("CI" in os.environ, "Not working on CI due to GEO restrictions.")
    def test_search(self):
        url = "https://urplay.se/api/v1/search?query=Alfons"
        self._test_folder_url(url, expected_results=5, exact_results=False)

    @unittest.skipIf("CI" in os.environ, "Not working on CI due to GEO restrictions.")
    def test_show_with_seasons(self):
        url = "https://urplay.se/_next/data/GA__A10ZjqJt3LcPhc8nZ/serie/193272-pregunta-ya.json"
        items = self._test_folder_url(url, expected_results=2)
        folders = [i for i in items if i.is_folder]
        self.assertGreaterEqual(len(folders), 2)
        videos = [i for i in items if i.is_playable]
        self.assertEqual(len(videos), 0)
