# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from resources.lib.logger import Logger
from resources.lib.textures.local import Local


class TestLocalTextures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.channel_path = os.path.abspath(os.path.join(".", "channels", "channel.nos", "nos2010"))

    def tearDown(self):
        pass

    def test_local_texture_instance(self):
        local = Local(Logger.instance())
        self.assertIsNotNone(local)

    def test_local_texture_file(self):
        local = Local(Logger.instance())
        url = local._get_texture_uri(self.channel_path, "3large.png")
        self.assertTrue(os.path.isabs(url))
        self.assertTrue(os.path.isfile(url))

    def test_local_texture_file_abs(self):
        local = Local(Logger.instance())
        path = os.path.abspath(os.path.join(self.channel_path, "3large.png"))
        url = local._get_texture_uri(self.channel_path, path)
        self.assertTrue(os.path.isabs(url))
        self.assertTrue(os.path.isfile(url))
        self.assertEqual(path, url)

    def test_local_texture_file_empty(self):
        local = Local(Logger.instance())
        url = local._get_texture_uri(self.channel_path, "")
        self.assertEqual("", url)

    def test_local_texture_file_http(self):
        local = Local(Logger.instance())
        url = local._get_texture_uri(self.channel_path, "http://test/img.jpg")
        self.assertEqual("http://test/img.jpg", url)
        url = local._get_texture_uri(self.channel_path, "https://test/img.jpg")
        self.assertEqual("https://test/img.jpg", url)

    def test_local_purging(self):
        local = Local(Logger.instance())
        local._purge_texture_cache(self.channel_path)

    def test_local_is_texture_empty(self):
        local = Local(Logger.instance())
        self.assertTrue(local.is_texture_or_empty(""))

    def test_local_is_texture_local(self):
        local = Local(Logger.instance())
        self.assertTrue(local.is_texture_or_empty("/home"))
        self.assertTrue(local.is_texture_or_empty("c:\\test"))

    def test_local_is_texture_not_local(self):
        local = Local(Logger.instance())
        self.assertFalse(local.is_texture_or_empty("https://"))
        self.assertFalse(local.is_texture_or_empty("http://"))
