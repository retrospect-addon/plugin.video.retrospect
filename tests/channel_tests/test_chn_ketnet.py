# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestKetNetChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestKetNetChannel, self).__init__(methodName, "channel.be.ketnet", "ketnet")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)

    def test_folder_listing(self):
        program_id = "content/ketnet/nl/kijken/d/de-elfenheuvel.model.json"
        url = "#programId={}".format(program_id)
        item = self._get_media_item(url)
        item.metaData["id"] = program_id

        items = self.channel.process_folder_list(item)
        self.assertGreater(len(items), 10)

    def test_folder_with_sublisting(self):
        program_id = "content/ketnet/nl/kijken/t/trefbal-royale.model.json"
        url = "#programId={}".format(program_id)
        item = self._get_media_item(url)
        item.metaData["id"] = program_id

        items = self.channel.process_folder_list(item)
        self.assertGreaterEqual(len(items), 2)

        item = items[1]
        items = self.channel.process_folder_list(item)
        self.assertGreater(len(items), 5)

    def test_video(self):
        video_id = "content/ketnet/nl/kijken/k/ket-doc/2/vragen-ga-naar-awel-be.model.json"
        url = "#videoId={}".format(video_id)
        item = self._get_media_item(url)
        item.metaData["id"] = video_id

        item = self.channel.process_video_item(item)
        self.assertTrue(item.has_streams())
        self.assertTrue(item.complete)
