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

    def test_day(self):
        today = datetime.datetime.now()
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        url = "https://api.regiogroei.cloud/programs/rtv-utrecht?startDate=" \
              "{:04d}-{:02d}-{:02d}&endDate={:04d}-{:02d}-{:02d}".\
            format(today.year, today.month, today.day, tomorrow.year, tomorrow.month, tomorrow.day)
        self._test_folder_url(url, expected_results=2)
