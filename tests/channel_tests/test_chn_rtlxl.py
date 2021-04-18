# SPDX-License-Identifier: GPL-3.0-or-later

from . channeltest import ChannelTest


class TestRtlXLChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestRtlXLChannel, self).__init__(methodName, "channel.rtlnl.rtl", None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 50)

    def test_main_program(self):
        url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/fun=getseasons/ak=399642"
        self._test_folder_url(url, 5)

    def test_sub_folder(self):
        url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/ak=399642/sk=507250/pg=1"
        self._test_folder_url(url, 5)

    def test_results_with_page(self):
        url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/ak=399642/sk=507250/pg=1"
        items = self._test_folder_url(url, 5)
        self.assertGreater(len([i for i in items if i.type == "page"]), 0)

    def test_video(self):
        url = "https://api.rtl.nl/watch/play/api/play/xl/7d6aa110-c039-47d6-bb36-73a2abeb90a5?device=web&drm=widevine&format=dash"
        self._test_video_url(url)
