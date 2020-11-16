# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from resources.lib.urihandler import UriHandler
from resources.lib.logger import Logger
from resources.lib.updater import Updater
from resources.lib.version import Version


class TestUpdater(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestUpdater, cls).setUpClass()
        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler()

    @classmethod
    def tearDownClass(cls):
        Logger.instance().close_log()

    def test_github_with_newer_version_stable(self):
        current_version = Version("0.2.0")
        updater = Updater(
            "https://api.github.com/repos/retrospect-addon/plugin.video.retrospect/releases",
            current_version, UriHandler.instance(), Logger.instance(), True)
        new_available = updater.is_new_version_available()
        self.assertTrue(new_available)

    def test_github_with_no_new_version_stable(self):
        current_version = Version("8.0.0")
        updater = Updater(
            "https://api.github.com/repos/retrospect-addon/plugin.video.retrospect/releases",
            current_version, UriHandler.instance(), Logger.instance(), True)
        new_available = updater.is_new_version_available()
        self.assertFalse(new_available)

    def test_github_with_new_version_beta(self):
        current_version = Version("0.3.5~beta")
        # first do a call for a new version, and extract the current one
        updater = Updater(
            "https://api.github.com/repos/retrospect-addon/plugin.video.retrospect/releases",
            current_version, UriHandler.instance(), Logger.instance(), True)
        updater.is_new_version_available()

        online_version = updater.onlineVersion
        current_version = Version("{}~beta1".format(online_version))
        updater = Updater(
            "https://api.github.com/repos/retrospect-addon/plugin.video.retrospect/releases",
            current_version, UriHandler.instance(), Logger.instance(), True)
        new_available = updater.is_new_version_available()
        self.assertTrue(new_available)
