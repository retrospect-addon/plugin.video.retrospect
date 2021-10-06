# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestMtvDeChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestMtvDeChannel, self).__init__(methodName, "channel.mtv.mtvnl", "mtvde")

    def test_channel_mtv_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_mtv_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 25)

    def test_video_list(self):
        url = "http://www.mtv.de/feeds/intl_m112/V8_0_0/62701278-3c80-4ef6-a801-1df8ffca7c78/90a54067-9c44-434f-a063-c06232cf047d"
        self._test_folder_url(url, expected_results=4)
