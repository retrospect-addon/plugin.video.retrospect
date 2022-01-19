# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestRpoAppChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestRpoAppChannel, self).__init__(methodName, "channel.regionalnl.rpoapp", "rtvutrecht")

    def test_channel_rtvoost(self):
        channel = self._switch_channel("rtvoost")
        self.assertIsNotNone(channel)

    def test_main_list_rtvoost(self):
        self._switch_channel("rtvoost")
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)

    def test_video_list_rtvoost(self):
        self._switch_channel("rtvoost")
        url = "https://www.rtvoost.nl/RadioTv/Results?medium=Radio&query=&category=4f53ab0f-3455-4561-80bc-f8669e32eedd&from=&to=&page=1"
        self._test_folder_url(url, expected_results=1)

    def test_video_update_rtvoost(self):
        self._switch_channel("rtvoost")
        url = "https://www.rtvoost.nl/media/bluebillywigplayeroptions/rtv/Tv/593840.json"
        self._test_video_url(url)

    def test_live_rtvoost(self):
        self._switch_channel("rtvoost")
        url = "https://oost.rpoapp.nl/v02/livestreams/AndroidTablet.json"
        items = self._test_folder_url(url, expected_results=2)
        self.assertGreaterEqual(len([i for i in items if i.isLive]), 3)
