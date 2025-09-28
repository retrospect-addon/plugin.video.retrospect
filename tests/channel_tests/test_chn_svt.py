# SPDX-License-Identifier: GPL-3.0-or-later
import datetime

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
        self.assertGreaterEqual(len(items), 2)

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
               "c51c2c12a390014f864a03a319e89c3e1332cf81cf39ef8f59cd01d1858ec989%22%2C"
               "%22version%22%3A1%7D%7D&ua=svtplaywebb-render-low-prio-client")
        self._test_folder_url(url, expected_results=4)

    def test_new_on_svt(self):
        # url = "https://contento.svt.se/graphql?operationName=FionaPage&variables=%7B%22includeFullOppetArkiv%22%3Atrue%2C%22selectionId%22%3A%22svtId_jGVZ7AL%22%2C%22userIsAbroad%22%3Atrue%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22b4e65a8f4cedc6bd9981e3539690908443f625c6854ea65f18c4b3b3be66b5dc%22%2C%22version%22%3A1%7D%7D&ua=svtplaywebb-render-prod-low-prio-client"
        url = "https://www.svtplay.se"
        self._test_folder_url(url, expected_results=4)

    def test_latest_news(self):
        url = "https://api.svt.se/contento/graphql?operationName=CategoryPageQuery&variables=%7B%22id%22%3A%20%22nyheter%22%2C%20%22includeFullOppetArkiv%22%3A%20true%2C%20%22tab%22%3A%20%22all%22%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%22c51c2c12a390014f864a03a319e89c3e1332cf81cf39ef8f59cd01d1858ec989%22%7D%7D&ua=svtplaywebb-play-render-prod-client"
        self._test_folder_url(url, expected_results=4)

    def test_most_viewed(self):
        url = "https://api.svt.se/contento/graphql?operationName=GridPage&variables=%7B%22includeFullOppetArkiv%22%3Atrue%2C%22selectionId%22%3A%22popular_start%22%2C%22userIsAbroad%22%3Atrue%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40%22%2C%22version%22%3A1%7D%7D"
        self._test_folder_url(url, expected_results=10)

    # Now only in HTML embedded
    def test_currently_playing(self):
        url = "https://api.svt.se/contento/graphql?operationName=GridPage&variables=%7B%22includeFullOppetArkiv%22%3Atrue%2C%22selectionId%22%3A%22live_start%22%2C%22userIsAbroad%22%3Atrue%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40%22%2C%22version%22%3A1%7D%7D"
        self._test_folder_url(url, expected_results=2)

    def test_live_streams(self):
        now = datetime.datetime.now() - datetime.timedelta(hours=6)
        date = "{:04}-{:02}-{:02}".format(now.year, now.month, now.day)
        url = f"https://api.svt.se/contento/graphql?operationName=BroadcastSchedule&variables=%7B%22day%22%3A%22{date}%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22464905fb9c6f51510427f3b913fde66cb43fa5b7f9197bcd13815800758a599b%22%2C%22version%22%3A1%7D%7D&ua=svtplaywebb-render-low-prio-client"
        self._test_folder_url(url, expected_results=3)

    def test_genre_tags_listing(self):
        url = "https://api.svt.se/contento/graphql?operationName=MainGenres&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%2265b3d9bccd1adf175d2ad6b1aaa482bb36f382f7bad6c555750f33322bc2b489%22%7D%7D&ua=svtplaywebb-play-render-prod-client"
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

    def test_category_listing(self):
        item = self._get_media_item("#genre_item", "Genre")
        item.metaData["genre_id"] = "nyheter"
        items = self.channel.process_folder_list(item)
        self.assertGreater(len(items), 10)

    def test_recent_listing(self):
        url = "https://api.svt.se/contento/graphql?operationName=GridPage&variables=%7B%22includeFullOppetArkiv%22%3Atrue%2C%22selectionId%22%3A%22latest_start%22%2C%22userIsAbroad%22%3Atrue%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40%22%2C%22version%22%3A1%7D%7D&ua=svtplaywebb-render-low-prio-client"
        self._test_folder_url(url, expected_results=10)

    def test_api_video_update(self):
        url = "https://api.svt.se/videoplayer-api/video/K5RLm5g"
        item = self._test_video_url(url)
        self.assertIsNotNone(item)

    def test_html_video_update(self):
        url = "https://www.svtplay.se/video/KXYZx9k/utvandrarna/utvandrarna?video=visa"
        item = self._test_video_url(url)
        self.assertTrue(item.url.endswith("KXYZx9k"))
