# SPDX-License-Identifier: GPL-3.0-or-later
import time
import unittest
import xbmc

from resources.lib import mediatype
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
        self._switch_channel(self._code)

    @classmethod
    def tearDownClass(cls):
        from resources.lib.addonsettings import AddonSettings
        AddonSettings.clear_cached_addon_settings_object()
        Logger.instance().close_log()

    def _switch_channel(self, channel_code):
        self._code = channel_code
        from resources.lib.helpers.channelimporter import ChannelIndex
        self.channel = ChannelIndex.get_register().get_channel(self._channel, self._code)

    def _test_folder_url(self, url, expected_results=None, exact_results=False, headers=None, retry=1):
        self.assertIsNotNone(self.channel)

        while retry >= 0:
            try:
                item = self._get_media_item(url)
                item.HttpHeaders.update(headers or {})

                items = self.channel.process_folder_list(item)
                if exact_results:
                    self.assertEqual(len(items), expected_results)
                else:
                    self.assertGreaterEqual(len(items), expected_results)
                return items
            except:
                if retry > 0:
                    Logger.error("Error on unittest attempt. Remaining: %d tries/try.", retry,
                                 exc_info=True)
                    retry -= 1
                    time.sleep(5)
                    continue
                else:
                    raise

    def _test_video_url(self, url, headers=None, retry=1):
        self.assertIsNotNone(self.channel)

        while retry >= 0:
            try:
                item = self._get_media_item(url)
                item.HttpHeaders.update(headers or {})
                item = self.channel.process_video_item(item)

                self.assertTrue(item.has_streams())
                self.assertTrue(item.complete)
                return item
            except:
                if retry > 0:
                    Logger.error("Error on unittest attempt. Remaining: %d tries/try.", retry,
                                 exc_info=True)
                    retry -= 1
                    time.sleep(5)
                    continue
                else:
                    raise

    def _get_media_item(self, url, name=None):
        from resources.lib.mediaitem import MediaItem

        item = MediaItem(name or "test_item", url, media_type=mediatype.FOLDER)
        return item

    def _set_keyboard_input(self, *words):
        kb = xbmc.Keyboard()
        kb.get_keyboard_stub().reset()

        for word in words:
            kb.get_keyboard_stub().add_input(word)
