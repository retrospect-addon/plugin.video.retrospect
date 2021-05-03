# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import os

from resources.lib.envcontroller import EnvController
from resources.lib.logger import Logger
from resources.lib.textures import TextureHandler
from resources.lib.retroconfig import Config
from resources.lib.urihandler import UriHandler


class AutoChannelTest(unittest.TestCase):
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
        self.channels = ChannelIndex.get_register().get_channels()

    def test_main_lists(self):
        from resources.lib.chn_class import Channel
        failed = []
        failed_subs = []

        for channel_info in self.__get_channels_to_test():
            channel = channel_info.get_channel()  # type: Channel
            try:
                items = channel.process_folder_list()
            except:
                items = []

            if len(items) < 3:
                failed.append(channel_info)
                continue

            item = items[-1]
            try:
                sub_items = channel.process_folder_list(item)
            except:
                sub_items = []

            if len(sub_items) == 0:
                failed_subs.append(channel_info)

        self.assertEqual(
            len(failed + failed_subs), 0,
            msg="Mainlist failed for for:\n - {}\nSublisting failed for for:\n - {}".format(
                "\n - ".join([str(f) for f in failed]),
                "\n - ".join([str(f) for f in failed_subs])))

    def __get_channels_to_test(self):
        from resources.lib.channelinfo import ChannelInfo
        channels_tested = os.listdir(os.path.join("tests", "channel_tests"))
        channels_tested = [chn[5:-3] for chn in channels_tested if chn.startswith("test_")]
        channels_tested.append("chn_vtmbe")

        for channel_info in self.channels:  # type: ChannelInfo
            if channel_info.moduleName in channels_tested:
                continue

            if channel_info.uses_external_addon:
                continue

            yield channel_info
