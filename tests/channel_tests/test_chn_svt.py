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
        self._test_folder_url(
            "https://api.svt.se/contento/graphql?ua=svtplaywebb-play-render-prod-client&"
            "operationName=GridPage&variables=%7B%22selectionId%22%3A%20%22latest%22%7D&extensions="
            "%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20"
            "%22b30578b1b188242ce190c8a2cefe3d4694efafd17a929d08d273ae224a302b24%22%7D%7D", 7)

    def test_video_list_for_show(self):
        show_item = self._get_media_item("#program_item")
        show_item.metaData["slug"] = "/aktuellt"
        items = self.channel.process_folder_list(show_item)
        self.assertGreater(len(items), 4)

    def test_list_for_genre(self):
        show_item = self._get_media_item("#genre_item")
        show_item.metaData["genre_id"] = "barn"
        items = self.channel.process_folder_list(show_item)
        self.assertGreater(len([i for i in items if i.is_folder]), 10)
        self.assertGreater(len([i for i in items if i.is_playable]), 10)

    def test_genre_recent_news(self):
        url = "https://api.svt.se/contento/graphql?ua=svtplaywebb-play-render-prod-client&" \
              "operationName=GenreLists&variables=%7B%22genre%22%3A%20%5B%22nyheter%22%5D%7D&" \
              "extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash" \
              "%22%3A%20%2290dca0b51b57904ccc59a418332e43e17db21c93a2346d1c73e05583a9aa598c%22%7D%7D"
        self._test_folder_url(url, expected_results=4)

    def test_new_on_svt(self):
        url = "https://api.svt.se/contento/graphql?ua=svtplaywebb-play-render-prod-client&" \
              "operationName=StartPage&variables=%7B%22abTestVariants%22%3A%20%5B%5D%2C%20%22" \
              "includeFullOppetArkiv%22%3A%20true%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22" \
              "version%22%3A%201%2C%20%22sha256Hash" \
              "%22%3A%20%22b2a022f7353fbe891696aacd173a74c964a5f382f6f9153f0fcf129cecd4b9ac%22%7D%7D"
        self._test_folder_url(url, expected_results=4)

    def test_api_video_update(self):
        url = "https://api.svt.se/videoplayer-api/video/e2DDJzo"
        item = self._test_video_url(url)
        self.assertIsNotNone(item)

    def test_html_video_update(self):
        url = "https://www.svtplay.se/video/33718658/anders-matresa/anders-matresa-bjorn-i-harjedalen?info=visa"
        item = self._test_video_url(url)
        self.assertTrue(item.url.endswith("jp9dDmp"))
