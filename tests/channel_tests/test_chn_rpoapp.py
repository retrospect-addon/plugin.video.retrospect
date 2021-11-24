# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestRpoAppChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestRpoAppChannel, self).__init__(methodName, "channel.regionalnl.rpoapp", "rtvutrecht")

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

    def test_update_via_javascript_zeeland(self):
        self._switch_channel("omroepzeeland")
        url = "https://www.omroepzeeland.nl/media/bluebillywigplayeroptions/rtv/Tv/370081782.json"
        self._test_video_url(url)

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

    def test_channel_exists_rijnmond(self):
        channel = self._switch_channel("rtvrijnmond")
        self.assertIsNotNone(channel)

    def test_mainlist_rijnmond(self):
        self._switch_channel("rtvrijnmond")
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 20)

    def test_video_list_rijnmond(self):
        self._switch_channel("rtvrijnmond")
        url = "https://www.rijnmond.nl/RadioTv/Results?medium=Tv&query=&category=b5663f4d-8529-49ed-b1d0-b6745e064a3c&from=&to=&page=1"
        self._test_folder_url(url, expected_results=10)

    def test_video_update_rijnmond(self):
        self._switch_channel("rtvrijnmond")
        url = "https://www.rijnmond.nl/media/bluebillywigplayeroptions/rtv/Tv/31699.json"
        self._test_video_url(url)

    def test_live_rijnmond(self):
        self._switch_channel("rtvrijnmond")
        url = "https://rijnmond.rpoapp.nl/v01/livestreams/AndroidTablet.json"
        items = self._test_folder_url(url, expected_results=2)
        self.assertGreaterEqual(len([i for i in items if i.isLive]), 3)
