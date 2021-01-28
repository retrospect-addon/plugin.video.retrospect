# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestVierBeChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestVierBeChannel, self).__init__(methodName, "channel.be.vier", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 20, "No items found in mainlist")
