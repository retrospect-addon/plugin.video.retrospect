# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import io
import os
import shutil
import unittest

import xbmc
from resources.lib.retroconfig import Config
from resources.lib.logger import Logger
from resources.lib.textures.cached import Cached
from resources.lib.urihandler import UriHandler


class TestCachedTextures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.channel_path = os.path.abspath(os.path.join(".", "channels", "channel.nos.nos2010"))
        self.texture_dir = os.path.abspath(os.path.join(
            "tests", "home", "userdata", "addon_data", "plugin.video.retrospect", "textures"))
        if os.path.isdir(self.texture_dir):
            shutil.rmtree(self.texture_dir)

    def tearDown(self):
        if os.path.isdir(self.texture_dir):
            shutil.rmtree(self.texture_dir)

    def test_cached_texture_instance(self):
        texture = self._get_texture_handler()
        self.assertIsNotNone(texture)

    def test_cached_texture_output_dir(self):
        texture = self._get_texture_handler()
        texture._get_texture_uri(self.channel_path, "3large.png")
        expected_dir = os.path.join(
            "tests", "home", "userdata", "addon_data", "plugin.video.retrospect",
            "textures", "channel.nos.nos2010")
        self.assertTrue(os.path.isdir(expected_dir))

    def test_cached_texture_file_local(self):
        texture = self._get_texture_handler()
        texture_path = "3large.png"
        local_path = os.path.join(self.texture_dir, "channel.nos.nos2010", "3large.png")

        # Get url and check if it exists
        url = texture._get_texture_uri(self.channel_path, texture_path)
        self.assertTrue(url.startswith("special://"))

        # Fetch the textures
        bytes_transfered = texture.fetch_textures()
        self.assertEqual(bytes_transfered, 0)

        # Check if files were actually fetched.
        os_url = xbmc.translatePath(url)
        self.assertTrue(os.path.isabs(os_url))
        self.assertTrue(os.path.isfile(os_url))
        self.assertEqual(local_path, os_url)

    def test_cached_texture_file_online(self):
        texture = self._get_texture_handler()
        texture_path = "not-large.png"
        local_path = os.path.join(self.texture_dir, "channel.nos.nos2010", "not-large.png")

        # Get url and check if it exists
        url = texture._get_texture_uri(self.channel_path, texture_path)
        self.assertTrue(url.startswith("special://"))

        # Fetch the textures
        bytes_transfered = texture.fetch_textures()
        self.assertGreater(bytes_transfered, 0)

        # Check if files were actually fetched.
        os_url = xbmc.translatePath(url)
        self.assertTrue(os.path.isabs(os_url))
        self.assertTrue(os.path.isfile(os_url))
        self.assertEqual(local_path, os_url)

    def test_cached_texture_file_special(self):
        texture = self._get_texture_handler()
        texture_path = "{}/textures/{}".format(Config.profileUri, "3large.png")
        url = texture._get_texture_uri(self.channel_path, texture_path)
        self.assertEqual(texture_path, url)

    def test_cached_texture_file_http(self):
        texture = self._get_texture_handler()
        texture_path = "https://test/texture.png"
        url = texture._get_texture_uri(self.channel_path, texture_path)
        self.assertEqual(texture_path, url)

    def test_cached_texture_file_empty(self):
        texture = self._get_texture_handler()
        url = texture._get_texture_uri(self.channel_path, "")
        self.assertEqual("", url)

    def test_cached_purging(self):
        texture = self._get_texture_handler()
        # Get a valid texture
        valid_path = texture._get_texture_uri(self.channel_path, "1large.png")
        texture.fetch_textures()
        texture.fetch_textures()

        # create dummy texture
        local_dir = os.path.join(self.texture_dir, "channel.nos.nos2010")
        local_path_1 = os.path.join(local_dir, "3large.png")
        with io.open(local_path_1, mode='ab+') as fp:
            fp.write(b'niks')
        local_path_2 = os.path.join(local_dir, "10large.png")
        with io.open(local_path_2, mode='ab+') as fp:
            fp.write(b'niks')

        texture._purge_texture_cache(self.channel_path)
        self.assertFalse(os.path.isfile(local_path_1))
        self.assertFalse(os.path.isfile(local_path_2))
        self.assertTrue(os.path.isfile(xbmc.translatePath(valid_path)))

    def test_cached_is_texture_empty(self):
        texture = self._get_texture_handler()
        self.assertTrue(texture.is_texture_or_empty(""))

    def test_cached_is_texture_local(self):
        texture = self._get_texture_handler()
        self.assertTrue(texture.is_texture_or_empty("special://test"))

    def test_cached_is_texture_not_local(self):
        texture = self._get_texture_handler()
        self.assertFalse(texture.is_texture_or_empty("/home"))
        self.assertFalse(texture.is_texture_or_empty("c:\\test"))
        self.assertFalse(texture.is_texture_or_empty("https://"))
        self.assertFalse(texture.is_texture_or_empty("/home/test/"))

    def _get_texture_handler(self):
        return Cached(
            Config.textureUrl,
            Config.profileDir,
            Config.profileUri,
            Logger.instance(),
            UriHandler.instance())
