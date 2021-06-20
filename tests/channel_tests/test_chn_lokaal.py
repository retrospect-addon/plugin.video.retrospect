# SPDX-License-Identifier: GPL-3.0-or-later
import unittest

from .channeltest import ChannelTest


class TestLokaalChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestLokaalChannel, self).__init__(methodName, "channel.regionalnl.lokaal", "rtvoost")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)

    def test_live_streams(self):
        live_url = "http://mobileapp.rtvoost.nl/v520/feeds/tv.aspx"
        items = self._test_folder_url(live_url, 1)
        self.assertGreaterEqual(1, len([i for i in items if i.is_video]))

    def test_rtvdrenthe_mainlist(self):
        self._switch_channel("rtvdrenthe")

        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)

    def test_rtvnoord_mainlist(self):
        self._switch_channel("rtvnoord")

        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)

    def test_rtvrijnmond_mainlist(self):
        self._switch_channel("rtvrijnmond")

        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)

    def test_omroepwest_mainlist(self):
        self._switch_channel("omroepwest")

        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)

    def test_omroepgelderland_mainlist(self):
        self._switch_channel("omroepgelderland")

        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)

    def test_omroepbrabant_mainlist(self):
        self._switch_channel("omroepbrabant")

        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)

    def test_omropfryslan_mainlist(self):
        self._switch_channel("omropfryslan")

        items = self.channel.process_folder_list(None)
        self.assertGreater(len(items), 10)
