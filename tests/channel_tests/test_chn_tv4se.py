# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import os
import unittest

from . channeltest import ChannelTest


class TestTv4Channel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestTv4Channel, self).__init__(methodName, "channel.se.tv4se", "tv4segroup")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreaterEqual(len(items), 5, "Incorrect number of items in mainlist")

    def test_program_list(self):
        url = "https://client-gateway.tv4.a2d.tv/graphql?operationName=MediaIndex&variables=%7B%22input%22%3A%20%7B%22letterFilters%22%3A%20%5B%22A%22%2C%20%22B%22%2C%20%22C%22%2C%20%22D%22%2C%20%22E%22%2C%20%22F%22%2C%20%22G%22%2C%20%22H%22%2C%20%22I%22%2C%20%22J%22%2C%20%22K%22%2C%20%22L%22%2C%20%22M%22%2C%20%22N%22%2C%20%22O%22%2C%20%22P%22%2C%20%22Q%22%2C%20%22R%22%2C%20%22S%22%2C%20%22T%22%2C%20%22U%22%2C%20%22V%22%2C%20%22W%22%2C%20%22X%22%2C%20%22Y%22%2C%20%22Z%22%5D%2C%20%22limit%22%3A%20500%2C%20%22offset%22%3A%200%7D%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%22423ba183684c9ea464c94e200696c8f6ec190fe9837f542a672623fa87ef0f4e%22%7D%7D"
        self._test_folder_url(url, expected_results=1000)

    def test_lastest_news(self):
        url = "https://client-gateway.tv4.a2d.tv/graphql?operationName=Panel&variables=%7B%22panelId%22%3A%20%225Rqb0w0SN16A6YHt5Mx8BU%22%2C%20%22limit%22%3A%20500%2C%20%22offset%22%3A%200%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%223ef650feea500555e560903fee7fc06f8276d046ea880c5540282a5341b65985%22%7D%7D"
        self._test_folder_url(url, expected_results=10)

    def test_recent(self):
        url = "https://client-gateway.tv4.a2d.tv/graphql?operationName=Panel&variables=%7B%22panelId%22%3A%20%221pDPvWRfhEg0wa5SvlP28N%22%2C%20%22limit%22%3A%20500%2C%20%22offset%22%3A%200%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%223ef650feea500555e560903fee7fc06f8276d046ea880c5540282a5341b65985%22%7D%7D"
        self._test_folder_url(url, expected_results=10)

    def test_popular(self):
        url = "https://client-gateway.tv4.a2d.tv/graphql?operationName=Panel&variables=%7B%22panelId%22%3A%20%223QnNaigt4Szgkyz8yMU9oF%22%2C%20%22limit%22%3A%20500%2C%20%22offset%22%3A%200%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%223ef650feea500555e560903fee7fc06f8276d046ea880c5540282a5341b65985%22%7D%7D"
        self._test_folder_url(url, expected_results=10)

    def test_categories(self):
        url = "https://client-gateway.tv4.a2d.tv/graphql?operationName=PageList&variables=%7B%22pageListId%22%3A%20%22categories%22%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%2258da321b8e31df2b746f1d1f374151a450a4c24bda6415182fe81551c90e7d25%22%7D%7D"
        self._test_folder_url(url, expected_results=10)

    def test_season_content_listing(self):
        url = "https://client-gateway.tv4.a2d.tv/graphql?operationName=SeasonEpisodes&variables=%7B%22seasonId%22%3A%20%224952da9781c046017460%22%2C%20%22input%22%3A%20%7B%22limit%22%3A%20100%2C%20%22offset%22%3A%200%7D%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%229f069a1ce297d68a0b4a3d108142919fb6d12827f35fc71b03976a251e239796%22%7D%7D"
        self._test_folder_url(url, expected_results=5)

    @unittest.skip(reason="Requires Login")
    def test_list_category_content(self):
        url = "https://client-gateway.tv4.a2d.tv/graphql?operationName=Page&variables=%7B%22pageId%22%3A%20%22dokument%C3%A4rer%22%2C%20%22input%22%3A%20%7B%22limit%22%3A%20100%2C%20%22offset%22%3A%200%7D%7D&extensions=%7B%22persistedQuery%22%3A%20%7B%22version%22%3A%201%2C%20%22sha256Hash%22%3A%20%22a30fb04a7dbabeaf3b08f66134c6ac1f1e4980de1f21024fa755d752608e6ad9%22%7D%7D"
        self._test_folder_url(url, expected_results=5)

    @unittest.skip(reason="Requires Login")
    def test_video_playback(self):
        url = "https://playback2.a2d.tv/play/5deba52e58a8ebba316d?service=tv4play&device=browser&browser=GoogleChrome&protocol=hls%2Cdash&drm=widevine&capabilities=live-drm-adstitch-2%2Cexpired_assets"
        self._test_video_url(url)