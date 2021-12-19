# SPDX-License-Identifier: GPL-3.0-or-later
import datetime

from . channeltest import ChannelTest


class TestRegioGroei(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestRegioGroei, self).__init__(methodName, "channel.regionalnl.regiogroei", "rtvutrecht")

    def test_channel_exists_utrecht(self):
        self.assertIsNotNone(self.channel)

    def test_main_list_utrecht(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    def test_video_list(self):
        url = "https://api.regiogroei.cloud/page/program/RTVU_2190407?slug=binnenstebuiten&origin=RTVU_2190407"
        self._test_folder_url(url, expected_results=2)

    def test_video(self):
        url = "https://rtvutrecht.bbvms.com/p/regiogroei_utrecht_web_videoplayer/c/4456927.json"
        self._test_video_url(url)

    def test_video_auto_birate(self):
        url = "https://rtvutrecht.bbvms.com/p/regiogroei_utrecht_web_videoplayer/c/4464173.json"
        self._test_video_url(url)

    def test_day_utrecht(self):
        today = datetime.datetime.now() - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        url = "https://api.regiogroei.cloud/programs/rtv-utrecht?startDate=" \
              "{:04d}-{:02d}-{:02d}&endDate={:04d}-{:02d}-{:02d}".\
            format(today.year, today.month, today.day, tomorrow.year, tomorrow.month, tomorrow.day)
        self._test_folder_url(url, expected_results=2)

    def test_live_utrecht(self):
        url = "https://rtvutrecht.bbvms.com/p/regiogroei_utrecht_web_videoplayer/c/3742011.json"
        self._test_video_url(url)

    # Zeeland stuff
    def test_channel_exists_zeeland(self):
        channel = self._switch_channel("omroepzeeland")
        self.assertIsNotNone(channel)

    def test_main_list_zeeland(self):
        self._switch_channel("omroepzeeland")
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 25)

    def test_video_listing_zeeland(self):
        self._switch_channel("omroepzeeland")
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    def test_video_zeeland(self):
        self._switch_channel("omroepzeeland")
        url = "https://omroepzeeland.bbvms.com/p/regiogroei_zeeland_web_videoplayer/c/sourceid_string:370275114-Code-Groen-28-09-2021-ZNB210914DY.json"
        self._test_video_url(url)

    def test_video_zeeland_should_load_no_source_id(self):
        self._switch_channel("omroepzeeland")
        url = "https://omroepzeeland.bbvms.com/p/regiogroei_zeeland_web_videoplayer/c/sourceid_string:2430771.json"
        self._test_video_url(url)

    def test_live_zeeland(self):
        self._switch_channel("omroepzeeland")
        url = "https://omroepzeeland.bbvms.com/p/regiogroei_zeeland_web_videoplayer/c/3745936.json"
        self._test_video_url(url)

    def test_day_zeeland(self):
        self._switch_channel("omroepzeeland")
        today = datetime.datetime.now() - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        url = "https://api.regiogroei.cloud/programs/omroep-zeeland-tv?startDate=" \
              "{:04d}-{:02d}-{:02d}&endDate={:04d}-{:02d}-{:02d}". \
            format(today.year, today.month, today.day, tomorrow.year, tomorrow.month, tomorrow.day)
        self._test_folder_url(url, expected_results=2)

