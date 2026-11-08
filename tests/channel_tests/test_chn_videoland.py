# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest
from unittest import mock

from resources.lib.helpers.datehelper import DateHelper
from .channeltest import ChannelTest


class TestVideolandNLChannel(ChannelTest):
    class JsonWrapper:
        def __init__(self, data):
            self.json = data

    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestVideolandNLChannel, self).__init__(methodName, "channel.videoland.videolandnl",
                                                     None)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_episode_number_added_for_season(self):
        data = self.JsonWrapper({"featureId": "videos_by_season_by_program"})
        items = [
            self.create_media_item("Some episode name"),
            self.create_media_item("Another episode name"),
            self.create_media_item("Yet another episode name"),
        ]

        changed = self.channel.postprocess_episodes(data, items)
        self.assertCountEqual(changed, items)
        self.assertEqual(changed[0].name, "01 Some episode name")
        self.assertEqual(changed[1].name, "02 Another episode name")
        self.assertEqual(changed[2].name, "03 Yet another episode name")

    def test_episode_number_not_added_for_other_than_episode(self):
        data = self.JsonWrapper({"featureId": "videos_by_season_by_program"})
        items = [
            self.create_media_item("Some episode name", "no_episode"),
            self.create_media_item("Another episode name", "no_episode"),
            self.create_media_item("Yet another episode name", "no_episode"),
        ]

        changed = self.channel.postprocess_episodes(data, items)
        self.assertCountEqual(changed, items)
        self.assertEqual(changed[0].name, "Some episode name")
        self.assertEqual(changed[1].name, "Another episode name")
        self.assertEqual(changed[2].name, "Yet another episode name")

    def test_episode_number_not_added_for_other_list(self):
        data = self.JsonWrapper({"featureId": "other"})
        items = [
            self.create_media_item("Some episode name"),
            self.create_media_item("Another episode name"),
            self.create_media_item("Yet another episode name"),
        ]

        changed = self.channel.postprocess_episodes(data, items)
        self.assertCountEqual(changed, items)
        self.assertEqual(changed[0].name, "Some episode name")
        self.assertEqual(changed[1].name, "Another episode name")
        self.assertEqual(changed[2].name, "Yet another episode name")

    def test_episode_number_not_added_for_aflevering(self):
        data = self.JsonWrapper({"featureId": "videos_by_season_by_program"})
        # Episodes ordered backwards
        items = [
            self.create_media_item("Aflevering 3"),
            self.create_media_item("Aflevering 2"),
            self.create_media_item("Aflevering 1"),
        ]

        changed = self.channel.postprocess_episodes(data, items)
        self.assertCountEqual(changed, items)
        self.assertEqual(changed[0].name, "Aflevering 3")
        self.assertEqual(changed[1].name, "Aflevering 2")
        self.assertEqual(changed[2].name, "Aflevering 1")

    def test_episode_number_not_added_for_numbered_names(self):
        data = self.JsonWrapper({"featureId": "videos_by_season_by_program"})
        items = [
            self.create_media_item("1. Train"),
            self.create_media_item("2. Exile"),
            self.create_media_item("3. Devotion"),
        ]

        changed = self.channel.postprocess_episodes(data, items)
        self.assertCountEqual(changed, items)
        self.assertEqual(changed[0].name, "1. Train")
        self.assertEqual(changed[1].name, "2. Exile")
        self.assertEqual(changed[2].name, "3. Devotion")

    def test_episode_number_not_added_for_partially_numbered_names(self):
        data = self.JsonWrapper({"featureId": "videos_by_season_by_program"})
        items = [
            self.create_media_item("1. Train"),
            self.create_media_item("2. Exile"),
            self.create_media_item("Special"),
        ]

        changed = self.channel.postprocess_episodes(data, items)
        self.assertCountEqual(changed, items)
        self.assertEqual(changed[0].name, "1. Train")
        self.assertEqual(changed[1].name, "2. Exile")
        self.assertEqual(changed[2].name, "Special")

    def test_episode_date_filled_in_for_numbered_names(self):
        data = self.JsonWrapper({"featureId": "videos_by_season_by_program"})
        items = [
            self.create_media_item("Aflevering 1", date="2022-07-05"),
            self.create_media_item("Aflevering 2"),
        ]

        changed = self.channel.postprocess_episodes(data, items)
        self.assertCountEqual(changed, items)
        self.assertEqual(changed[0].name, "Aflevering 1")
        self.assertEqual(changed[1].name, "Aflevering 2 [date unknown]")
        self.assertEqual(changed[1].get_date(), "2022-07-05")

    def test_episode_names_not_cleaned_by_default(self):
        data = self.JsonWrapper({"featureId": "videos_by_season_by_program"})
        items = [
            self.create_media_item("2. Aflevering 2"),
            self.create_media_item("1. Aflevering 1"),
        ]

        changed = self.channel.postprocess_episodes(data, items)
        self.assertEqual(changed[0].name, "2. Aflevering 2")
        self.assertEqual(changed[1].name, "1. Aflevering 1")

    def test_episode_names_cleaned_when_enabled(self):
        data = self.JsonWrapper({"featureId": "videos_by_season_by_program"})
        items = [
            self.create_media_item("2. Aflevering 2"),
            self.create_media_item("1. Aflevering 1"),
            self.create_media_item("3. Aflevering 4"),
            self.create_media_item("4. Train"),
        ]

        with mock.patch.object(self.channel, "_get_setting",
                               side_effect=lambda setting_id, *args, **kwargs:
                               "true" if setting_id == "clean_episode_names" else None):
            changed = self.channel.postprocess_episodes(data, items)

        self.assertEqual(changed[0].name, "Aflevering 2")
        self.assertEqual(changed[1].name, "Aflevering 1")
        # Numbers that don't match and other names are left alone.
        self.assertEqual(changed[2].name, "3. Aflevering 4")
        self.assertEqual(changed[3].name, "4. Train")

    def test_episode_number_date_filled_in(self):
        data = self.JsonWrapper({"featureId": "videos_by_season_by_program"})
        items = [
            self.create_media_item("Some episode name", date="2022-07-05"),
            self.create_media_item("Another episode name", date="2022-07-06"),
            self.create_media_item("Yet another episode name")
        ]

        changed = self.channel.postprocess_episodes(data, items)
        self.assertCountEqual(changed, items)
        self.assertEqual(changed[0].name, "01 Some episode name")
        self.assertEqual(changed[1].name, "02 Another episode name")
        self.assertEqual(changed[2].name, "03 Yet another episode name [date unknown]")
        self.assertTrue(changed[0].has_date())
        self.assertTrue(changed[1].has_date())
        self.assertTrue(changed[2].has_date())
        self.assertEqual(changed[0].get_date(), "2022-07-05")
        self.assertEqual(changed[1].get_date(), "2022-07-06")
        self.assertEqual(changed[2].get_date(), "2022-07-06")

    # @unittest.skipIf(not os.environ.get("VIDEOLAND_USERNAME"),
    #                  "Not testing login without credentials")
    # def test_folder_with_single(self):
    #     self.__log_on()
    #
    #     url = "https://layout.videoland.bedrock.tech/front/v1/rtlnl/m6group_web/main/token-web-4/program/1714/layout?nbPages=10"
    #     items = self._test_folder_url(url, 3)
    #
    #     # If this fails with: Devices List, then there are too many sessions!
    #     videos = [i for i in items if i.is_playable]
    #     self.assertGreaterEqual(len(videos), 1)

    def create_media_item(self, name, media_type="episode", date=""):
        item = self._get_media_item("", name)
        item.media_type = media_type
        if date:
            timestamp = DateHelper.get_datetime_from_string(date, "%Y-%m-%d")
            item.set_date(timestamp.year, timestamp.month, timestamp.day)
        return item

    def __log_on(self):
        username = os.environ.get("VIDEOLAND_USERNAME")
        password = os.environ.get("VIDEOLAND_PASSWORD")
        # Make sure we are logged off
        self.channel._Channel__jwt = None
        self.channel._Channel__authenticator._Authenticator__handler.log_off(username="")
        # Then log on.
        self.channel.loggedOn = self.channel.log_on(username, password)
