# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import unittest

from resources.lib.retroconfig import Config
from resources.lib.logger import Logger
from resources.lib.textures.remote import Remote
from resources.lib.urihandler import UriHandler


class TestResourceTextures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.channel_path = os.path.abspath(os.path.join(".", "channels", "channel.nos", "nos2010"))

    def tearDown(self):
        pass

    def test_remote_texture_instance(self):
        texture = self._get_texture_handler()
        self.assertIsNotNone(texture)

    def test_remote_texture_from_remote(self):
        texture = self._get_texture_handler()
        texture_path = "3large.png"
        online_path = "https://cdn.rieter.net/resource.images.retrospect/resources/channel.nos.nos2010/3large.png"

        # Get url and check if it exists
        url = texture._get_texture_uri(self.channel_path, texture_path)
        self.assertEqual(online_path, url)

    def test_remote_texture_from_http(self):
        texture = self._get_texture_handler()
        texture_path = "https://test/texture.png"
        url = texture._get_texture_uri(self.channel_path, texture_path)
        self.assertEqual(texture_path, url)

    def test_remote_texture_filename_empty(self):
        texture = self._get_texture_handler()
        url = texture._get_texture_uri(self.channel_path, "")
        self.assertEqual("", url)

    def test_remote_is_texture_for_empty_input(self):
        texture = self._get_texture_handler()
        self.assertTrue(texture.is_texture_or_empty(""))

    def test_remote_is_texture_for_texture(self):
        texture = self._get_texture_handler()
        self.assertTrue(texture.is_texture_or_empty("https://cdn.rieter.net/resource.images.retrospect/resources/channel.nos.nos2010/3large.png"))

    def test_remote_is_texture_other(self):
        texture = self._get_texture_handler()
        self.assertFalse(texture.is_texture_or_empty("/home"))
        self.assertFalse(texture.is_texture_or_empty("c:\\test"))
        self.assertFalse(texture.is_texture_or_empty("https://"))
        self.assertFalse(texture.is_texture_or_empty("/home/test/"))

    def _get_texture_handler(self):
        return Remote(
            Config.textureUrl,
            Logger.instance())
