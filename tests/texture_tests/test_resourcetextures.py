# SPDX-License-Identifier: GPL-3.0-or-later

import os
import unittest

from resources.lib.retroconfig import Config
from resources.lib.logger import Logger
from resources.lib.textures.resourceaddon import Resources
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

    def test_resource_texture_instance(self):
        texture = self._get_texture_handler()
        self.assertIsNotNone(texture)

    def test_resource_texture_file_from_resource(self):
        texture = self._get_texture_handler()
        texture_path = "3large.png"
        resource_path = "resource://resource.images.retrospect/channel.nos.nos2010/3large.png"

        # Get url and check if it exists
        url = texture._get_texture_uri(self.channel_path, texture_path)
        self.assertEqual(resource_path, url)

    def test_resource_texture_file_resource(self):
        texture = self._get_texture_handler()
        texture_path = "resource://{}/{}".format(Config.textureResource, "3large.png")
        url = texture._get_texture_uri(self.channel_path, texture_path)
        self.assertEqual(texture_path, url)

    def test_resource_texture_file_http(self):
        texture = self._get_texture_handler()
        texture_path = "https://test/texture.png"
        url = texture._get_texture_uri(self.channel_path, texture_path)
        self.assertEqual(texture_path, url)

    def test_resource_texture_file_empty(self):
        texture = self._get_texture_handler()
        url = texture._get_texture_uri(self.channel_path, "")
        self.assertEqual("", url)

    def test_resource_is_texture_empty(self):
        texture = self._get_texture_handler()
        self.assertTrue(texture.is_texture_or_empty(""))

    def test_resource_is_texture_local(self):
        texture = self._get_texture_handler()
        self.assertTrue(texture.is_texture_or_empty("resource://test"))

    def test_resource_is_texture_not_local(self):
        texture = self._get_texture_handler()
        self.assertFalse(texture.is_texture_or_empty("/home"))
        self.assertFalse(texture.is_texture_or_empty("c:\\test"))
        self.assertFalse(texture.is_texture_or_empty("https://"))
        self.assertFalse(texture.is_texture_or_empty("/home/test/"))

    def _get_texture_handler(self):
        return Resources(
            Config.textureResource,
            Logger.instance())
