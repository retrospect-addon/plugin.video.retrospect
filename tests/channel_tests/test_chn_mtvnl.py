# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from . channeltest import ChannelTest


class TestMtvNlChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestMtvNlChannel, self).__init__(methodName, "channel.mtv.mtvnl", "mtvnl")

    def test_channel_mtv_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_mtv_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 50)

    @unittest.skipIf("CI" in os.environ, "Skipping in CI due to Geo-Restrictions")
    def test_video(self):
        url = "http://media.mtvnservices.com/pmt/e1/access/index.html?uri=mgid:arc:video:mtv.nl:0b0647ff-0795-11eb-834d-70df2f866ace&configtype=edge"
        self._test_video_url(url)

    @unittest.skipIf("CI" in os.environ, "Skipping in CI due to Geo-Restrictions")
    def test_clip(self):
        url = "https://media-utils.mtvnservices.com/services/MediaGenerator/mgid:arc:video:mtv.nl:daf4a238-4417-4b3f-9bcd-097dce3920fe?arcStage=live&format=json&acceptMethods=hls&clang=nl&https=true"
        self._test_video_url(url)

    def test_season_folders(self):
        url = "http://www.mtv.nl/feeds/intl_m112/V8_0_0/62701278-3c80-4ef6-a801-1df8ffca7c78/7a48cd50-d237-11e1-a549-0026b9414f30"

        item = self._get_media_item(url)
        item.metaData["guid"] = "7a48cd50-d237-11e1-a549-0026b9414f30"
        items = self.channel.process_folder_list(item)

        seasons = [s for s in items if s.type == "folder" and s.name.startswith("\a")]
        self.assertGreaterEqual(len(seasons), 1)

    def test_season_videos(self):
        url = "http://www.mtv.nl/feeds/intl_m112/V8_0_0/62701278-3c80-4ef6-a801-1df8ffca7c78/7a48cd50-d237-11e1-a549-0026b9414f30/50f05242-c1a4-11ea-9225-70df2f866ace"
        self._test_folder_url(url, expected_results=1)
