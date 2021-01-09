# SPDX-License-Identifier: GPL-3.0-or-later

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
