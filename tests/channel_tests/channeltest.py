# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import unittest

from resources.lib.envcontroller import EnvController
from resources.lib.logger import Logger
from resources.lib.textures import TextureHandler
from resources.lib.retroconfig import Config
from resources.lib.urihandler import UriHandler


class ChannelTest(unittest.TestCase):
    # noinspection PyPep8Naming
    def __init__(self, methodName, channel, code):  # NOSONAR
        super(ChannelTest, self).__init__(methodName)
        self._channel = channel
        self._code = code
        self.channel = None

    @classmethod
    def setUpClass(cls):
        """ Setup the required elements for channels to run """

        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler(ignore_ssl_errors=False)
        TextureHandler.set_texture_handler(Config, Logger.instance(), UriHandler.instance())
        EnvController.cache_check()

    def setUp(self):
        """ Setup a new and clean channel """
        from resources.lib.helpers.channelimporter import ChannelIndex
        self.channel = ChannelIndex.get_register().get_channel(self._channel, self._code)

    @classmethod
    def tearDownClass(cls):
        Logger.instance().close_log()

    def _test_folder_url(self, url, expected_results=None, exact_results=False, headers=None):
        self.assertIsNotNone(self.channel)
        item = self._get_media_item(url)
        item.HttpHeaders.update(headers or {})

        items = self.channel.process_folder_list(item)
        if exact_results:
            self.assertEqual(len(items), expected_results)
        else:
            self.assertGreaterEqual(len(items), expected_results)
        return items

    def _test_video_url(self, url, headers=None):
        self.assertIsNotNone(self.channel)
        item = self._get_media_item(url)
        item.HttpHeaders.update(headers or {})
        item = self.channel.process_video_item(item)
        self.assertTrue(item.has_media_item_parts())

    def _get_media_item(self, url, name=None):
        from resources.lib.mediaitem import MediaItem
        item = MediaItem(name or "test_item", url)
        return item
