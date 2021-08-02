# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestRpoAppChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestRpoAppChannel, self).__init__(methodName, "channel.regionalnl.rpoapp", "rtvutrecht")

    def test_channel_exists_utrecht(self):
        self.assertIsNotNone(self.channel)

    def test_main_list_utrecht(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    def test_video_listing_utrecht(self):
        url = "https://www.rtvutrecht.nl/gemist/uitzending/rtvutrecht/unieuws/"
        self._test_folder_url(url, expected_results=20)

    def test_video_utrecht(self):
        url = "https://www.rtvutrecht.nl/gemist/uitzending/rtvutrecht/unieuws/20210503-1700/"
        self._test_video_url(url)

    def test_channel_exists_zeeland(self):
        channel = self._switch_channel("omroepzeeland")
        self.assertIsNotNone(channel)

    def test_main_list_zeeland(self):
        self._switch_channel("omroepzeeland")
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 25)

    def test_video_listing_zeeland(self):
        self._switch_channel("omroepzeeland")
        url = "https://www.omroepzeeland.nl/RadioTv/Results?medium=Tv&query=&category=9434cdf1-a4ac-49f9-be67-1964b87613c9&from=&to=&page=1"
        self._test_folder_url(url, expected_results=1)

    def test_video_zeeland(self):
        self._switch_channel("omroepzeeland")
        url = "https://www.omroepzeeland.nl/media/bluebillywigplayeroptions/rtv/Tv/370241386.json"
        self._test_video_url(url)

    def test_live_zeeland(self):
        self._switch_channel("omroepzeeland")
        url = "https://zeeland.rpoapp.nl/v01/livestreams/AndroidTablet.json"
        items = self._test_folder_url(url, expected_results=2)
        self.assertGreaterEqual(len([i for i in items if i.isLive]), 2)

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
