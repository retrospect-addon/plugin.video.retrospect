# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from . channeltest import ChannelTest


class TestRtlXLChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestRtlXLChannel, self).__init__(methodName, "channel.rtlnl.rtl", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 20)

    def test_main_program(self):
        url = "https://api.rtl.nl/rtlxl/related/api/related/366335"
        self._test_folder_url(url, 5)

    def test_day_listing(self):
        url = "https://api.rtl.nl/rtlxl/missed/api/missed?dayOffset=1"
        self._test_folder_url(url, 5)

    @unittest.skipIf("RTLXL_USERNAME" not in os.environ, "Skipping due to missing username/password")
    def test_video_update(self):
        url = "https://api.rtl.nl/watch/play/api/play/xl/0f2c7de3-881b-4467-ba3f-0ca2aabaf718?device=web&drm=widevine&format=dash"
        self._test_video_url(url)
