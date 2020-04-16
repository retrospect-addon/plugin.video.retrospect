import unittest

from resources.lib.logger import Logger
from resources.lib.textures import TextureHandler
from resources.lib.retroconfig import Config
from resources.lib.urihandler import UriHandler


class TestCloaker(unittest.TestCase):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestCloaker, self).__init__(methodName)
        self.channel = None

    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler(ignore_ssl_errors=False)
        TextureHandler.set_texture_handler(Config, Logger.instance(), UriHandler.instance())

    def setUp(self):
        from resources.lib.helpers.channelimporter import ChannelIndex
        self.channel = ChannelIndex.get_register().get_channel("chn_nos2010", "uzgjson")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(len(items), 8, "No items found in mainlist")
