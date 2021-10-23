# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestMtvDeChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestMtvDeChannel, self).__init__(methodName, "channel.nick.nickelodeon", "mtvde")

    def test_channel_mtvde_exists(self):
        self.assertIsNotNone(self.channel)

    def test_channel_mtvde_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 25)

    def test_video_list(self):
        url = "https://www.mtv.de/serien/jersey-shore-family-vacation"
        self._test_folder_url(url, expected_results=4)

    def test_video(self):
        url = "https://www.mtv.de/folgen/qbpkgz/jersey-shore-family-vacation-snooki-geht-nach-washington-teil-eins-staffel-3-ep-13"
        self._test_video_url(url)

    def test_list_with_seasons(self):
        url = "https://www.mtv.de/serien/jersey-shore-family-vacation"
        items = self._test_folder_url(url, expected_results=4)
        folders = [i for i in items if i.media_type == "season"]
        self.assertGreater(len(folders), 0)
