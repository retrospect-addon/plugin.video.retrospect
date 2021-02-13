# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestKijkNlChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestKijkNlChannel, self).__init__(methodName, "channel.be.ketnet", "ketnet")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 50)
