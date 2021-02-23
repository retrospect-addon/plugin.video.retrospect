import os
import unittest

from resources.lib.logger import Logger
from resources.lib.retroconfig import Config
from resources.lib.settings.localsettings import LocalSettings


class TestLocalSettings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)

    def setUp(self):
        local_settings_file = os.path.join(Config.profileDir, "settings.json")
        if os.path.isfile(local_settings_file):
            os.remove(local_settings_file)

    def test_creation_on_missing(self):
        store = LocalSettings(Config.profileDir, Logger.instance())
        store.set_setting("test", True)
        self.assertTrue(os.path.isfile(store.local_settings_file))

    def test_store_value(self):
        value_to_store = True
        setting_to_store = "test"
        store = LocalSettings(Config.profileDir, Logger.instance())
        store.set_setting(setting_to_store, value_to_store)
        del store

        store = LocalSettings(Config.profileDir, Logger.instance())
        result = store.get_setting(setting_to_store)
        self.assertEqual(value_to_store, result)
