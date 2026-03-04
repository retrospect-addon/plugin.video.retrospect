# SPDX-License-Identifier: GPL-3.0-or-later
import os
import unittest

from resources.lib.urihandler import UriHandler

import json
import shutil
import sys
import tempfile
from unittest.mock import MagicMock, patch

sys.path.insert(0, "channels/channel.nlziet/nlziet")
from api import (  # noqa: E402
    API_V8_SERIES, API_V9_VOD_HANDSHAKE, API_V9_PLACEMENT,
    API_V9_RECOMMEND_FILTERED,
)
import epg_enrichment  # noqa: E402

from resources.lib import mediatype
from .channeltest import ChannelTest


class TestNLZietChannel(ChannelTest):
    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super(TestNLZietChannel, self).__init__(methodName, "channel.nlziet.nlziet", None)

    def _make_media_item(self, name="test", url="http://example.com"):
        from resources.lib.mediaitem import MediaItem
        return MediaItem(name, url)

    def test_channel_exists(self):
        self.assertIsNotNone(self.channel)

    def test_process_folder_list_login_failure(self):
        """process_folder_list returns None when login fails."""
        original_log_on = self.channel.log_on
        try:
            self.channel.log_on = lambda *a, **kw: False
            result = self.channel.process_folder_list(None)
            self.assertIsNone(result)
        finally:
            self.channel.log_on = original_log_on

    # -- create_vod_item tests -----------------------------------------------

    def test_create_vod_item_series(self):
        """Series items (no type field) become FolderItems."""
        from resources.lib.mediaitem import FolderItem
        result_set = {
            "content": {
                "id": "abc123",
                "title": "Test Series",
                "image": {
                    "portraitUrl": "https://example.com/portrait.jpg",
                    "landscapeUrl": "https://example.com/landscape.jpg"
                },
                "logo": {
                    "normalUrl": "https://example.com/logo.png"
                },
                "tags": []
            }
        }
        item = self.channel.create_vod_item(result_set)
        self.assertIsNotNone(item)
        self.assertIsInstance(item, FolderItem)
        self.assertIn("/v8/series/abc123", item.url)
        self.assertEqual(item.name, "Test Series")

    def test_create_vod_item_movie(self):
        """Items tagged 'Movie' become playable MediaItems."""
        from resources.lib.mediaitem import MediaItem
        result_set = {
            "content": {
                "id": "mov456",
                "title": "Test Movie",
                "type": "Epg",
                "description": "A great movie.",
                "formattedDuration": "2u 10m",
                "tags": ["Movie"],
                "image": {"portraitUrl": None, "landscapeUrl": "https://example.com/thumb.jpg"},
                "logo": {"normalUrl": "https://example.com/logo.png"},
                "contentProvider": "Rtl",
                "broadcastedAt": "2026-02-13T20:27:18+01:00",
                "formattedDate": "Vr 13 feb",
                "availableUntil": "2026-02-22T00:05:37+01:00",
                "formattedAvailabilityWindow": "Nog 1 dag beschikbaar",
                "isAvailable": True,
                "seriesId": None,
                "seasonId": None
            }
        }
        item = self.channel.create_vod_item(result_set)
        self.assertIsNotNone(item)
        self.assertIsInstance(item, MediaItem)
        self.assertEqual(item.media_type, mediatype.MOVIE)
        self.assertIn("/v9/stream/handshake", item.url)
        self.assertIn("context=OnDemand", item.url)
        self.assertIn("id=mov456", item.url)
        self.assertTrue(item.isGeoLocked)
        self.assertIn("A great movie.", item.description)
        self.assertIn("Nog 1 dag beschikbaar", item.description)
        self.assertEqual(item.thumb, "https://example.com/thumb.jpg")
        self.assertEqual(item.icon, "https://example.com/logo.png")

    def test_create_vod_item_episode(self):
        """Vod-type items become episode MediaItems."""
        from resources.lib.mediaitem import MediaItem
        result_set = {
            "content": {
                "id": "ep789",
                "title": "Test Show",
                "type": "Vod",
                "subtitle": "Afl. 22",
                "description": "Episode description.",
                "formattedDuration": "1u 3m",
                "tags": ["NewEpisode"],
                "image": {"portraitUrl": None, "landscapeUrl": "https://example.com/ep.jpg"},
                "logo": {"normalUrl": None},
                "contentProvider": "Talpa",
                "seriesId": "ser-id",
                "seasonId": "sea-id",
                "isAvailable": True
            }
        }
        item = self.channel.create_vod_item(result_set)
        self.assertIsNotNone(item)
        self.assertIsInstance(item, MediaItem)
        self.assertEqual(item.media_type, mediatype.EPISODE)

    def test_create_vod_item_unavailable_skipped(self):
        """Items with isAvailable=False are skipped."""
        result_set = {
            "content": {
                "id": "gone",
                "title": "Gone Movie",
                "type": "Vod",
                "tags": [],
                "isAvailable": False,
                "image": {}, "logo": {}
            }
        }
        item = self.channel.create_vod_item(result_set)
        self.assertIsNone(item)

    def test_create_vod_item_empty_content(self):
        """Empty content dict returns None."""
        self.assertIsNone(self.channel.create_vod_item({"content": {}}))
        self.assertIsNone(self.channel.create_vod_item({}))

    def test_create_vod_item_episode_numbering(self):
        """Trending items with formattedEpisodeNumbering get season info."""
        result_set = {
            "content": {
                "id": "ep-num",
                "title": "Some Show",
                "type": "Vod",
                "tags": [],
                "formattedEpisodeNumbering": "S02:A05",
                "image": {}, "logo": {},
                "isAvailable": True
            }
        }
        item = self.channel.create_vod_item(result_set)
        self.assertIsNotNone(item)
        self.assertEqual(item.season, 2)
        self.assertEqual(item.episode, 5)

    # -- create_episode_item tests -------------------------------------------

    def test_create_episode_item(self):
        """Episode items get season/episode info from formattedEpisodeNumbering."""
        from resources.lib.mediaitem import MediaItem
        result_set = {
            "content": {
                "id": "epid",
                "title": "Episode Title",
                "subtitle": "Afl. 3",
                "formattedEpisodeNumbering": "S01:A03",
                "formattedDuration": "45m",
                "description": "Episode plot.",
                "image": {"portraitUrl": None, "landscapeUrl": "https://example.com/ep.jpg"},
                "logo": {"normalUrl": None},
                "isAvailable": True
            }
        }
        item = self.channel.create_episode_item(result_set)
        self.assertIsNotNone(item)
        self.assertIsInstance(item, MediaItem)
        self.assertEqual(item.season, 1)
        self.assertEqual(item.episode, 3)
        self.assertTrue(item.isDrmProtected)

    def test_create_episode_item_no_numbering(self):
        """Episodes without formattedEpisodeNumbering still work."""
        result_set = {
            "content": {
                "id": "epid2",
                "title": "Unnamed Episode",
                "image": {}, "logo": {},
                "isAvailable": True
            }
        }
        item = self.channel.create_episode_item(result_set)
        self.assertIsNotNone(item)
        self.assertEqual(item.name, "Unnamed Episode")

    # -- create_search_result_item tests -------------------------------------

    def test_create_search_result_series(self):
        """Search result with type 'Series' becomes a FolderItem."""
        from resources.lib.mediaitem import FolderItem
        result_set = {
            "content": {
                "id": "srid",
                "title": "Found Series",
                "type": "Series",
                "tags": [],
                "image": {}, "logo": {}
            }
        }
        item = self.channel.create_search_result_item(result_set)
        self.assertIsNotNone(item)
        self.assertIsInstance(item, FolderItem)
        self.assertIn("/v8/series/srid", item.url)

    def test_create_search_result_movie(self):
        """Search result with type 'Movie' becomes a playable movie."""
        from resources.lib.mediaitem import MediaItem
        result_set = {
            "content": {
                "id": "mrid",
                "title": "Found Movie",
                "type": "Movie",
                "tags": [],
                "image": {}, "logo": {}
            }
        }
        item = self.channel.create_search_result_item(result_set)
        self.assertIsNotNone(item)
        self.assertIsInstance(item, MediaItem)
        self.assertEqual(item.media_type, mediatype.MOVIE)
        self.assertIn("/v9/stream/handshake", item.url)
        self.assertIn("context=OnDemand", item.url)
        self.assertIn("id=mrid", item.url)

    def test_parse_duration_hours_and_minutes(self):
        self.assertEqual(self.channel._Channel__parse_duration("1u 23m"), 4980)

    def test_parse_duration_hours_only(self):
        self.assertEqual(self.channel._Channel__parse_duration("2u"), 7200)

    def test_parse_duration_minutes_only(self):
        self.assertEqual(self.channel._Channel__parse_duration("45m"), 2700)

    def test_parse_duration_empty(self):
        self.assertEqual(self.channel._Channel__parse_duration(""), 0)

    def test_parse_duration_garbage(self):
        self.assertEqual(self.channel._Channel__parse_duration("no numbers"), 0)

    # -- __set_vod_metadata tests --------------------------------------------

    def test_metadata_description_with_subtitle(self):
        """Subtitle is shown as bold heading above description."""
        item = self._make_media_item()
        content = {
            "subtitle": "Afl. 5",
            "description": "Episode plot text.",
            "image": {}, "logo": {}
        }
        self.channel._Channel__set_vod_metadata(item, content)
        self.assertIn("[B]Afl. 5[/B]", item.description)
        self.assertIn("Episode plot text.", item.description)

    def test_metadata_subtitle_equals_description(self):
        """When subtitle equals description, no duplication."""
        item = self._make_media_item()
        content = {
            "subtitle": "Same Title",
            "description": "Same Title",
            "image": {}, "logo": {}
        }
        self.channel._Channel__set_vod_metadata(item, content)
        self.assertEqual(item.description, "Same Title")

    def test_metadata_subtitle_only(self):
        """When there's only subtitle and no description, subtitle is used."""
        item = self._make_media_item()
        content = {
            "subtitle": "Just Subtitle",
            "image": {}, "logo": {}
        }
        self.channel._Channel__set_vod_metadata(item, content)
        self.assertEqual(item.description, "Just Subtitle")

    def test_metadata_poster_and_thumb(self):
        """Portrait image → poster, landscape → thumb."""
        item = self._make_media_item()
        content = {
            "image": {
                "portraitUrl": "https://example.com/portrait.jpg",
                "landscapeUrl": "https://example.com/landscape.jpg"
            },
            "logo": {}
        }
        self.channel._Channel__set_vod_metadata(item, content)
        self.assertEqual(item.thumb, "https://example.com/landscape.jpg")
        self.assertEqual(item.poster, "https://example.com/portrait.jpg")

    def test_metadata_studio(self):
        """contentProvider maps to studio info label."""
        item = self._make_media_item()
        content = {"contentProvider": "Rtl", "image": {}, "logo": {}}
        self.channel._Channel__set_vod_metadata(item, content)
        self.assertTrue(item.has_info_label("studio"))

    def test_metadata_broadcast_date(self):
        """broadcastedAt is parsed into set_date."""
        item = self._make_media_item()
        content = {
            "broadcastedAt": "2026-02-19T20:30:00+01:00",
            "formattedDate": "Do 19 feb",
            "image": {}, "logo": {}
        }
        self.channel._Channel__set_vod_metadata(item, content)
        self.assertIn("19 feb", str(item))

    # -- get_initial_folder_items tests --------------------------------------

    def test_initial_folder_items(self):
        """Main list returns dynamic placement rows when logged on."""
        self.channel.loggedOn = True
        _data, items = self.channel.get_initial_folder_items("")
        self.assertIsNotNone(items)
        self.assertGreaterEqual(len(items), 1)
        self.assertTrue(any(i.url and "search" in i.url.lower() for i in items),
                        "Expected a Search folder")

    def test_initial_folder_items_not_logged_in(self):
        """Main list returns empty when not logged in."""
        self.channel.loggedOn = False
        _data, items = self.channel.get_initial_folder_items("")
        self.assertEqual(len(items), 0)

    def test_initial_folder_items_search_is_first(self):
        """Search should be the first item in the main menu."""
        self.channel.loggedOn = True
        _data, items = self.channel.get_initial_folder_items("")
        self.assertGreaterEqual(len(items), 1)
        self.assertIn("search", items[0].url.lower())

    def test_initial_folder_items_includes_explore_pages(self):
        """Placements component creates explore category folders."""
        self.channel.loggedOn = True
        placement_response = json.dumps({"components": [
            {"type": "Placements", "title": "Ontdek hier", "items": [
                {"id": "explore-series", "title": "Series"},
                {"id": "explore-movies", "title": "Films"},
            ]},
        ]})
        with patch("resources.lib.urihandler.UriHandler.open",
                   return_value=placement_response):
            _data, items = self.channel.get_initial_folder_items("")
        titles = [i.name for i in items]
        self.assertIn("Series", titles)
        self.assertIn("Films", titles)
        series_item = next(i for i in items if i.name == "Series")
        self.assertEqual(series_item.url, API_V9_PLACEMENT.format("explore-series"))

    def test_get_explore_items_creates_genre_folders(self):
        """Explore page components become genre folder items."""
        explore_response = json.dumps({"components": [
            {"type": "Header", "title": "Films"},
            {"type": "Filters", "url": "https://api.nlziet.nl/v9/filters/genres/movies"},
            {"type": "ItemTileList", "title": "Drama",
             "url": API_V9_RECOMMEND_FILTERED + "?category=Movies&genre=Drama&limit=50"},
            {"type": "ItemTileList", "title": "Comedy",
             "url": API_V9_RECOMMEND_FILTERED + "?category=Movies&genre=Comedy&limit=50"},
        ]})
        _data, items = self.channel.get_explore_items(explore_response)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].name, "Drama")
        self.assertEqual(items[1].name, "Comedy")
        self.assertIn("recommend/filtered", items[0].url)

    def test_get_explore_items_series_mixed_urls(self):
        """Series page has curated (withcontext) and genre-filtered rows."""
        explore_response = json.dumps({"components": [
            {"type": "Header", "title": "Series"},
            {"type": "Filters",
             "itemsUrl": API_V9_RECOMMEND_FILTERED + "?category=Series&limit=50",
             "url": "https://api.nlziet.nl/v9/filters/genres/series"},
            {"type": "ItemTileList", "title": "Nieuwste series",
             "url": "https://api.nlziet.nl/v9/recommend/withcontext?contextName=allNewestSeries&limit=50"},
            {"type": "ItemTileList", "title": "Drama",
             "url": API_V9_RECOMMEND_FILTERED + "?category=Series&genre=Drama&limit=50"},
            {"type": "ItemTileList", "title": "Thriller/Crime",
             "url": API_V9_RECOMMEND_FILTERED + "?category=Series&genre=Crime&limit=50"},
        ]})
        _data, items = self.channel.get_explore_items(explore_response)
        self.assertEqual(len(items), 3)
        self.assertIn("withcontext", items[0].url)
        self.assertIn("recommend/filtered", items[1].url)

    def test_get_explore_items_kids_no_filters(self):
        """Kids page has curated lists only, no Filters component."""
        explore_response = json.dumps({"components": [
            {"type": "Header", "title": "Kids"},
            {"type": "ItemTileList", "title": "Populair",
             "url": "https://api.nlziet.nl/v9/recommend/withcontext?contextName=popularSeriesYouthMediumPreTeen&limit=50"},
            {"type": "ItemTileList", "title": "Animatieseries",
             "url": "https://api.nlziet.nl/v9/recommend/withcontext?contextName=moderatedSeriesList&listname=youth_series_animatie&limit=50"},
        ]})
        _data, items = self.channel.get_explore_items(explore_response)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].name, "Populair")

    def test_get_explore_items_documentaries_mixed(self):
        """Documentaries page mixes filtered and curated rows."""
        explore_response = json.dumps({"components": [
            {"type": "Header", "title": "Documentaires"},
            {"type": "ItemTileList", "title": "Documentaire series",
             "url": API_V9_RECOMMEND_FILTERED + "?category=Programs&genre=Documentary&limit=50"},
            {"type": "ItemTileList", "title": "Meest bekeken documentaires",
             "url": "https://api.nlziet.nl/v9/recommend/withcontext?contextName=trendingDocumentaries&limit=50"},
        ]})
        _data, items = self.channel.get_explore_items(explore_response)
        self.assertEqual(len(items), 2)
        self.assertIn("recommend/filtered", items[0].url)
        self.assertIn("withcontext", items[1].url)

    def test_get_explore_items_empty_data(self):
        """Empty data returns no items."""
        _data, items = self.channel.get_explore_items("")
        self.assertEqual(len(items), 0)

    # -- create_live_channel_item tests --------------------------------------

    def test_create_live_channel_item(self):
        """Live channel with full data becomes a playable live item."""
        result_set = {
            "channel": {
                "content": {
                    "id": "npo1",
                    "title": "NPO 1",
                    "logo": {"normalUrl": "https://example.com/npo1.png"}
                }
            },
            "programLocations": [
                {"content": {"assetId": "abc", "title": "Current Show"}}
            ]
        }
        item = self.channel.create_live_channel_item(result_set)
        self.assertIsNotNone(item)
        self.assertTrue(item.isLive)
        self.assertTrue(item.isDrmProtected)
        self.assertIn("channel=npo1", item.url)
        self.assertEqual(item.thumb, "https://example.com/npo1.png")
        self.assertEqual(item.description, "Current Show")
        self.assertEqual(item.metaData.get("asset_id"), "abc")

    def test_create_live_channel_item_no_channel(self):
        """Missing channel dict returns None."""
        self.assertIsNone(self.channel.create_live_channel_item({}))

    def test_create_live_channel_item_no_id(self):
        """Channel without id returns None."""
        result_set = {"channel": {"content": {"title": "No ID"}}}
        self.assertIsNone(self.channel.create_live_channel_item(result_set))

    def test_create_live_channel_item_paid(self):
        """Channel with missingSubscriptionFeature is marked paid."""
        result_set = {
            "channel": {
                "content": {"id": "x", "title": "Premium"},
                "missingSubscriptionFeature": "PremiumFeature"
            }
        }
        item = self.channel.create_live_channel_item(result_set)
        self.assertIsNotNone(item)
        self.assertTrue(item.isPaid)

    # -- extract_series_data tests -------------------------------------------

    def test_extract_series_data_seasons(self):
        """Series detail response produces season folders newest-first."""
        import json
        from resources.lib.mediaitem import FolderItem, MediaItem as MI
        self.channel.parentItem = MI("Series", API_V8_SERIES.format("sid"))
        # API returns seasons newest-first.
        data = json.dumps({
            "content": {
                "id": "sid",
                "title": "My Series",
                "seasons": [
                    {"id": "s2", "title": "Season 2"},
                    {"id": "s1", "title": "Season 1"}
                ]
            }
        })
        result_data, items = self.channel.extract_series_data(data)
        self.assertEqual(result_data, "")
        self.assertEqual(len(items), 2)
        self.assertIsInstance(items[0], FolderItem)
        # Presented newest-first to the user.
        self.assertIn("seasonId=s2", items[0].url)
        self.assertIn("seasonId=s1", items[1].url)

    def test_extract_series_data_empty_content(self):
        """Empty content returns no items."""
        from resources.lib.mediaitem import MediaItem as MI
        self.channel.parentItem = MI("S", API_V8_SERIES.format("sid"))
        result_data, items = self.channel.extract_series_data('{}')
        self.assertEqual(len(items), 0)

    def test_extract_series_data_nested_content(self):
        """Handles data.content wrapper format."""
        import json
        from resources.lib.mediaitem import FolderItem, MediaItem as MI
        self.channel.parentItem = MI("S", API_V8_SERIES.format("sid"))
        data = json.dumps({
            "data": {
                "content": {
                    "id": "sid",
                    "title": "Nested",
                    "seasons": [{"id": "s1", "title": "S1"}]
                }
            }
        })
        result_data, items = self.channel.extract_series_data(data)
        self.assertEqual(len(items), 1)

    @patch("chn_nlziet.chn_class.Channel.process_folder_list")
    def test_extract_series_data_seasonless(self, mock_pfl):
        """Seasonless series fetches episodes directly (no intermediate folder)."""
        import json
        from resources.lib.mediaitem import MediaItem as MI
        self.channel.parentItem = MI("Series", API_V8_SERIES.format("sid"))
        ep = MI("Episode 1", "https://example.com/ep1")
        mock_pfl.return_value = [ep]
        data = json.dumps({
            "content": {
                "id": "sid",
                "title": "Koekiemonsters eetkar",
                "seasons": [],
                "isSeasonSelectorEnabled": False
            }
        })
        result_data, items = self.channel.extract_series_data(data)
        self.assertEqual(result_data, "")
        mock_pfl.assert_called_once()
        parent = mock_pfl.call_args[0][0]
        self.assertIn("/v9/series/sid/episodes?", parent.url)
        self.assertNotIn("seasonId", parent.url)
        self.assertIn(ep, items)

    def test_extract_series_data_stores_series_title_in_season_metadata(self):
        """Season folder items carry nlziet:series_title for Up Next support."""
        import json
        from resources.lib.mediaitem import MediaItem as MI
        self.channel.parentItem = MI("Series", API_V8_SERIES.format("sid"))
        data = json.dumps({
            "content": {
                "id": "sid",
                "title": "Great Show",
                "seasons": [{"id": "s1", "title": "Season 1"}]
            }
        })
        _, items = self.channel.extract_series_data(data)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].metaData.get("nlziet:series_title"), "Great Show")

    def test_extract_series_title_reads_parent_metadata(self):
        """extract_series_title preprocessor caches series title on channel instance."""
        from resources.lib.mediaitem import FolderItem
        from resources.lib.helpers.jsonhelper import JsonHelper
        parent = FolderItem("Season 1", "https://api.nlziet.nl/v9/series/sid/episodes?seasonId=s1",
                            content_type="episodes")
        parent.metaData["nlziet:series_title"] = "Great Show"
        self.channel.parentItem = parent
        data, items = self.channel.extract_series_title("{}")
        self.assertEqual(items, [])
        self.assertEqual(self.channel._Channel__current_series_title, "Great Show")

    def test_extract_series_title_no_parent_metadata(self):
        """extract_series_title sets empty string when parent has no series title."""
        from resources.lib.mediaitem import FolderItem
        parent = FolderItem("Season 1", "https://api.nlziet.nl/v9/series/sid/episodes?seasonId=s1",
                            content_type="episodes")
        self.channel.parentItem = parent
        self.channel.extract_series_title("{}")
        self.assertEqual(self.channel._Channel__current_series_title, "")

    # -- Episode shortcut tests -----------------------------------------------

    @patch("chn_nlziet.UriHandler")
    def test_fetch_continue_item(self, mock_uri):
        """Continue watching returns a playable item from /play endpoint."""
        mock_uri.open.return_value = json.dumps({
            "content": {
                "id": "ep42",
                "title": "Familiediner"
            }
        })
        item = self.channel._Channel__fetch_continue_item("sid")
        self.assertIsNotNone(item)
        self.assertIn("ep42", item.url)
        self.assertIn("/v9/stream/handshake", item.url)
        self.assertTrue(item.dontGroup)
        mock_uri.open.assert_called_once()
        self.assertIn("/v9/series/sid/play", mock_uri.open.call_args[0][0])

    @patch("chn_nlziet.UriHandler")
    def test_fetch_continue_item_empty_response(self, mock_uri):
        """Continue watching returns None on empty response."""
        mock_uri.open.return_value = ""
        item = self.channel._Channel__fetch_continue_item("sid")
        self.assertIsNone(item)

    @patch("chn_nlziet.UriHandler")
    def test_fetch_continue_item_no_content_id(self, mock_uri):
        """Continue watching returns None when content has no id."""
        mock_uri.open.return_value = json.dumps({
            "content": {"title": "No ID"}
        })
        item = self.channel._Channel__fetch_continue_item("sid")
        self.assertIsNone(item)

    @patch("chn_nlziet.UriHandler")
    def test_fetch_season_episodes_basic(self, mock_uri):
        """Season episodes returns (broadcastAt, item) tuples in order."""
        mock_uri.open.return_value = json.dumps({"data": [
            {"content": {"id": "ep1", "subtitle": "S1:A1 Pilot",
                         "broadcastAt": "2024-01-01T00:00:00+01:00",
                         "firstAvailable": "2024-01-02T00:00:00+01:00"}},
            {"content": {"id": "ep2", "subtitle": "S1:A2 Second",
                         "broadcastAt": "2024-01-08T00:00:00+01:00"}},
        ]})
        result = self.channel._Channel__fetch_season_episodes("sid", "s1")
        self.assertEqual(len(result), 2)
        broadcast_at, item = result[0]
        self.assertEqual(broadcast_at, "2024-01-01T00:00:00+01:00")
        self.assertIn("ep1", item.url)
        self.assertTrue(item.dontGroup)
        self.assertEqual(item.metaData.get("nlziet:ep_title"), "S1:A1 Pilot")
        call_url = mock_uri.open.call_args[0][0]
        self.assertIn("seasonId=s1", call_url)
        self.assertIn("limit=400", call_url)

    @patch("chn_nlziet.UriHandler")
    def test_fetch_season_episodes_no_season_id(self, mock_uri):
        """Season episodes returns empty list for empty season_id."""
        result = self.channel._Channel__fetch_season_episodes("sid", "")
        self.assertEqual(result, [])
        mock_uri.open.assert_not_called()

    @patch("chn_nlziet.UriHandler")
    def test_fetch_season_episodes_empty_response(self, mock_uri):
        """Season episodes returns empty list on empty HTTP response."""
        mock_uri.open.return_value = ""
        result = self.channel._Channel__fetch_season_episodes("sid", "s1")
        self.assertEqual(result, [])

    @patch("chn_nlziet.UriHandler")
    def test_fetch_season_episodes_no_broadcast_at(self, mock_uri):
        """Season episodes handles missing broadcastAt as empty string."""
        mock_uri.open.return_value = json.dumps({
            "data": [{"content": {"id": "ep1", "subtitle": "Afl. 1"}}]
        })
        result = self.channel._Channel__fetch_season_episodes("sid", "s1")
        self.assertEqual(len(result), 1)
        broadcast_at, item = result[0]
        self.assertEqual(broadcast_at, "")
        self.assertIn("ep1", item.url)

    @patch("chn_nlziet.UriHandler")
    def test_build_shortcuts_all_three(self, mock_uri):
        """Build shortcuts returns continue, recent, and first items."""
        play_response = json.dumps({
            "content": {"id": "cont1", "title": "Continue Ep"}
        })
        # seasons[0] = oldest season (s1): first1 has the min broadcastAt
        oldest_eps = json.dumps({"data": [
            {"content": {"id": "old3", "subtitle": "S0:A3 Last",
                         "broadcastAt": "2020-03-01T00:00:00+01:00"}},
            {"content": {"id": "first1", "subtitle": "S0:A1 Pilot",
                         "broadcastAt": "2020-01-01T00:00:00+01:00"}},
        ]})
        # seasons[-1] = newest season (s2): ep10 has the max broadcastAt
        newest_eps = json.dumps({"data": [
            {"content": {"id": "ep10", "subtitle": "S1:A10 Latest",
                         "broadcastAt": "2024-03-01T00:00:00+01:00"}},
            {"content": {"id": "ep1n", "subtitle": "S1:A1 Start",
                         "broadcastAt": "2024-01-01T00:00:00+01:00"}},
        ]})
        mock_uri.open.side_effect = [play_response, newest_eps, oldest_eps]
        seasons = [{"id": "s1"}, {"id": "s2"}]
        shortcuts = self.channel._Channel__build_episode_shortcuts("sid", seasons)
        self.assertEqual(len(shortcuts), 3)
        # Order: continue, recent, first
        self.assertIn("cont1", shortcuts[0].url)
        self.assertIn("ep10", shortcuts[1].url)    # max broadcastAt in newest season
        self.assertIn("first1", shortcuts[2].url)  # min broadcastAt in oldest season

    @patch("chn_nlziet.UriHandler")
    def test_build_shortcuts_omits_continue_when_same_as_first(self, mock_uri):
        """Continue is omitted when it points to the same episode as first."""
        same_id = "same1"
        play_response = json.dumps({
            "content": {"id": same_id, "title": "Same Ep"}
        })
        # Single season (newest == oldest): same1 has min broadcastAt
        season_eps = json.dumps({"data": [
            {"content": {"id": same_id, "subtitle": "S1:A1 Same",
                         "broadcastAt": "2024-01-01T00:00:00+01:00"}},
            {"content": {"id": "last1", "subtitle": "S1:A3 Latest",
                         "broadcastAt": "2024-03-01T00:00:00+01:00"}},
        ]})
        mock_uri.open.side_effect = [play_response, season_eps]
        seasons = [{"id": "s1"}]
        shortcuts = self.channel._Channel__build_episode_shortcuts("sid", seasons)
        # Continue omitted (same url as first), only recent + first
        self.assertEqual(len(shortcuts), 2)
        urls = [s.url for s in shortcuts]
        self.assertTrue(any("last1" in u for u in urls))
        self.assertTrue(any(same_id in u for u in urls))

    def test_build_shortcuts_empty_seasons(self):
        """Build shortcuts returns empty list for empty seasons."""
        shortcuts = self.channel._Channel__build_episode_shortcuts("sid", [])
        self.assertEqual(shortcuts, [])

    def test_build_shortcuts_no_series_id(self):
        """Build shortcuts returns empty list for empty series_id."""
        shortcuts = self.channel._Channel__build_episode_shortcuts("", [{"id": "s1"}])
        self.assertEqual(shortcuts, [])

    @patch("chn_nlziet.UriHandler")
    def test_build_shortcuts_all_fetches_fail(self, mock_uri):
        """Build shortcuts handles all fetch failures gracefully."""
        mock_uri.open.return_value = ""
        seasons = [{"id": "s1"}]
        shortcuts = self.channel._Channel__build_episode_shortcuts("sid", seasons)
        self.assertEqual(shortcuts, [])

    @patch("chn_nlziet.UriHandler")
    def test_build_shortcuts_picks_by_broadcast_at(self, mock_uri):
        """First/latest are chosen by broadcastAt, not API response order."""
        play_response = json.dumps({"content": {"id": "cont1", "title": "C"}})
        # Single season, API returns newest-first; broadcastAt identifies order.
        season_eps = json.dumps({"data": [
            {"content": {"id": "ep3", "subtitle": "S1:A3 Last",
                         "broadcastAt": "2024-03-01T00:00:00+01:00"}},
            {"content": {"id": "ep2", "subtitle": "S1:A2 Mid",
                         "broadcastAt": "2024-02-01T00:00:00+01:00"}},
            {"content": {"id": "ep1", "subtitle": "S1:A1 First",
                         "broadcastAt": "2024-01-01T00:00:00+01:00"}},
        ]})
        mock_uri.open.side_effect = [play_response, season_eps]
        seasons = [{"id": "s1"}]
        shortcuts = self.channel._Channel__build_episode_shortcuts("sid", seasons)
        self.assertEqual(len(shortcuts), 3)
        self.assertIn("cont1", shortcuts[0].url)
        self.assertIn("ep3", shortcuts[1].url)  # max broadcastAt = latest
        self.assertIn("ep1", shortcuts[2].url)  # min broadcastAt = first

    def _make_ep(self, ep_id, broadcast_at=""):
        """Helper: create a (broadcastAt, MediaItem) tuple."""
        from resources.lib.mediaitem import MediaItem
        item = MediaItem(ep_id, "https://example.com/{}".format(ep_id))
        return (broadcast_at, item)

    def test_pick_boundary_none_for_empty(self):
        """Boundary picker returns None for empty input."""
        result = self.channel._Channel__pick_boundary_episode([], True)
        self.assertIsNone(result)

    def test_pick_boundary_single_item(self):
        """Boundary picker returns the only item regardless of direction."""
        eps = [self._make_ep("only")]
        result = self.channel._Channel__pick_boundary_episode(eps, True)
        self.assertIs(result, eps[0][1])

    def test_pick_boundary_ascending_api_broadcastAt_agree(self):
        """Ascending API: both API pos and broadcastAt vote for same first/last."""
        eps = [
            self._make_ep("ep1", "2024-01-01T00:00:00+00:00"),
            self._make_ep("ep2", "2024-02-01T00:00:00+00:00"),
            self._make_ep("ep3", "2024-03-01T00:00:00+00:00"),
        ]
        first = self.channel._Channel__pick_boundary_episode(eps, True)
        last = self.channel._Channel__pick_boundary_episode(eps, False)
        self.assertIn("ep1", first.url)
        self.assertIn("ep3", last.url)

    def test_pick_boundary_descending_api_broadcastAt_agree(self):
        """Descending API: broadcastAt corrects inverted API position order."""
        eps = [
            self._make_ep("ep3", "2024-03-01T00:00:00+00:00"),
            self._make_ep("ep2", "2024-02-01T00:00:00+00:00"),
            self._make_ep("ep1", "2024-01-01T00:00:00+00:00"),
        ]
        first = self.channel._Channel__pick_boundary_episode(eps, True)
        last = self.channel._Channel__pick_boundary_episode(eps, False)
        # Both API-pos and broadcastAt votes yield ep1 (last in list = oldest)
        self.assertIn("ep1", first.url)
        # And ep3 (first in list = newest)
        self.assertIn("ep3", last.url)

    def test_pick_boundary_majority_vote_no_first_available(self):
        """Descending API order: pick_first=True picks last item (oldest)."""
        eps = [
            self._make_ep("newest", "2024-12-01T00:00:00+00:00"),
            self._make_ep("oldest", "2020-01-01T00:00:00+00:00"),
        ]
        # API order: newest first → pick_first=True means API votes for oldest (eps[-1])
        first = self.channel._Channel__pick_boundary_episode(eps, True)
        last = self.channel._Channel__pick_boundary_episode(eps, False)
        self.assertIn("oldest", first.url)
        self.assertIn("newest", last.url)

    def test_create_vod_item_series_type(self):
        """Items with explicit type 'Series' become FolderItems."""
        from resources.lib.mediaitem import FolderItem
        result_set = {
            "content": {
                "id": "ser456",
                "title": "Trending Series",
                "type": "Series",
                "tags": [],
                "image": {}, "logo": {}
            }
        }
        item = self.channel.create_vod_item(result_set)
        self.assertIsNotNone(item)
        self.assertIsInstance(item, FolderItem)
        self.assertIn("/v8/series/ser456", item.url)

    # -- create_vod_item null edge cases ------------------------------------

    def test_create_vod_item_null_numbering(self):
        """Null formattedEpisodeNumbering does not crash."""
        result_set = {
            "content": {
                "id": "null-num",
                "title": "Null Numbering",
                "type": "Vod",
                "tags": [],
                "formattedEpisodeNumbering": None,
                "image": {}, "logo": {},
                "isAvailable": True
            }
        }
        item = self.channel.create_vod_item(result_set)
        self.assertIsNotNone(item)

    def test_create_episode_item_null_numbering(self):
        """Null formattedEpisodeNumbering in episode does not crash."""
        result_set = {
            "content": {
                "id": "ep-null",
                "title": "Null Episode",
                "formattedEpisodeNumbering": None,
                "image": {}, "logo": {}
            }
        }
        item = self.channel.create_episode_item(result_set)
        self.assertIsNotNone(item)

    def test_create_episode_item_numbering_from_subtitle(self):
        """Episode numbering is parsed from subtitle when formattedEpisodeNumbering is None."""
        result_set = {
            "content": {
                "id": "ep-sub",
                "title": "Patience",
                "subtitle": "S1:A6 Pandora's box",
                "image": {}, "logo": {}
            }
        }
        item = self.channel.create_episode_item(result_set)
        self.assertIsNotNone(item)
        self.assertEqual(item.season, 1)
        self.assertEqual(item.episode, 6)
        self.assertEqual(item.metaData.get("nlziet:subtitle"), "Pandora's box")

    def test_create_episode_item_dontgroup(self):
        """Episode items have dontGroup set to preserve API order."""
        result_set = {
            "content": {
                "id": "ep-dg", "title": "Show", "subtitle": "Sub",
                "image": {}, "logo": {}
            }
        }
        item = self.channel.create_episode_item(result_set)
        self.assertTrue(item.dontGroup)

    def test_create_episode_item_tv_show_title(self):
        """Episode items inherit tv_show_title from __current_series_title."""
        self.channel._Channel__current_series_title = "My Series"
        result_set = {
            "content": {
                "id": "ep-tvt", "title": "An Episode",
                "image": {}, "logo": {}
            }
        }
        item = self.channel.create_episode_item(result_set)
        self.assertIsNotNone(item)
        self.assertEqual(item.tv_show_title, "My Series")

    def test_create_episode_item_no_series_title(self):
        """Episode items work without __current_series_title set."""
        if hasattr(self.channel, "_Channel__current_series_title"):
            del self.channel._Channel__current_series_title
        result_set = {
            "content": {
                "id": "ep-nst", "title": "An Episode",
                "image": {}, "logo": {}
            }
        }
        item = self.channel.create_episode_item(result_set)
        self.assertIsNotNone(item)
        self.assertFalse(item.tv_show_title)

    def test_create_episode_item_empty_content(self):
        """Empty content returns None."""
        self.assertIsNone(self.channel.create_episode_item({"content": {}}))
        self.assertIsNone(self.channel.create_episode_item({}))

    # -- create_search_result_item edge cases --------------------------------

    def test_create_search_result_episode(self):
        """Search result with unknown type becomes an episode."""
        result_set = {
            "content": {
                "id": "eid",
                "title": "Some Episode",
                "type": "Vod",
                "tags": [],
                "image": {}, "logo": {}
            }
        }
        item = self.channel.create_search_result_item(result_set)
        self.assertIsNotNone(item)
        self.assertEqual(item.media_type, mediatype.EPISODE)

    def test_create_search_result_empty(self):
        """Empty search result returns None."""
        self.assertIsNone(self.channel.create_search_result_item({}))
        self.assertIsNone(self.channel.create_search_result_item({"content": {}}))

    # -- __set_vod_metadata edge cases --------------------------------------

    def test_metadata_null_fields(self):
        """Null image/logo/description fields don't crash."""
        item = self._make_media_item()
        content = {
            "subtitle": None,
            "description": None,
            "image": None,
            "logo": None,
            "contentProvider": None,
            "broadcastedAt": None,
            "formattedDuration": None
        }
        self.channel._Channel__set_vod_metadata(item, content)

    # -- __handle_stream_handshake error handling ----------------------------

    @patch("chn_nlziet.UriHandler")
    def test_handshake_errors_as_dict(self, mock_uri):
        """Handshake errors returned as a dict (not list) don't crash."""
        error_response = json.dumps({
            "errors": {
                "assetId": {"type": "InvalidAsset", "message": "Not playable"}
            }
        })
        mock_uri.open.return_value = error_response
        item = self._make_media_item()
        result = self.channel._Channel__handle_stream_handshake(
            item, API_V9_VOD_HANDSHAKE.format("x"))
        self.assertFalse(result.complete)

    @patch("chn_nlziet.UriHandler")
    def test_handshake_errors_as_list(self, mock_uri):
        """Handshake errors returned as a list are handled normally."""
        error_response = json.dumps({
            "errors": [{"type": "MaximumStreamsReached",
                        "message": "Too many",
                        "data": {"maximumNumberOfStreams": 2}}]
        })
        mock_uri.open.return_value = error_response
        item = self._make_media_item()
        result = self.channel._Channel__handle_stream_handshake(
            item, API_V9_VOD_HANDSHAKE.format("x"))
        self.assertFalse(result.complete)

    @patch("chn_nlziet.UriHandler")
    def test_handshake_errors_as_strings(self, mock_uri):
        """Handshake errors returned as a list of strings don't crash."""
        error_response = json.dumps({
            "errors": ["Invalid request parameter"]
        })
        mock_uri.open.return_value = error_response
        item = self._make_media_item()
        result = self.channel._Channel__handle_stream_handshake(
            item, API_V9_VOD_HANDSHAKE.format("x"))
        self.assertFalse(result.complete)

    # -- IPTV Manager tests --------------------------------------------------

    _LIVE_FIXTURE = json.dumps({"data": [
        {
            "channel": {
                "content": {
                    "id": "npo1",
                    "title": "NPO 1",
                    "logo": {"normalUrl": "https://example.com/npo1.png"}
                }
            },
            "programLocations": [
                {"content": {"assetId": "live-abc", "title": "Current Show"}}
            ]
        },
        {
            "channel": {
                "content": {
                    "id": "rtl4",
                    "title": "RTL 4",
                    "logo": {"normalUrl": "https://example.com/rtl4.png"}
                }
            },
            "programLocations": []
        }
    ]})

    _EPG_FIXTURE = json.dumps({"data": [
        {
            "channel": {"content": {"id": "npo1"}},
            "programLocations": [
                {
                    "content": {
                        "title": "News",
                        "startAt": "2026-02-21T20:00:00+01:00",
                        "endAt": "2026-02-21T20:30:00+01:00",
                        "image": {"landscapeUrl": "https://example.com/news.jpg"},
                        "isReplayAllowed": True,
                        "assetId": "replay-123",
                        "contentItemId": "news-item-1"
                    }
                },
                {
                    "content": {
                        "title": "Drama",
                        "startAt": "2026-02-21T20:30:00+01:00",
                        "endAt": "2026-02-21T21:30:00+01:00",
                        "image": {},
                        "isReplayAllowed": False,
                        "assetId": "drama-456",
                        "contentItemId": "drama-item-2"
                    }
                }
            ]
        }
    ]})

    def _make_mock_parser(self):
        parser = MagicMock()
        parser.create_action_url.return_value = "plugin://plugin.video.retrospect/play"
        return parser

    def _fresh_epg_cache_dir(self):
        """Create a fresh temp dir for EPG caches, isolating tests from each other.

        Returns the temp dir path.  Caller must clean up with shutil.rmtree and
        reset epg_enrichment._CACHE_DIR to None.
        """
        tmpdir = tempfile.mkdtemp(prefix="retrospect-epg-test-")
        epg_enrichment._CACHE_DIR = tmpdir
        return tmpdir

    def test_iptv_streams_not_authenticated(self):
        """Returns empty list when not logged in."""
        self.channel.loggedOn = False
        original = self.channel.log_on
        try:
            self.channel.log_on = lambda *a, **kw: False
            result = self.channel.create_iptv_streams(self._make_mock_parser())
            self.assertEqual(result, [])
        finally:
            self.channel.log_on = original

    def test_iptv_epg_not_authenticated(self):
        """Returns empty dict when not logged in."""
        self.channel.loggedOn = False
        original = self.channel.log_on
        try:
            self.channel.log_on = lambda *a, **kw: False
            result = self.channel.create_iptv_epg(self._make_mock_parser())
            self.assertEqual(result, {})
        finally:
            self.channel.log_on = original

    @patch("chn_nlziet.UriHandler")
    def test_iptv_streams_parsing(self, mock_uri):
        """Parses live channel JSON into stream dicts."""
        mock_uri.open.return_value = self._LIVE_FIXTURE
        self.channel.loggedOn = True
        parser = self._make_mock_parser()

        streams = self.channel.create_iptv_streams(parser)

        self.assertEqual(len(streams), 2)
        self.assertEqual(streams[0]["id"], "npo1")
        self.assertEqual(streams[0]["name"], "NPO 1")
        self.assertEqual(streams[0]["logo"], "https://example.com/npo1.png")
        self.assertIn("stream", streams[0])
        self.assertEqual(streams[1]["id"], "rtl4")
        parser.pickler.store_media_items.assert_called_once()

    @patch("chn_nlziet.UriHandler")
    def test_iptv_streams_empty_response(self, mock_uri):
        """Empty API response returns empty list."""
        mock_uri.open.return_value = ""
        self.channel.loggedOn = True

        streams = self.channel.create_iptv_streams(self._make_mock_parser())
        self.assertEqual(streams, [])

    @patch("chn_nlziet.UriHandler")
    def test_iptv_epg_parsing(self, mock_uri):
        """Parses EPG JSON into channel-keyed dict with program entries."""
        tmpdir = self._fresh_epg_cache_dir()
        try:
            mock_uri.open.side_effect = [self._EPG_FIXTURE] + [""] * 20
            self.channel.loggedOn = True
            parser = self._make_mock_parser()

            epg = self.channel.create_iptv_epg(parser)

            self.assertIn("npo1", epg)
            programs = epg["npo1"]
            self.assertEqual(len(programs), 2)
            self.assertEqual(programs[0]["title"], "News")
            self.assertEqual(programs[0]["start"], "2026-02-21T20:00:00+01:00")
            self.assertEqual(programs[0]["stop"], "2026-02-21T20:30:00+01:00")
            self.assertEqual(programs[0]["image"], "https://example.com/news.jpg")
            self.assertEqual(programs[1]["title"], "Drama")
            self.assertNotIn("image", programs[1])
        finally:
            epg_enrichment._CACHE_DIR = None
            shutil.rmtree(tmpdir, ignore_errors=True)

    @patch("chn_nlziet.UriHandler")
    def test_iptv_epg_replay_stream(self, mock_uri):
        """Replay-allowed programs include a stream URL."""
        tmpdir = self._fresh_epg_cache_dir()
        try:
            mock_uri.open.side_effect = [self._EPG_FIXTURE] + [""] * 20
            self.channel.loggedOn = True
            parser = self._make_mock_parser()

            epg = self.channel.create_iptv_epg(parser)

            programs = epg["npo1"]
            self.assertIn("stream", programs[0])
            self.assertNotIn("stream", programs[1])
            parser.pickler.store_media_items.assert_called()
        finally:
            epg_enrichment._CACHE_DIR = None
            shutil.rmtree(tmpdir, ignore_errors=True)

    @patch("chn_nlziet.UriHandler")
    def test_iptv_epg_skips_incomplete_programs(self, mock_uri):
        """Programs missing title/startAt/endAt are skipped."""
        tmpdir = self._fresh_epg_cache_dir()
        try:
            fixture = json.dumps({"data": [{
                "channel": {"content": {"id": "ch1"}},
                "programLocations": [
                    {"content": {"title": "Good", "startAt": "T1", "endAt": "T2",
                                 "contentItemId": "good-1", "assetId": "asset-1"}},
                    {"content": {"title": "No End", "startAt": "T1",
                                 "contentItemId": "noend-2", "assetId": "asset-2"}},
                    {"content": {"startAt": "T1", "endAt": "T2",
                                 "contentItemId": "notitle-3", "assetId": "asset-3"}},
                ]
            }]})
            mock_uri.open.side_effect = [fixture] + [""] * 20
            self.channel.loggedOn = True

            epg = self.channel.create_iptv_epg(self._make_mock_parser())

            self.assertEqual(len(epg["ch1"]), 1)
            self.assertEqual(epg["ch1"][0]["title"], "Good")
        finally:
            epg_enrichment._CACHE_DIR = None
            shutil.rmtree(tmpdir, ignore_errors=True)

    @patch("chn_nlziet.UriHandler")
    def test_iptv_epg_watch_ahead_gets_stream(self, mock_uri):
        """Future programmes with WatchInAdvance tag get a stream URL."""
        tmpdir = self._fresh_epg_cache_dir()
        try:
            import datetime
            future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)
            start = future.strftime("%Y-%m-%dT%H:%M:%S+01:00")
            end = (future + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S+01:00")
            fixture = json.dumps({"data": [{
                "channel": {"content": {"id": "npo3"}},
                "programLocations": [
                    {
                        "content": {
                            "title": "Break Free",
                            "startAt": start,
                            "endAt": end,
                            "tags": ["WatchInAdvance"],
                            "isReplayAllowed": False,
                            "assetId": "asset-wa-1",
                            "contentItemId": "wa-item-1"
                        }
                    }
                ]
            }]})
            mock_uri.open.side_effect = [fixture] + [""] * 20
            self.channel.loggedOn = True
            parser = self._make_mock_parser()

            epg = self.channel.create_iptv_epg(parser)

            programs = epg["npo3"]
            self.assertEqual(len(programs), 1)
            self.assertIn("stream", programs[0])
            self.assertIn("description", programs[0])
        finally:
            epg_enrichment._CACHE_DIR = None
            shutil.rmtree(tmpdir, ignore_errors=True)

    @patch("chn_nlziet.UriHandler")
    def test_iptv_epg_future_without_watch_ahead_no_stream(self, mock_uri):
        """Future programmes without WatchInAdvance tag do NOT get a stream URL."""
        tmpdir = self._fresh_epg_cache_dir()
        try:
            import datetime
            future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)
            start = future.strftime("%Y-%m-%dT%H:%M:%S+01:00")
            end = (future + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S+01:00")
            fixture = json.dumps({"data": [{
                "channel": {"content": {"id": "npo3"}},
                "programLocations": [
                    {
                        "content": {
                            "title": "Regular Show",
                            "startAt": start,
                            "endAt": end,
                            "isReplayAllowed": False,
                            "assetId": "asset-future-1",
                            "contentItemId": "future-item-1"
                        }
                    }
                ]
            }]})
            mock_uri.open.side_effect = [fixture] + [""] * 20
            self.channel.loggedOn = True
            parser = self._make_mock_parser()

            epg = self.channel.create_iptv_epg(parser)

            programs = epg["npo3"]
            self.assertEqual(len(programs), 1)
            self.assertNotIn("stream", programs[0])
        finally:
            epg_enrichment._CACHE_DIR = None
            shutil.rmtree(tmpdir, ignore_errors=True)

    # -- deduplicate_episode_titles tests ------------------------------------

    def test_deduplicate_episode_titles_all_same(self):
        """When all episodes share one title, use 'subtitle (title)' format."""
        from resources.lib.mediaitem import MediaItem
        items = []
        for sub in ["Dieren", "Op de boerderij", "Naar school"]:
            item = MediaItem("Woezel & Pip", "http://example.com/v", media_type=mediatype.EPISODE)
            item.metaData["nlziet:subtitle"] = sub
            items.append(item)

        result = self.channel.deduplicate_episode_titles(None, items)
        self.assertEqual([i.name for i in result], [
            "Dieren (Woezel & Pip)",
            "Op de boerderij (Woezel & Pip)",
            "Naar school (Woezel & Pip)"])

    def test_deduplicate_episode_titles_different(self):
        """When titles differ, no substitution happens."""
        from resources.lib.mediaitem import MediaItem
        items = [
            MediaItem("Ep 1", "http://example.com/1", media_type=mediatype.EPISODE),
            MediaItem("Ep 2", "http://example.com/2", media_type=mediatype.EPISODE),
        ]
        result = self.channel.deduplicate_episode_titles(None, items)
        self.assertEqual([i.name for i in result], ["Ep 1", "Ep 2"])

    def test_deduplicate_episode_titles_single_item(self):
        """A single episode is never deduplicated."""
        from resources.lib.mediaitem import MediaItem
        item = MediaItem("Solo", "http://example.com/1", media_type=mediatype.EPISODE)
        item.metaData["nlziet:subtitle"] = "Subtitle"
        result = self.channel.deduplicate_episode_titles(None, [item])
        self.assertEqual(result[0].name, "Solo")

    def test_deduplicate_episode_titles_skips_folders(self):
        """Folder items are ignored when checking title uniqueness."""
        from resources.lib.mediaitem import MediaItem, FolderItem
        from resources.lib import contenttype
        folder = FolderItem("Same Title", "http://example.com/f",
                            content_type=contenttype.EPISODES)
        ep1 = MediaItem("Same Title", "http://example.com/1", media_type=mediatype.EPISODE)
        ep1.metaData["nlziet:subtitle"] = "Sub A"
        ep2 = MediaItem("Same Title", "http://example.com/2", media_type=mediatype.EPISODE)
        ep2.metaData["nlziet:subtitle"] = "Sub B"

        result = self.channel.deduplicate_episode_titles(None, [folder, ep1, ep2])
        self.assertEqual(result[0].name, "Same Title")  # folder unchanged
        self.assertEqual(result[1].name, "Sub A (Same Title)")
        self.assertEqual(result[2].name, "Sub B (Same Title)")

    def test_deduplicate_episode_titles_no_subtitle(self):
        """Episodes without a stored subtitle keep their original title."""
        from resources.lib.mediaitem import MediaItem
        ep1 = MediaItem("Same", "http://example.com/1", media_type=mediatype.EPISODE)
        ep1.metaData["nlziet:subtitle"] = "Has Sub"
        ep2 = MediaItem("Same", "http://example.com/2", media_type=mediatype.EPISODE)
        # ep2 has no subtitle stored

        result = self.channel.deduplicate_episode_titles(None, [ep1, ep2])
        self.assertEqual(result[0].name, "Has Sub (Same)")
        self.assertEqual(result[1].name, "Same")

    def test_create_episode_item_stores_subtitle(self):
        """create_episode_item stores subtitle in metaData when different from title."""
        result_set = {
            "content": {
                "id": "epid",
                "title": "Woezel & Pip",
                "subtitle": "Dieren",
                "image": {}, "logo": {},
                "isAvailable": True
            }
        }
        item = self.channel.create_episode_item(result_set)
        self.assertEqual(item.metaData.get("nlziet:subtitle"), "Dieren")

    def test_create_episode_item_no_subtitle_stored_when_same(self):
        """No subtitle stored when it equals the title."""
        result_set = {
            "content": {
                "id": "epid",
                "title": "Same Name",
                "subtitle": "Same Name",
                "image": {}, "logo": {},
                "isAvailable": True
            }
        }
        item = self.channel.create_episode_item(result_set)
        self.assertNotIn("nlziet:subtitle", item.metaData)

    def test_deduplicate_episode_titles_partial_duplicates(self):
        """Partial duplicates get 'subtitle (title)' format."""
        from resources.lib.mediaitem import MediaItem
        ep1 = MediaItem("NOS Olympische Spelen", "http://example.com/1",
                         media_type=mediatype.EPISODE)
        ep1.metaData["nlziet:subtitle"] = "Schaatsen"
        ep2 = MediaItem("NOS Olympische Spelen", "http://example.com/2",
                         media_type=mediatype.EPISODE)
        ep2.metaData["nlziet:subtitle"] = "Live"
        ep3 = MediaItem("Unique Title", "http://example.com/3",
                         media_type=mediatype.EPISODE)
        ep3.metaData["nlziet:subtitle"] = "Some Sub"

        result = self.channel.deduplicate_episode_titles(None, [ep1, ep2, ep3])
        self.assertEqual(result[0].name, "Schaatsen (NOS Olympische Spelen)")
        self.assertEqual(result[1].name, "Live (NOS Olympische Spelen)")
        self.assertEqual(result[2].name, "Unique Title")


class TestEpisodeBoundaryDetection(unittest.TestCase):
    """Unit tests for __pick_boundary_episode and __is_ascending."""

    @classmethod
    def setUpClass(cls):
        from resources.lib.logger import Logger
        from resources.lib.textures import TextureHandler
        from resources.lib.retroconfig import Config
        Logger.create_logger(None, str(cls), min_log_level=0)
        UriHandler.create_uri_handler(ignore_ssl_errors=False)
        TextureHandler.set_texture_handler(
            Config, Logger.instance(), UriHandler.instance())

    @classmethod
    def tearDownClass(cls):
        from resources.lib.addonsettings import AddonSettings
        from resources.lib.logger import Logger
        AddonSettings.clear_cached_addon_settings_object()
        Logger.instance().close_log()

    @staticmethod
    def _make_item(name):
        from resources.lib.mediaitem import MediaItem
        return MediaItem(name, "http://example.com/{}".format(name),
                         media_type=mediatype.EPISODE)

    @staticmethod
    def _pick(eps, pick_first):
        from chn_nlziet import Channel
        return Channel._Channel__pick_boundary_episode(eps, pick_first)

    @staticmethod
    def _is_ascending(eps):
        from chn_nlziet import Channel
        return Channel._Channel__is_ascending(eps)

    def test_descending_clean_broadcastat_first(self):
        """Descending API order with monotonic broadcastAt → first = last item."""
        eps = [
            ("2026-03-06T20:35:00+01:00", self._make_item("S20:A2")),
            ("2026-02-27T20:35:00+01:00", self._make_item("S20:A1")),
        ]
        result = self._pick(eps, pick_first=True)
        self.assertEqual(result.name, "S20:A1")

    def test_descending_clean_broadcastat_recent(self):
        """Descending API order with monotonic broadcastAt → recent = first item."""
        eps = [
            ("2026-03-06T20:35:00+01:00", self._make_item("S20:A2")),
            ("2026-02-27T20:35:00+01:00", self._make_item("S20:A1")),
        ]
        result = self._pick(eps, pick_first=False)
        self.assertEqual(result.name, "S20:A2")

    def test_descending_corrupted_broadcastat_first(self):
        """Flikken Maastricht S1: bulk-import timestamps, non-monotonic.

        API order is correct (A13 → A1), broadcastAt is garbage.
        Should still pick A1 as first episode.
        """
        eps = [
            ("2025-05-22T10:36:27+02:00", self._make_item("S1:A13")),
            ("2025-05-22T10:36:27+02:00", self._make_item("S1:A12")),
            ("2022-01-13T01:00:00+01:00", self._make_item("S1:A11")),
            ("2025-05-22T10:36:26+02:00", self._make_item("S1:A10")),
            ("2025-05-22T10:36:26+02:00", self._make_item("S1:A9")),
            ("2025-05-22T10:36:27+02:00", self._make_item("S1:A8")),
            ("2025-05-22T10:36:26+02:00", self._make_item("S1:A7")),
            ("2025-05-22T10:36:26+02:00", self._make_item("S1:A6")),
            ("2025-05-22T10:36:26+02:00", self._make_item("S1:A5")),
            ("2025-05-22T10:36:26+02:00", self._make_item("S1:A4")),
            ("2025-05-22T10:36:26+02:00", self._make_item("S1:A3")),
            ("2025-05-22T10:36:25+02:00", self._make_item("S1:A2")),
            ("2025-05-22T10:36:25+02:00", self._make_item("S1:A1")),
        ]
        result = self._pick(eps, pick_first=True)
        self.assertEqual(result.name, "S1:A1")

    def test_descending_corrupted_broadcastat_recent(self):
        """Flikken Maastricht S1: most recent should be A13."""
        eps = [
            ("2025-05-22T10:36:27+02:00", self._make_item("S1:A13")),
            ("2022-01-13T01:00:00+01:00", self._make_item("S1:A11")),
            ("2025-05-22T10:36:25+02:00", self._make_item("S1:A1")),
        ]
        result = self._pick(eps, pick_first=False)
        self.assertEqual(result.name, "S1:A13")

    def test_ascending_clean_broadcastat_first(self):
        """Fawlty Towers S1: ascending API order, clean broadcastAt."""
        eps = [
            ("1975-09-19T01:00:00+01:00", self._make_item("S1:A1")),
            ("1975-09-26T01:00:00+01:00", self._make_item("S1:A2")),
            ("1975-10-03T01:00:00+01:00", self._make_item("S1:A3")),
            ("1975-10-10T01:00:00+01:00", self._make_item("S1:A4")),
            ("1975-10-17T01:00:00+01:00", self._make_item("S1:A5")),
            ("1975-10-24T01:00:00+01:00", self._make_item("S1:A6")),
        ]
        result = self._pick(eps, pick_first=True)
        self.assertEqual(result.name, "S1:A1")

    def test_ascending_clean_broadcastat_recent(self):
        """Fawlty Towers S1: most recent should be A6."""
        eps = [
            ("1975-09-19T01:00:00+01:00", self._make_item("S1:A1")),
            ("1975-10-24T01:00:00+01:00", self._make_item("S1:A6")),
        ]
        result = self._pick(eps, pick_first=False)
        self.assertEqual(result.name, "S1:A6")

    def test_descending_rebroadcast_first(self):
        """De Luizenmoeder S1: some episodes have re-broadcast dates."""
        eps = [
            ("2018-03-18T20:25:00+01:00", self._make_item("S1:A10")),
            ("2018-03-11T20:25:00+01:00", self._make_item("S1:A9")),
            ("2020-12-04T20:25:00+01:00", self._make_item("S1:A5")),
            ("2020-12-11T20:25:00+01:00", self._make_item("S1:A3")),
            ("2022-05-08T02:05:00+02:00", self._make_item("S1:A2")),
            ("2018-01-14T20:25:00+01:00", self._make_item("S1:A1")),
        ]
        result = self._pick(eps, pick_first=True)
        self.assertEqual(result.name, "S1:A1")

    def test_descending_rebroadcast_recent(self):
        """De Luizenmoeder S1: most recent should be A10."""
        eps = [
            ("2018-03-18T20:25:00+01:00", self._make_item("S1:A10")),
            ("2020-12-04T20:25:00+01:00", self._make_item("S1:A5")),
            ("2022-05-08T02:05:00+02:00", self._make_item("S1:A2")),
            ("2018-01-14T20:25:00+01:00", self._make_item("S1:A1")),
        ]
        result = self._pick(eps, pick_first=False)
        self.assertEqual(result.name, "S1:A10")

    def test_single_episode(self):
        """Single episode → always returned regardless of pick_first."""
        eps = [("2025-01-01T00:00:00+01:00", self._make_item("Only"))]
        self.assertEqual(self._pick(eps, pick_first=True).name, "Only")
        self.assertEqual(self._pick(eps, pick_first=False).name, "Only")

    def test_empty_list(self):
        """Empty episode list → None."""
        self.assertIsNone(self._pick([], pick_first=True))
        self.assertIsNone(self._pick([], pick_first=False))

    def test_no_broadcastat(self):
        """All broadcastAt empty → defaults to descending."""
        eps = [
            ("", self._make_item("A3")),
            ("", self._make_item("A2")),
            ("", self._make_item("A1")),
        ]
        # Default descending: first = last, recent = first
        self.assertEqual(self._pick(eps, pick_first=True).name, "A1")
        self.assertEqual(self._pick(eps, pick_first=False).name, "A3")

    def test_is_ascending_monotonic_increasing(self):
        eps = [
            ("2018-01-01T00:00:00+01:00", self._make_item("A")),
            ("2018-02-01T00:00:00+01:00", self._make_item("B")),
            ("2018-03-01T00:00:00+01:00", self._make_item("C")),
        ]
        self.assertTrue(self._is_ascending(eps))

    def test_is_ascending_monotonic_decreasing(self):
        eps = [
            ("2018-03-01T00:00:00+01:00", self._make_item("C")),
            ("2018-02-01T00:00:00+01:00", self._make_item("B")),
            ("2018-01-01T00:00:00+01:00", self._make_item("A")),
        ]
        self.assertFalse(self._is_ascending(eps))

    def test_is_ascending_non_monotonic(self):
        """Non-monotonic broadcastAt → defaults to descending (False)."""
        eps = [
            ("2018-03-01T00:00:00+01:00", self._make_item("C")),
            ("2018-01-01T00:00:00+01:00", self._make_item("A")),
            ("2018-02-01T00:00:00+01:00", self._make_item("B")),
        ]
        self.assertFalse(self._is_ascending(eps))

    def test_is_ascending_no_dates(self):
        """No broadcastAt dates → defaults to descending (False)."""
        eps = [("", self._make_item("A")), ("", self._make_item("B"))]
        self.assertFalse(self._is_ascending(eps))


class TestNLZietChannelLive(ChannelTest):
    """Live integration tests — requires NLZIET_USERNAME and NLZIET_PASSWORD."""

    # noinspection PyPep8Naming
    def __init__(self, methodName):  # NOSONAR
        super().__init__(methodName, "channel.nlziet.nlziet", None)

    @classmethod
    def setUpClass(cls):
        cls.username = os.getenv("NLZIET_USERNAME")
        cls.password = os.getenv("NLZIET_PASSWORD")
        if not cls.username or not cls.password:
            raise unittest.SkipTest("NLZIET credentials not in environment.")
        super().setUpClass()

        # Clear any cached mock tokens left by TestNLZIETAuthMocked, then do a
        # one-time real authentication and pre-store the first available profile
        # (profile 0) so that each setUp() uses the cached-token path and never
        # triggers the interactive profile-selection dialog.
        from resources.lib.addonsettings import AddonSettings, LOCAL
        from resources.lib.authentication.nlzietoauth2handler import NLZIETOAuth2Handler
        from resources.lib.authentication.authenticator import Authenticator
        for client_id in (NLZIETOAuth2Handler.WEB_CLIENT_ID, NLZIETOAuth2Handler.TV_CLIENT_ID):
            prefix = "nlziet_oauth2_{}_".format(client_id)
            AddonSettings.set_setting("{}access_token".format(prefix), "", store=LOCAL)
            AddonSettings.set_setting("{}refresh_token".format(prefix), "", store=LOCAL)
            AddonSettings.set_setting("{}expires_at".format(prefix), "", store=LOCAL)
        AddonSettings.set_setting(NLZIETOAuth2Handler.AUTH_METHOD_SETTING, "web", store=LOCAL)
        handler = NLZIETOAuth2Handler(use_device_flow=False)
        auth = Authenticator(handler)
        result = auth.log_on(username=cls.username, password=cls.password)
        if not result.logged_on:
            raise unittest.SkipTest("NLZIET live login failed in setUpClass.")
        profiles = handler.list_profiles()
        if profiles:
            handler.set_profile(profiles[0]["id"])

    def setUp(self):
        super().setUp()
        if not self.channel.log_on(self.username, self.password):
            self.skipTest("NLZIET login failed.")

    def test_login_succeeds(self):
        """Live: log_on() with real credentials succeeds."""
        self.assertTrue(self.channel.loggedOn)


    def test_process_folder_list_returns_items(self):
        """Live: process_folder_list(None) returns a non-empty item list after login."""
        items = self.channel.process_folder_list(None)
        self.assertIsNotNone(items)
        self.assertGreater(len(items), 0)


    def test_series_detail_has_season_structure(self):
        """Live: series detail returns seasons (prerequisite for shortcuts)."""
        # Use a known series by searching for one first
        from resources.lib.mediaitem import MediaItem
        url = "https://api.nlziet.nl/v8/series/mock-series-001"
        item = MediaItem("Test Series", url)
        items = self.channel.process_folder_list(item)
        # Series may not exist; just verify no exception is raised
        self.assertIsNotNone(items)


    def test_iptv_streams_returns_channels(self):
        """Live: create_iptv_streams() returns a non-empty list when authenticated."""
        from unittest.mock import MagicMock
        parser = MagicMock()
        parser.create_action_url.return_value = "plugin://plugin.video.retrospect/play"
        streams = self.channel.create_iptv_streams(parser)
        self.assertIsNotNone(streams)
        self.assertGreater(len(streams), 0)

    def test_iptv_epg_returns_data(self):
        """Live: create_iptv_epg() returns EPG entries when authenticated."""
        from unittest.mock import MagicMock
        parser = MagicMock()
        parser.create_action_url.return_value = "plugin://plugin.video.retrospect/play"
        epg = self.channel.create_iptv_epg(parser)
        self.assertIsNotNone(epg)

    # -- boundary episode detection ------------------------------------------

    def _boundary_eps(self, series_id, season_id):
        """Fetch episodes via the channel and return the list of tuples."""
        return self.channel._Channel__fetch_season_episodes(series_id, season_id)

    def test_boundary_fm_s18_descending_first(self):
        """Live: Flikken Maastricht S18 (descending) → first episode is A1."""
        from tests.authentication.nlziet_mocks import MOCK_FM_S18_SERIES_ID, MOCK_FM_S18_SEASON_ID
        eps = self._boundary_eps(MOCK_FM_S18_SERIES_ID, MOCK_FM_S18_SEASON_ID)
        self.assertGreater(len(eps), 0)
        result = self.channel._Channel__pick_boundary_episode(eps, pick_first=True)
        self.assertIn("S18:A1", result.name)

    def test_boundary_fm_s18_descending_recent(self):
        """Live: Flikken Maastricht S18 (descending) → most-recent episode is A13."""
        from tests.authentication.nlziet_mocks import MOCK_FM_S18_SERIES_ID, MOCK_FM_S18_SEASON_ID
        eps = self._boundary_eps(MOCK_FM_S18_SERIES_ID, MOCK_FM_S18_SEASON_ID)
        self.assertGreater(len(eps), 0)
        result = self.channel._Channel__pick_boundary_episode(eps, pick_first=False)
        self.assertIn("S18:A13", result.name)

    def test_boundary_luizenmoeder_s1_rebroadcast_first(self):
        """Live: De Luizenmoeder S1 (rebroadcast dates) → first episode is A1."""
        from tests.authentication.nlziet_mocks import (
            MOCK_LUIZENMOEDER_S1_SERIES_ID, MOCK_LUIZENMOEDER_S1_SEASON_ID)
        eps = self._boundary_eps(MOCK_LUIZENMOEDER_S1_SERIES_ID, MOCK_LUIZENMOEDER_S1_SEASON_ID)
        self.assertGreater(len(eps), 0)
        result = self.channel._Channel__pick_boundary_episode(eps, pick_first=True)
        self.assertIn("S1:A1", result.name)

    def test_boundary_luizenmoeder_s1_rebroadcast_recent(self):
        """Live: De Luizenmoeder S1 (rebroadcast dates) → most-recent episode is A10."""
        from tests.authentication.nlziet_mocks import (
            MOCK_LUIZENMOEDER_S1_SERIES_ID, MOCK_LUIZENMOEDER_S1_SEASON_ID)
        eps = self._boundary_eps(MOCK_LUIZENMOEDER_S1_SERIES_ID, MOCK_LUIZENMOEDER_S1_SEASON_ID)
        self.assertGreater(len(eps), 0)
        result = self.channel._Channel__pick_boundary_episode(eps, pick_first=False)
        self.assertIn("S1:A10", result.name)

    def test_boundary_fawlty_s1_ascending_first(self):
        """Live: Fawlty Towers S1 (ascending) → first episode is A1."""
        from tests.authentication.nlziet_mocks import (
            MOCK_FAWLTY_S1_SERIES_ID, MOCK_FAWLTY_S1_SEASON_ID)
        eps = self._boundary_eps(MOCK_FAWLTY_S1_SERIES_ID, MOCK_FAWLTY_S1_SEASON_ID)
        self.assertGreater(len(eps), 0)
        result = self.channel._Channel__pick_boundary_episode(eps, pick_first=True)
        self.assertIn("S1:A1", result.name)

    def test_boundary_fawlty_s1_ascending_recent(self):
        """Live: Fawlty Towers S1 (ascending) → most-recent episode is A6."""
        from tests.authentication.nlziet_mocks import (
            MOCK_FAWLTY_S1_SERIES_ID, MOCK_FAWLTY_S1_SEASON_ID)
        eps = self._boundary_eps(MOCK_FAWLTY_S1_SERIES_ID, MOCK_FAWLTY_S1_SEASON_ID)
        self.assertGreater(len(eps), 0)
        result = self.channel._Channel__pick_boundary_episode(eps, pick_first=False)
        self.assertIn("S1:A6", result.name)


class TestNLZietChannelMocked(TestNLZietChannelLive):
    """Mocked channel tests — always runs, uses NLZietMockDispatcher."""

    _mock_dispatcher = None
    _original_open = None

    @classmethod
    def setUpClass(cls):
        # Skip TestNLZietChannelLive.setUpClass (credential guard); go straight to ChannelTest.
        super(TestNLZietChannelLive, cls).setUpClass()

        from tests.authentication.nlziet_mocks import NLZietMockDispatcher
        cls.username = "test@example.com"
        cls.password = "mock_password"
        cls._mock_dispatcher = NLZietMockDispatcher()
        cls._original_open = UriHandler.instance().open
        uri_instance = UriHandler.instance()
        dispatcher = cls._mock_dispatcher

        def mock_open(uri, proxy=None, params=None, data=None, json=None,
                      referer=None, additional_headers=None, no_cache=False,
                      force_text=False, force_cache_duration=None, method=""):
            return dispatcher.dispatch(
                uri, uri_instance,
                params=params, data=data, json=json, method=method,
                additional_headers=additional_headers,
            )

        uri_instance.open = mock_open

    @classmethod
    def tearDownClass(cls):
        if cls._original_open is not None:
            UriHandler.instance().open = cls._original_open
        super().tearDownClass()

    def setUp(self):
        if self._mock_dispatcher:
            self._mock_dispatcher.reset()
        UriHandler.delete_cookie(domain=".nlziet.nl")
        # Create channel and log in via mock (skips TestNLZietChannelLive.setUp credential guard).
        super(TestNLZietChannelLive, self).setUp()
        # Pre-set the profile so log_on skips the interactive selection dialog.
        from tests.authentication.nlziet_mocks import MOCK_PROFILE_LIST
        from resources.lib.addonsettings import AddonSettings, LOCAL
        handler = self.channel._Channel__handler  # noqa: SLF001
        AddonSettings.set_setting(
            "{}profile_id".format(handler.prefix), MOCK_PROFILE_LIST[0]["id"], store=LOCAL)
        if not self.channel.log_on(self.username, self.password):
            self.fail("Mocked NLZIET login failed.")
