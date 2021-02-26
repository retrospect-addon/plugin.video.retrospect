# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from . channeltest import ChannelTest


class TestMtvNlChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestMtvNlChannel, self).__init__(methodName, "channel.mtv.mtvnl", "mtvde")

    def test_channel_mtv_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_mtv_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 50)

    @unittest.skipIf("CI" in os.environ, "Skipping in CI due to Geo-Restrictions")
    def test_clip(self):
        url = "https://media-utils.mtvnservices.com/services/MediaGenerator/mgid:arc:video:mtv.nl:daf4a238-4417-4b3f-9bcd-097dce3920fe?arcStage=live&format=json&acceptMethods=hls&clang=nl&https=true"
        self._test_video_url(url)

    def test_season_folders(self):
        url = "https://www.mtv.de/feeds/intl_m112/V8_0_0/62701278-3c80-4ef6-a801-1df8ffca7c78/7a4914c2-d237-11e1-a549-0026b9414f30"

        item = self._get_media_item(url)
        item.metaData["guid"] = '7a4914c2-d237-11e1-a549-0026b9414f30'
        items = self.channel.process_folder_list(item)

        seasons = [s for s in items if s.type == "folder" and s.name.startswith("\a")]
        self.assertGreaterEqual(len(seasons), 1)
