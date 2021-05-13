# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestNosChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNosChannel, self).__init__(methodName, "channel.nos.nosnl", "nosnl")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 4, "No items found in mainlist")

    def test_most_viewed_items(self):
        url = "https://api.nos.nl/mobile/videos/most-viewed/phone.json"
        self._test_folder_url(url, expected_results=10)

    def test_video_update(self):
        url = "https://api.nos.nl/mobile/video/2380242/phone.json"
        from resources.lib.mediaitem import MediaItem
        item = self._test_video_url(url)    # type: MediaItem

        for stream in [s for s in item.streams if "hls" in s.Url]:
            self.assertTrue("cdn.streamgate.nl" in stream.Url)
