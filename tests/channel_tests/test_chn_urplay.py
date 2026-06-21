# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from . channeltest import ChannelTest


@unittest.skipIf("CI" in os.environ, "Not working on CI due to GitHub IP blocks.")
class TestUrPlayChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestUrPlayChannel, self).__init__(methodName, "channel.se.urplay", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 2)

    def test_main_tv_show_list(self):
        url = "https://urplay.se/bladdra/alla-program"
        self._test_folder_url(url, 100)

    def test_main_category_list(self):
        url = "https://urplay.se/bladdra/alla-kategorier"
        self._test_folder_url(url, 10)

    def test_video_play(self):
        url = "https://media-api.urplay.se/config-streaming/v1/urplay/sources/175178"
        self._test_video_url(url)

    def test_audio_play(self):
        url = "https://media-api.urplay.se/config-streaming/v1/urplay/sources/220604"
        self._test_video_url(url)

    def test_category_content(self):
        url = "https://urplay.se/bladdra/dokumentar"
        items = self._test_folder_url(url, 10) or []
        self.assertGreaterEqual(len(items[0].items), 1)

    def test_show_with_only_video(self):
        url = "https://urplay.se/api/v1/season_episodes?seriesId=220596"
        item = self._get_media_item(url, "Ada löser en tand")
        item.metaData["seasonLink"] = "https://urplay.se/serie/220596-ada-loser-en-tand"
        items = self.channel.process_folder_list(item)

        folders = [i for i in items if i.is_folder]
        self.assertGreaterEqual(len(folders), 0)
        videos = [i for i in items if i.is_playable]
        self.assertGreater(len(videos), 2)

    def test_show_with_seasons(self):
        url = "https://urplay.se/api/v1/season_episodes?seriesId=242456"
        item = self._get_media_item(url, "Lassugen")
        item.metaData["seasonLink"] = "https://urplay.se/serie/242456-lassugen"
        items = self.channel.process_folder_list(item)

        folders = [i for i in items if i.is_folder]
        self.assertGreaterEqual(len(folders), 2)
        videos = [i for i in items if i.is_playable]
        self.assertEqual(len(videos), 0)
