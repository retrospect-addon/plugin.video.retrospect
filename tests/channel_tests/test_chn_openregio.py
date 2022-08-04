# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestOpenRegioChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestOpenRegioChannel, self).__init__(methodName, "channel.regionalnl.openregio", "wosnl")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_mainlist(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 20)

    def test_show_listing(self):
        self._test_folder_url(
            "https://media.wos.nl/retrospect/wos/83903f02-9ddf-408e-9a4e-ebcacdbda6a5.json", 5)

    def test_video_update(self):
        self._test_video_url("https://1ab3dwyh2pgi.b-cdn.net/a22a6ac2-0443-4c85-929d-981ef5ae0d6a_1080.mp4")

    def test_studio_040(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "studio040")
        self.assertIsNotNone(chn)
        self.assertEqual("studio040", chn.channelCode)

    def test_studio_040_list(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "studio040")
        items = chn.process_folder_list(None)
        self.assertGreater(len(items), 5)

    def test_dtvnl(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "dtvnl")
        self.assertIsNotNone(chn)
        self.assertEqual("dtvnl", chn.channelCode)

    def test_dtvnl_list(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "dtvnl")
        items = chn.process_folder_list(None)
        self.assertGreater(len(items), 5)

    def test_venlonl(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "venlonl")
        self.assertIsNotNone(chn)
        self.assertEqual("venlonl", chn.channelCode)

    def test_venlonl_list(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "venlonl")
        items = chn.process_folder_list(None)
        self.assertGreater(len(items), 5)

    def test_horstnl(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "horstnl")
        self.assertIsNotNone(chn)
        self.assertEqual("horstnl", chn.channelCode)

    def test_horstnl_list(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        chn = ChannelIndex.get_register().get_channel(self._channel, "horstnl")
        items = chn.process_folder_list(None)
        self.assertGreater(len(items), 3)
