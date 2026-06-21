# SPDX-License-Identifier: GPL-3.0-or-later
from . channeltest import ChannelTest


class TestSchatKamerChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestSchatKamerChannel, self).__init__(methodName, "channel.nos.schatkamer", None)
        self.headers = {
            "rsc": "1"
        }

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 5, "No items found in main list")

    def test_serie_listing(self):
        url = "https://schatkamer.beeldengeluid.nl/serie/2101608030021822731/borreltijd"
        self._test_folder_url(url, 5)

    def test_video(self):
        url = "https://schatkamer.beeldengeluid.nl/programma/2101608050038191431/tussenspel-elektronische-muziek-door-tom-dissevelt"
        self._test_video_url(url, headers=self.headers)

    def test_search(self):
        url = "https://schatkamer.beeldengeluid.nl/zoeken?q=tussenspel&_rsc=1"
        self._test_folder_url(url, 5)
