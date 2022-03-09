# SPDX-License-Identifier: GPL-3.0-or-later

from .channeltest import ChannelTest


class TestLokaalChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestLokaalChannel, self).__init__(methodName, "channel.regionalnl.lokaal", "rtvdrenthe")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_rtvdrenthe_mainlist(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 9)

    def test_omropfryslan_mainlist(self):
        self._switch_channel("omropfryslan")

        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)
