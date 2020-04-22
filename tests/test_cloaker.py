# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import unittest
import os
from collections import namedtuple

from resources.lib.cloaker import Cloaker
from resources.lib.settings import localsettings
from resources.lib.logger import Logger

# Dummy Channel Info object
ChannelInfo = namedtuple("ChannelInfo", ["guid", "id"])


class TestCloaker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)

    def setUp(self):
        self.cloakSettings = "settings.json"
        self.channel = ChannelInfo(guid="channel.id", id="channel.id.code")
        self.logger = Logger.instance()

        if os.path.isfile(self.cloakSettings):
            os.remove(self.cloakSettings)

        self.store = localsettings.LocalSettings(".", logger=self.logger)
        self.cloaker = Cloaker(channel=self.channel, settings_store=self.store, logger=self.logger)

    def tearDown(self):
        # we need to actively delete the cloaker and store to prevent any issues with reuse
        del self.cloaker
        del self.store

        if os.path.isfile(self.cloakSettings):
            os.remove(self.cloakSettings)

    def test_setting_first_time_cloak(self):
        self.assertTrue(self.cloaker.cloak("test-url"))
        self.assertFalse(self.cloaker.cloak("test-url2"))

    def test_is_cloaked(self):
        test_url = "test_url"
        self.assertFalse(self.cloaker.is_cloaked(test_url))
        self.cloaker.cloak(test_url)
        self.assertTrue(self.cloaker.is_cloaked(test_url))

    def test_is_already_cloaked(self):
        test_url = "test_url"
        self.assertTrue(self.cloaker.cloak(test_url))
        self.assertFalse(self.cloaker.cloak(test_url))

    def test_uncloak(self):
        test_url = "test_url"
        self.assertTrue(self.cloaker.cloak(test_url))
        self.assertTrue(self.cloaker.is_cloaked(test_url))
        self.cloaker.un_cloak(test_url)
        self.cloaker.un_cloak("not in there")
        self.assertFalse(self.cloaker.is_cloaked(test_url))
