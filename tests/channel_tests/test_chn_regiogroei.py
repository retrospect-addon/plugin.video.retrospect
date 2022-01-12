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
        self._test_folder_url(url, expected_results=2)

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
        url = "https://api.regiogroei.cloud/page/episode/C4915464A4E0AD8CC12587820042AB5C"
        self._test_video_url(url)

    def test_rtv_noord_live(self):
        self._switch_channel("rtvnoord")
        url = "https://api.regiogroei.cloud/page/channel/tv-noord?channel=tv-noord"
        self._test_video_url(url)

        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 5)

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
        self._test_folder_url(url, expected_results=2)
