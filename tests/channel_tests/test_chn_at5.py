# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestAt5Channel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestAt5Channel, self).__init__(methodName, "channel.regionalnl.at5", None)

    def test_channel_at5_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_at5_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 5)

    def test_channel_at5_show_folder(self):
        url = "https://ditisdesupercooleappapi.at5.nl/api/article/p450"
        self._test_folder_url(url, expected_results=3)

    def test_channel_at5_video_resolving(self):
        url = "https://ditisdesupercooleappapi.at5.nl/api/article/p450"
        items = self._test_folder_url(url, expected_results=3)
        self._test_video_url(items[0].url)

    def test_channel_rtv_noord_holland_exists(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        self.channel = ChannelIndex.get_register().get_channel(self._channel, "rtvnh")
        self.assertIsNotNone(self.channel)

    def test_channel_rtv_noord_holland_main_list(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        self.channel = ChannelIndex.get_register().get_channel(self._channel, "rtvnh")
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)

    def test_channel_rtv_noord_show_folder(self):
        url = "https://ditisdesupercooleappapi.nhnieuws.nl/api/article/256024"
        self._test_folder_url(url, expected_results=20)

    def test_channel_rtv_noord_video_resolving(self):
        url = "https://ditisdesupercooleappapi.nhnieuws.nl/api/article/256024"
        items = self._test_folder_url(url, expected_results=20)
        self._test_video_url(items[0].url)
