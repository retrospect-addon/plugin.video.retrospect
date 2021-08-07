# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestBvnTvChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestBvnTvChannel, self).__init__(methodName, "channel.nos.bvntv", "bvntv")

    def test_channel_at5_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_at5_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 5)

    def test_episode_listing_show(self):
        url = "https://www.bvn.tv/programma/nos-journaal/"
        self._test_folder_url(url, expected_results=2)

    def test_episode_listing_show_few_results(self):
        url = "https://www.bvn.tv/programma/40-jaar-tv-show/"
        self._test_folder_url(url, expected_results=3)

    def test_episode_listing_show_single_episode(self):
        url = "https://www.bvn.tv/programma/de-gert-hermien-story/"
        self._test_folder_url(url, expected_results=1)

    def test_live_stream(self):
        url = "https://www.bvn.tv/programma/live/LI_BVN_4589107"
        self._test_video_url(url)
