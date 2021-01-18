# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestEspnChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestEspnChannel, self).__init__(methodName, "channel.sports.espn", "espnnl")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 1)

    def test_main_list_sub_buckets(self):
        items = self.channel.process_folder_list(None)
        for item in items:
            self.assertIsInstance(item.metaData["bucket"], list)
            self.assertGreater(len(item.metaData["bucket"]), 1)
            self.assertIsInstance(item.metaData["bucket"][0], dict)

