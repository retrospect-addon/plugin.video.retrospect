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
        url = "https://npo.nl/start/video/candy-boys"
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
        item = MediaItem("With seasons", "https://npo.nl/start/api/domain/programs-by-season?guid=6df6cea2-4137-4f42-a183-830072f6b0ea&type=timeless_series")
        item.metaData["guid"] = "b6b7fa82-d565-42a1-8a75-46dbab66bd74"
        items = self.channel.process_folder_list(item)
        self.assertGreaterEqual(len(items), 1)
        self.assertGreaterEqual(len([i for i in items if i.is_playable]), 1)

    def test_update_next_js(self):
        from resources.lib.mediaitem import MediaItem
        url = "https://npo.nl/start/serie/nos-journaal-20-00-uur/seizoen-61/nos-journaal_96627"
        item = MediaItem("Video via NextJS", url)
        item.metaData["program_guid"] = "7917478b-8750-498f-8ced-dc6548ef2612"

        item = self.channel.process_video_item(item)
        self.assertTrue(item.has_streams())
        self.assertTrue(item.complete)

    def test_series_recent_episodes_via_guid(self):
        self._test_folder_url("https://npo.nl/start/api/domain/programs-by-series?seriesGuid=af032e71-3047-4b22-aac9-c2ef9c8bb9a3&limit=20&sort=-firstBroadcastDate", 2)

    def test_series_with_single_season(self):
        self._test_folder_url("https://npo.nl/start/api/domain/series-seasons?slug=selma-s-oorlog&type=timeless_series", expected_results=1)

    def test_trending(self):
        item = self._get_media_item("https://npo.nl/start/api/domain/recommendation-collection?partyId=1&collectionId=trending-anonymous-v0&partyId=2640c596-09ac-4c41-841c-c7fc68b4a7e5", "test_trending")
        item.metaData["retrospect:parser"] = "collection-with-series"
        items = self.channel.process_folder_list(item)
        self.assertGreater(len(items), 10)

    def test_popular(self):
        build_version = self.channel.build_version
        url = f"https://npo.nl/start/_next/data/{build_version}/collectie/nieuw-en-populair.json?slug=nieuw-en-populair"
        self._test_folder_url(url, 20)

    def test_news(self):
        build_version = self.channel.build_version
        url = f"https://npo.nl/start/_next/data/{build_version}/collectie/nieuws-en-achtergronden.json?slug=nieuws-en-achtergronden"
        self._test_folder_url(url, 20)

    def test_search_serie(self):
        url = "https://npo.nl/start/api/domain/search-collection-items?searchType=series&partyId=1&searchQuery=journaal&subscriptionType=anonymous"
        self._test_folder_url(url, 5)

    def test_search_video(self):
        url = "https://npo.nl/start/api/domain/search-collection-items?searchType=broadcasts&partyId=1&searchQuery=journaal&subscriptionType=anonymous"
        self._test_folder_url(url, 5)

    def test_programs(self):
        self._test_folder_url("https://npo.nl/start/api/domain/page-layout?slug=programmas", 5)

    def test_more_genres(self):
        self._test_folder_url("https://npo.nl/start/api/domain/page-collection?type=dynamic_page&collectionId=2670b702-d621-44be-b411-7aae3c3820eb&partyId=1", 7)

    def test_page(self):
        self._test_folder_url("https://npo.nl/start/api/domain/page-collection?type=series&collectionId=db612122-75e0-4f6c-8a32-e9202ae9fce8&partyId=1", 10)

    def test_update_stream_pow(self):
        url = "KN_1693383"
        self._test_video_url(url)
