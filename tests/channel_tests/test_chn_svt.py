# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestSvtChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestSvtChannel, self).__init__(methodName, "channel.se.svt", "svt")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 13, "No items found in mainlist")

    def test_main_program_list(self):
        url = "https://api.svt.se/contento/graphql?operationName=ProgramsListing&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%2217252e11da632f5c0d1b924b32be9191f6854723a0f50fb2adb35f72bb670efa%22%7D%7D&ua=svtplaywebb-play-render-prod-client"
        item = self._get_media_item(url, "TV Shows")
        item.metaData["list_type"] = "folders"
        result = self.channel.process_folder_list(item)
        self.assertGreater(len(result), 10)

    def test_video_list_for_show(self):
        show_item = self._get_media_item("#program_item")
        show_item.metaData["slug"] = "/aktuellt"
        items = self.channel.process_folder_list(show_item)
        self.assertGreaterEqual(2, len(items))

    def test_list_for_genre_barn(self):
        show_item = self._get_media_item("#genre_item")
        show_item.metaData["genre_id"] = "barn"
        items = self.channel.process_folder_list(show_item)
        self.assertGreater(len([i for i in items if i.is_folder]), 10)
        self.assertGreater(len([i for i in items if i.is_playable]), 10)

    def test_genre_recent_news(self):
        url = ("https://api.svt.se/contento/graphql?operationName=CategoryPageQuery&variables=%7B"
               "%22id%22%3A%22nyheter%22%2C%22includeFullOppetArkiv%22%3Atrue%2C%22tab%22%3A%22all"
               "%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22"
               "00be06320342614f4b186e9c7710c29a7fc235a1936bde08a6ab0f427131bfaf%22%2C"
               "%22version%22%3A1%7D%7D&ua=svtplaywebb-render-low-prio-client")
        self._test_folder_url(url, expected_results=4)

    def test_new_on_svt(self):
        url = "https://api.svt.se/contento/graphql?operationName=FionaPage&variables=%7B%22includeFullOppetArkiv%22%3Atrue%2C%22selectionId%22%3A%22svtId_egWQ3y7%22%2C%22userIsAbroad%22%3Atrue%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22dc8f85e195903fe6227a76ec1e1d300d470ee8ea123bea6bee26215cc6e4959d%22%2C%22version%22%3A1%7D%7D&ua=svtplaywebb-render-low-prio-client"
        self._test_folder_url(url, expected_results=4)

    def test_latest_news(self):
        url = "https://api.svt.se/contento/graphql?operationName=CategoryPageQuery&variables=%7B%22id%22%3A%20%22nyheter%22%2C%20%22includeFullOppetArkiv%22%3A%20true%2C%20%22tab%22%3A%20%22all%22%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%2200be06320342614f4b186e9c7710c29a7fc235a1936bde08a6ab0f427131bfaf%22%7D%7D&ua=svtplaywebb-play-render-prod-client"
        self._test_folder_url(url, expected_results=4)

    def test_most_viewed(self):
        url = "https://api.svt.se/contento/graphql?operationName=GridPage&variables=%7B%22includeFullOppetArkiv%22%3Atrue%2C%22selectionId%22%3A%22popular_start%22%2C%22userIsAbroad%22%3Atrue%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40%22%2C%22version%22%3A1%7D%7D"
        self._test_folder_url(url, expected_results=10)

    # Now only in HTML embedded
    def test_currently_playing(self):
        url = "https://api.svt.se/contento/graphql?operationName=GridPage&variables=%7B%22includeFullOppetArkiv%22%3Atrue%2C%22selectionId%22%3A%22live_start%22%2C%22userIsAbroad%22%3Atrue%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40%22%2C%22version%22%3A1%7D%7D"
        self._test_folder_url(url, expected_results=10)

    def test_genre_tags_listing(self):
        url = "https://api.svt.se/contento/graphql?ua=svtplaywebb-play-render-prod-client&operationName=AllGenres&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%226bef51146d05b427fba78f326453127f7601188e46038c9a5c7b9c2649d4719c%22%7D%7D"
        self._test_folder_url(url, expected_results=10)

    # Now only in HTML embedded.
    def test_last_chance(self):
        url = "https://api.svt.se/contento/graphql?operationName=GridPage&variables=%7B%22includeFullOppetArkiv%22%3A%20true%2C%20%22selectionId%22%3A%20%22lastchance_start%22%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%22a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40%22%7D%7D&ua=svtplaywebb-play-render-prod-client"
        self._test_folder_url(url, expected_results=10)

    def test_single_episodes(self):
        url = "https://api.svt.se/contento/graphql?operationName=ProgramsListing&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%2217252e11da632f5c0d1b924b32be9191f6854723a0f50fb2adb35f72bb670efa%22%7D%7D&ua=svtplaywebb-play-render-prod-client"
        item = self._get_media_item(url, "Singles")
        item.metaData["list_type"] = "videos"
        result = self.channel.process_folder_list(item)
        self.assertGreater(len(result), 10)

    def test_recent_listing(self):
        url = "https://api.svt.se/contento/graphql?operationName=GridPage&variables=%7B%22includeFullOppetArkiv%22%3Atrue%2C%22selectionId%22%3A%22latest_start%22%2C%22userIsAbroad%22%3Atrue%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40%22%2C%22version%22%3A1%7D%7D&ua=svtplaywebb-render-low-prio-client"
        self._test_folder_url(url, expected_results=10)

    def test_api_video_update(self):
        url = "https://api.svt.se/videoplayer-api/video/e2DDJzo"
        item = self._test_video_url(url)
        self.assertIsNotNone(item)

    def test_html_video_update(self):
        url = "https://www.svtplay.se/video/33718658/anders-matresa/anders-matresa-bjorn-i-harjedalen?info=visa"
        item = self._test_video_url(url)
        self.assertTrue(item.url.endswith("jp9dDmp"))
