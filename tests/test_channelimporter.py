# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import unittest

from resources.lib.logger import Logger


class TestChannelImporter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)

        # Set the Local TextureHandler as default
        from resources.lib.textures import TextureHandler
        from resources.lib.textures.local import Local
        TextureHandler._TextureHandler__TextureHandler = Local(Logger.instance())

    @classmethod
    def tearDownClass(cls):
        from resources.lib.addonsettings import AddonSettings
        AddonSettings.clear_cached_addon_settings_object()
        Logger.instance().close_log()

    def tearDown(self):
        # Remove the indexer
        from resources.lib.helpers.channelimporter import ChannelIndex
        ChannelIndex._ChannelIndex__channelIndexer = None

    def setUp(self):
        self.index_json = os.path.join(
            "tests", "home", "userdata", "addon_data", "plugin.video.retrospect",
            "channelindex.json")
        if os.path.isfile(self.index_json):
            os.remove(self.index_json)

    def test_instance(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        instance = ChannelIndex.get_register()
        self.assertIsNotNone(instance)

    def test_channels(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        instance = ChannelIndex.get_register()
        channels = instance.get_channels()
        self.assertGreater(len(channels), 50)

    def test_channel(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        instance = ChannelIndex.get_register()

        # Fetch a simple channel
        channel = instance.get_channel("channel.se.svt", "svt")
        self.assertIsNotNone(channel)
        channel = instance.get_channel("channel.se.svt", "svt2")
        self.assertIsNone(channel)

    def test_ignored_channel(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        instance = ChannelIndex.get_register()

        # Fetch a simple channel
        channel = instance.get_channel("channel.nos.schooltv", "schooltv")
        self.assertIsNone(channel)

    def test_categories(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        instance = ChannelIndex.get_register()
        cats = instance.get_categories()
        self.assertGreaterEqual(len(cats), 7)
