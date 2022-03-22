# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import unittest

from . channeltest import ChannelTest


class TestRegioGroei(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestRegioGroei, self).__init__(methodName, "channel.regionalnl.regiogroei", "rtvutrecht")

    def test_rtv_utrecht_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_rtv_utrecht_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    def test_rtv_utrecht_video_list(self):
        url = "https://api.regiogroei.cloud/page/program/RTVU_2190407?slug=binnenstebuiten&origin=RTVU_2190407"
        self._test_folder_url(url, expected_results=2)

    def test_rtv_utrecht_video(self):
        url = "https://api.regiogroei.cloud/page/episode/RTVU_2190428"
        self._test_video_url(url)

    def test_rtv_utrecht_video_auto_birate(self):
        url = "https://api.regiogroei.cloud/page/episode/RTVU_2213398"
        item = self._test_video_url(url)

        item.streams.sort(key=lambda s: s.Bitrate)
        highest = item.streams[-1]
        self.assertTrue("m3u8" in highest.Url)

    def test_rtv_utrecht_day(self):
        today = datetime.datetime.now() - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        url = "https://api.regiogroei.cloud/programs/rtv-utrecht?startDate=" \
              "{:04d}-{:02d}-{:02d}&endDate={:04d}-{:02d}-{:02d}".\
            format(today.year, today.month, today.day, tomorrow.year, tomorrow.month, tomorrow.day)
        self._test_folder_url(url, expected_results=1)

    def test_rtv_utrecht_live(self):
        url = "https://api.regiogroei.cloud/page/channel/rtv-utrecht?channel=rtv-utrecht"
        self._test_video_url(url)

    # Zeeland stuff
    def test_zeeland_channel_exists(self):
        channel = self._switch_channel("omroepzeeland")
        self.assertIsNotNone(channel)

    def test_zeeland_main_list(self):
        self._switch_channel("omroepzeeland")
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 25)

    def test_zeeland_video_listing(self):
        self._switch_channel("omroepzeeland")
        url = "https://api.regiogroei.cloud/page/program/370060057?slug=binnenstebuiten&origin=370060057"
        self._test_folder_url(url, expected_results=10)

    def test_zeeland_video(self):
        self._switch_channel("omroepzeeland")
        url = "https://api.regiogroei.cloud/page/episode/370275114"
        self._test_video_url(url)

    def test_zeeland_live(self):
        self._switch_channel("omroepzeeland")
        url = "https://api.regiogroei.cloud/page/channel/omroep-zeeland-tv?channel=omroep-zeeland-tv"
        self._test_video_url(url)

    def test_zeeland_day(self):
        self._switch_channel("omroepzeeland")
        today = datetime.datetime.now() - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        url = "https://api.regiogroei.cloud/programs/omroep-zeeland-tv?startDate=" \
              "{:04d}-{:02d}-{:02d}&endDate={:04d}-{:02d}-{:02d}". \
            format(today.year, today.month, today.day, tomorrow.year, tomorrow.month, tomorrow.day)
        self._test_folder_url(url, expected_results=2)

    # RTV Noord
    def test_rtv_noord_channel_exists(self):
        channel = self._switch_channel("rtvnoord")
        self.assertIsNotNone(channel)

    def test_rtv_noord_mainlist(self):
        self._switch_channel("rtvnoord")

    def test_rtv_noord_video_listing(self):
        self._switch_channel("rtvnoord")
        url = "https://api.regiogroei.cloud/page/program/10010?slug=noord-vandaag&origin=10010"
        self._test_folder_url(url, expected_results=20)

    def test_rtv_noord_video(self):
        self._switch_channel("rtvnoord")
        url = "https://api.regiogroei.cloud/page/episode/98895891574E99E5C12587E8003F0CD3"
        item = self._test_video_url(url)
        self.assertFalse(item.isLive)

    def test_rtv_noord_live(self):
        self._switch_channel("rtvnoord")
        url = "https://api.regiogroei.cloud/page/channel/tv-noord?channel=tv-noord"
        live_item = self._test_video_url(url)
        self.assertTrue(live_item.isLive)

    @unittest.skipIf(
        datetime.datetime.now() < datetime.datetime(year=2022, month=2, day=1),
        "Skipping for a month as it seems that all are unavailable.")
    def test_rtv_noord_day(self):
        self._switch_channel("rtvnoord")
        today = datetime.datetime.now() - datetime.timedelta(days=2)
        tomorrow = today + datetime.timedelta(days=1)

        url = "https://api.regiogroei.cloud/programs/tv-noord?startDate=" \
              "{:04d}-{:02d}-{:02d}&endDate={:04d}-{:02d}-{:02d}". \
            format(today.year, today.month, today.day, tomorrow.year, tomorrow.month, tomorrow.day)
        self._test_folder_url(url, expected_results=1)

    # RTV Rijnmond
    def test_rijnmond_channel_exists(self):
        channel = self._switch_channel("rtvrijnmond")
        self.assertIsNotNone(channel)

    def test_rijnmond_mainlist(self):
        self._switch_channel("rtvrijnmond")
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 20)

    def test_rijnmond_video_list(self):
        self._switch_channel("rtvrijnmond")
        url = "https://api.regiogroei.cloud/page/program/tvnws?slug=rijnmond-vandaag&origin=tvnws"
        self._test_folder_url(url, expected_results=10)

    def test_rijnmond_video_update(self):
        self._switch_channel("rtvrijnmond")
        url = "https://api.regiogroei.cloud/page/episode/32738"
        item = self._test_video_url(url)
        self.assertFalse(item.isLive)

    def test_rijnmond_live(self):
        self._switch_channel("rtvrijnmond")
        url = "https://api.regiogroei.cloud/page/channel/tv-rijnmond?channel=tv-rijnmond"
        live_item = self._test_video_url(url)
        self.assertTrue(live_item.isLive)

    def test_rijnmond_day(self):
        self._switch_channel("rtvrijnmond")
        today = datetime.datetime.now() - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        url = "https://api.regiogroei.cloud/programs/tv-rijnmond?startDate=" \
              "{:04d}-{:02d}-{:02d}&endDate={:04d}-{:02d}-{:02d}". \
            format(today.year, today.month, today.day, tomorrow.year, tomorrow.month, tomorrow.day)
        self._test_folder_url(url, expected_results=1)

    # RTV West
    def test_tv_west_channel_exists(self):
        channel = self._switch_channel("omroepwest")
        self.assertIsNotNone(channel)

    def test_tv_west_mainlist(self):
        self._switch_channel("omroepwest")
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 20)

    def test_tv_westd_video_list(self):
        self._switch_channel("omroepwest")
        url = "https://api.regiogroei.cloud/page/program/170000115?slug=tv-west-nieuws&origin=170000115"
        self._test_folder_url(url, expected_results=10)

    def test_tv_westd_video_update(self):
        self._switch_channel("omroepwest")
        url = "https://api.regiogroei.cloud/page/episode/170392546?slug=tv-west-nieuws&origin=170392546"
        item = self._test_video_url(url)
        self.assertFalse(item.isLive)

    def test_tv_west_live(self):
        self._switch_channel("omroepwest")
        url = "https://api.regiogroei.cloud/page/channel/tv-west?channel=tv-west"
        live_item = self._test_video_url(url)
        self.assertTrue(live_item.isLive)

    def test_tv_west_day(self):
        self._switch_channel("omroepwest")
        today = datetime.datetime.now() - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        url = "https://api.regiogroei.cloud/programs/tv-west?startDate=" \
              "{:04d}-{:02d}-{:02d}&endDate={:04d}-{:02d}-{:02d}". \
            format(today.year, today.month, today.day, tomorrow.year, tomorrow.month, tomorrow.day)
        self._test_folder_url(url, expected_results=1)

    # TV gelderland
    def test_omroepgelderland_channel_exists(self):
        channel = self._switch_channel("omroepgelderland")
        self.assertIsNotNone(channel)

    def test_omroepgelderland_mainlist(self):
        self._switch_channel("omroepgelderland")
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 20)

    def test_omroepgelderland_show_list(self):
        self._switch_channel("omroepgelderland")
        url = "https://api.regiogroei.cloud/page/program/83"
        self._test_folder_url(url, expected_results=10)

    def test_omroepgelderland_news_listing(self):
        self._switch_channel("omroepgelderland")
        url = "https://api.regiogroei.cloud/page/program/31"
        self._test_folder_url(url, expected_results=20)

    def test_omroepgelderland_video(self):
        self._switch_channel("omroepgelderland")
        url = "https://api.regiogroei.cloud/page/episode/101616?slug=gld-nieuws&origin=101616"
        self._test_video_url(url)

    def test_omroepgelderland_live_streams(self):
        self._switch_channel("omroepgelderland")
        live_url = "https://api.regiogroei.cloud/page/channel/tv-gelderland?channel=tv-gelderland"
        items = self._test_video_url(live_url)

    # TV Oost
    def test_tvoost_channel_exists(self):
        channel = self._switch_channel("rtvoost")
        self.assertIsNotNone(channel)

    def test_tvoost_mainlist(self):
        self._switch_channel("rtvoost")
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 20)

    def test_tvoost_show_list(self):
        self._switch_channel("rtvoost")
        url = "https://api.regiogroei.cloud/page/program/1093?slug=roots&origin=1093"
        self._test_folder_url(url, expected_results=10)

    def test_tvoost_video(self):
        self._switch_channel("rtvoost")
        url = "https://api.regiogroei.cloud/page/episode/557418?slug=roots&origin=557418"
        self._test_video_url(url)

    def test_tvoost_live_streams(self):
        self._switch_channel("rtvoost")
        live_url = "https://api.regiogroei.cloud/page/channel/tv-oost?channel=tv-oost"
        items = self._test_video_url(live_url)
