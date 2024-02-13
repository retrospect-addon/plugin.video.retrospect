# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import os
import unittest

from . channeltest import ChannelTest


class TestNpoChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNpoChannel, self).__init__(methodName, "channel.nos.nos2010", "uzgjson")

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_main_list(self):
        items = self.channel.process_folder_list(None)
        self.assertEqual(8, len(items), "No items found in mainlist")

    def test_live_radio(self):
        self._test_folder_url("https://www.npoluister.nl/",
                              expected_results=4)

    def test_live_radio_video(self):
        url = "https://www.npo3fm.nl/"
        self._test_video_url(url, parser="liveRadio")

    def test_live_radio_audio(self):
        url = "https://www.nporadio2.nl/soulenjazz"
        self._test_video_url(url, parser="liveRadio")

    def test_live_tv(self):
        self._test_folder_url("https://npo.nl/start/api/domain/guide-channels", 4)

    def test_recent_week_list(self):
        from resources.lib.mediaitem import MediaItem
        item = MediaItem("recent", "https://npo.nl/start/api/domain/guide-channels")
        item.metaData["retrospect:parser"] = "recent"
        items = self.channel.process_folder_list(item)
        self.assertGreaterEqual(len(items), 7)

    @unittest.skipIf("CI" in os.environ, "Skipping in CI due to Geo-Restrictions")
    def test_single_video(self):
        url = "https://npo.nl/start/video/de-otter-een-legende-keert-terug"
        self._test_video_url(url)

    @unittest.skipUnless(6 < datetime.datetime.utcnow().hour < 23, "No now broadcasts after 00:00")
    def test_recent_sub_items(self):
        from resources.lib.mediaitem import MediaItem
        item = MediaItem("recent", "#recentday")
        now = datetime.datetime.now()
        item.metaData["date"] = f"{now.day:02}-{now.month:02}-{now.year}"
        item.metaData["channels"] = {
            "83dc1f25-a065-496c-9418-bd5c60dfb36d": "NPO"
        }
        items = self.channel.process_folder_list(item)
        self.assertGreater(len(items), 10)

    def test_series_without_season(self):
        items = self._test_folder_url("https://npo.nl/start/api/domain/programs-by-season?guid=d205ce60-d638-4cab-8dbf-d48ddd7c489e", 1)
        self.assertTrue(all([i.is_playable for i in items]))

    def test_series_with_seasons_via_slug(self):
        from resources.lib.mediaitem import MediaItem
        item = MediaItem("With seasons", "https://npo.nl/start/api/domain/series-seasons?slug=first-dates&type=timebound_series")
        item.metaData["guid"] = "b89e4e01-5966-4d26-ba7d-b5e1eae45362"
        items = self.channel.process_folder_list(item)
        self.assertGreater(len(items), 10)
        self.assertGreater(len([i for i in items if i.is_playable]), 2)

    def test_series_recent_episodes_via_guid(self):
        self._test_folder_url("https://npo.nl/start/api/domain/programs-by-series?seriesGuid=b89e4e01-5966-4d26-ba7d-b5e1eae45362&limit=20&sort=-firstBroadcastDate", 4)

    def test_series_with_single_season(self):
        self._test_folder_url("https://npo.nl/start/api/domain/series-seasons?slug=selma-s-oorlog&type=timeless_series", expected_results=1)

    def test_trending(self):
        self._test_folder_url("https://npo.nl/start/api/domain/recommendation-collection?key=trending-anonymous-v0", 10)

    def test_popular(self):
        self._test_folder_url("https://npo.nl/start/api/domain/recommendation-collection?key=popular-anonymous-v0&partyId=unknown", 10)

    def test_news(self):
        self._test_folder_url("https://npo.nl/start/api/domain/recommendation-collection?key=news-anonymous-v0&partyId=unknown", 10)

    def test_programs(self):
        self._test_folder_url("https://npo.nl/start/api/domain/page-layout?slug=programmas", 5)

    def test_page(self):
        self._test_folder_url("https://npo.nl/start/api/domain/page-collection?type=series&guid=cc065da7-e6d2-44d6-bbce-2d600954e0b0", 10)

    def test_update_stream_pow(self):
        url = "POW_05467583"
        self._test_video_url(url)
