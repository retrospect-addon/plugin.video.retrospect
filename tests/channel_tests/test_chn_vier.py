# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import os
import unittest

from resources.lib.addonsettings import AddonSettings
from . channeltest import ChannelTest


class TestVierBeChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestVierBeChannel, self).__init__(methodName, "channel.be.vier", "playtv")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list_vier(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")

    def test_go_play_tv_show(self):
        url = "https://www.play.tv/vik-gert"
        self._test_folder_url(url, 5)

    def test_recent_day_list(self):
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        url = f"https://www.play.tv/tv-gids/play/{yesterday.year}-{yesterday.month:02d}-{yesterday.day:02d}"
        self._test_folder_url(url, 5)

    @unittest.skipIf("PLAY_TV_TOKEN" not in os.environ, "Not testing updating without credentials")
    def test_go_play_video_in_main_list(self):
        token = os.environ["PLAY_TV_TOKEN"]
        AddonSettings.set_setting("viervijfzes_refresh_token", token)
        url = "https://www.play.tv/video/killer-in-law"
        self._test_video_url(url)

    @unittest.skipIf("PLAY_TV_TOKEN" not in os.environ, "Not testing updating without credentials")
    def test_video_url(self):
        token = os.environ["PLAY_TV_TOKEN"]
        AddonSettings.set_setting("viervijfzes_refresh_token", token)
        url = "https://www.play.tv/video/vik-gert/vik-gert-s1/vik-gert-s1-aflevering-12"
        self._test_video_url(url)
