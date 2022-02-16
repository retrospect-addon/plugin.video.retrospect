# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestVrtNuChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestVrtNuChannel, self).__init__(methodName, "channel.be.vrtnu", "vrtnu")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 120, "No items found in mainlist")

    def test_videos(self):
        url = "https://www.vrt.be/vrtnu/a-z/4ever/"
        items = self._test_folder_url(url, expected_results=10)
        videos = [v for v in items if not v.is_folder]
        self.assertGreaterEqual(len(videos), 1)

    def test_folder(self):
        url = "https://www.vrt.be/vrtnu/a-z/4ever/"
        items = self._test_folder_url(url, expected_results=10)
        folders = [f for f in items if f.is_folder]
        self.assertGreaterEqual(len(folders), 1)
