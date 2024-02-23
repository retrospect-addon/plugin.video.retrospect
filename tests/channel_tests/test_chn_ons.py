# SPDX-License-Identifier: GPL-3.0-or-later
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.urihandler import UriHandler
from . channeltest import ChannelTest


class TestOnsChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestOnsChannel, self).__init__(methodName, "channel.videos.ons", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 8, "No items found in mainlist")

    def test_folder(self):
        data = UriHandler.open(self.channel.mainListUri)
        data = JsonHelper(data)
        folder_id = data.get_value(0, "folder", "id")

        self._test_folder_url(self.channel.mainListUri, 1,
                              parser="folder", meta={"folder_id": folder_id})

    def test_video(self):
        data = UriHandler.open(self.channel.mainListUri)
        data = JsonHelper(data)
        clip_id = data.get_value(0, "id")
        self._test_video_url(f"http://api.ibbroadcast.nl/clips.ashx?key={self.channel.api_key}&mode=getclip&id={clip_id}&output=json")