# SPDX-License-Identifier: GPL-3.0-or-later
import unittest

from . channeltest import ChannelTest


class TestTweedeKamerChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestTweedeKamerChannel, self).__init__(methodName, "channel.videos.tweedekamer", "tweedekamer")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_create_main_index(self):
        _, items = self.channel.create_main_index(None)
        print(items)
        self.assertEqual(len(items), 3, "No items found in main index")

    def test_create_livestreams(self):
        # livestreams URL
        self._test_folder_url("https://cdn.debatdirect.tweedekamer.nl/api/app", 5)

    def test_create_debate_archive(self):
        # list of recent dates
        # minimum expected number is 0, because only dates with debates are listed
        self._test_folder_url("https://cdn.debatdirect.tweedekamer.nl/api/agenda", 0)

    def test_create_video_items(self):
        # list of debates on a specific date
        self._test_folder_url("https://cdn.debatdirect.tweedekamer.nl/api/agenda/2023-02-21", 15)

    def test_search_results(self):
        # list of debates on a specific date
        self._test_folder_url("https://cdn.debatdirect.tweedekamer.nl/search?q=voorbeeld&status[0]=geweest&sortering=relevant&vanaf=0", 5)

    def test_debate_video(self):
        # stream for a debate
        self._test_video_url("https://cdn.debatdirect.tweedekamer.nl/api/agenda/2023-02-21/debates/66560928-5437-4c6b-997f-de5401a6f2d5")
