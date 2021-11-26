# SPDX-License-Identifier: GPL-3.0-or-later
from . channeltest import ChannelTest


class TestChannel9Channel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestChannel9Channel, self).__init__(methodName, "channel.videos.channel9", "channel9")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 6)

    def test_video_listing(self):
        url = "https://docs.microsoft.com/api/hierarchy/shows/all-around-azure/episodes?page=0&locale=en-us&pageSize=30&orderBy=uploaddate%20desc"
        self._test_folder_url(url, expected_results=2)

    def test_video_listing_with_levels(self):
        url = "https://docs.microsoft.com/api/hierarchy/shows/learn-live/episodes?page=0&locale=en-us&pageSize=30&orderBy=uploaddate%20desc"
        self._test_folder_url(url, expected_results=2)

    def test_update_video(self):
        url = "https://docs.microsoft.com/api/video/public/v1/entries/batch?ids=8572a0e6-75cb-4608-b7d0-e377671fdd09"
        self._test_video_url(url)

    # def test_channel_shows_folder(self):
    #     url = "https://channel9.msdn.com/Browse/AllShows?sort=atoz"
    #     self._test_folder_url(url, expected_results=16, exact_results=True)
    #
    # def test_channel_show_folder(self):
    #     url = "https://channel9.msdn.com/Shows/5-Things"
    #     self._test_folder_url(url, expected_results=5)
    #
    # def test_channel_event_folder(self):
    #     url = "https://channel9.msdn.com/Browse/Events?sort=atoz"
    #     self._test_folder_url(url, expected_results=8)
    #
    # def test_channel_subevent_folder(self):
    #     url = "https://channel9.msdn.com/Events/Build"
    #     self._test_folder_url(url, expected_results=8)
    #
    # def test_channel_video_resolving(self):
    #     url = "https://channel9.msdn.com/Shows/5-Things/Five-Things-About-Azure-Functions"
    #     self._test_video_url(url)
