# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import unittest

from resources.lib.logger import Logger


class TestChannelImporter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)

    def setUp(self):
        self.index_json = os.path.join(
            "tests", "home", "userdata", "addon_data", "plugin.video.retrospect",
            "channelindex.json")
        if os.path.isfile(self.index_json):
            os.remove(self.index_json)

    def tearDown(self):
        from resources.lib.addonsettings import AddonSettings
        AddonSettings.clear_cached_addon_settings_object()
        Logger.instance().close_log()

    def test_instance(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        instance = ChannelIndex.get_register()
        self.assertIsNotNone(instance)

    def test_channels(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        instance = ChannelIndex.get_register()
        channels = instance.get_channels()
        self.assertGreater(len(channels), 50)
        self.assertTrue(os.path.isfile(self.index_json))
