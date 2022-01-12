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
            "%22265677a2465d93d39b536545cdc3664d97e3843ce5e34f145b2a45813b85007b%22%7D%7D", 7)

    def test_video_list(self):
        self._test_folder_url(
            "https://api.svt.se/contento/graphql?ua=svtplaywebb-play-render-prod-client&operation"
            "Name=GridPage&variables=%7B%22selectionId%22%3A%20%22popular%22%7D&extensions=%7B%22"
            "persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%22265677"
            "a2465d93d39b536545cdc3664d97e3843ce5e34f145b2a45813b85007b%22%7D%7D", 5)

    def test_recent_news(self):
        url = "https://api.svt.se/contento/graphql?ua=svtplaywebb-play-render-prod-client&" \
              "operationName=GenreLists&variables=%7B%22genre%22%3A%20%5B%22nyheter%22%5D%7D&" \
              "extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash" \
              "%22%3A%20%2290dca0b51b57904ccc59a418332e43e17db21c93a2346d1c73e05583a9aa598c%22%7D%7D"
        self._test_folder_url(url, expected_results=4)

    def test_api_video_update(self):
        url = "https://api.svt.se/videoplayer-api/video/e2DDJzo"
        item = self._test_video_url(url)
        self.assertIsNotNone(item)

    def test_html_video_update(self):
        url = "https://www.svtplay.se/video/24060250/i-am-patrick-swayze"
        item = self._test_video_url(url)
        self.assertTrue(item.url.endswith("82mMLWX"))
