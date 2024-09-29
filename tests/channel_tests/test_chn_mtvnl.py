# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from . channeltest import ChannelTest


@unittest.skip("Broken channel: no more videos")
class TestMtvNlChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestMtvNlChannel, self).__init__(methodName, "channel.nick.nickelodeon", "mtvnl")

    def test_channel_mtv_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_mtv_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 25)

    def test_folder(self):
        url = "https://www.mtv.nl/shows/teen-mom-young-pregnant"
        self._test_folder_url(url, expected_results=3)

    @unittest.skipIf("CI" in os.environ, "Skipping in CI due to Geo-Restrictions")
    def test_video(self):
        # url = "https://www.mtv.nl/clip/4jnx08/teen-mom-young-pregnant-teen-mom-young-pregnant-ik-denk-niet-dat-ze-er-klaar-voor-is"
        url = "https://topaz.viacomcbs.digital/topaz/api/mgid:arc:showvideo:mtv.nl:94baade0-7d7f-4982-a2ad-a9f9b0276c39/mica.json?clientPlatform=desktop&ssus=44545c3d-6208-45e5-953e-801abf27ae7b&browser=Chrome&device=Desktop&os=Windows+10"
        self._test_video_url(url)
