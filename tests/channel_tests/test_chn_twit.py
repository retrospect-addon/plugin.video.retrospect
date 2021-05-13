# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestTwitChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestTwitChannel, self).__init__(methodName, "channel.videos.twit", "twit")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    def test_video_listing(self):
        url = "https://twit.tv/shows/windows-weekly"
        self._test_folder_url(url, expected_results=6)

    def test_video_listing_for_page(self):
        url = "https://twit.tv/episodes?filter%5Bshows%5D=1645"
        items = self._test_folder_url(url, expected_results=6)

        pages = [p for p in items if p.is_folder]
        self.assertGreaterEqual(len(pages), 1)

    def test_video_listing_for_page_2(self):
        url = "https://twit.tv/list/episodes?page=2&filter%5Bshows%5D=1645"
        items = self._test_folder_url(url, expected_results=6)

        pages = [p for p in items if p.is_folder]
        self.assertGreaterEqual(len(pages), 1)

    def test_video(self):
        url = "https://twit.tv/shows/windows-weekly/episodes/721?autostart=false"
        self._test_video_url(url)
