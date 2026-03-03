# SPDX-License-Identifier: GPL-3.0-or-later
"""NLZiet channel for Retrospect."""

import datetime
import json
import re
import threading
import time
from typing import Optional, List, Tuple, Union

import xbmc
import xbmcaddon

from http import HTTPStatus

from resources.lib import chn_class
from resources.lib import contenttype
from resources.lib import mediatype
from resources.lib.actions import action
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.authentication.authenticator import Authenticator
from resources.lib.authentication.nlzietoauth2handler import NLZIETOAuth2Handler
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.streams.mpd import Mpd
from resources.lib.urihandler import UriHandler
from resources.lib.xbmcwrapper import XbmcWrapper

from api import (
    API_V7_APPCONFIG,
    API_V7_CONTINUE_WATCHING,
    API_V8_PROFILE, API_V8_RECOMMEND,
    API_V8_SERIES, API_V8_SERIES_PREFIX, API_V8_TRACKED_SERIES,
    API_V9_CONTINUE_WATCHING,
    API_V9_EPG, API_V9_EPG_LIVE_CHANNEL, API_V9_EPG_DATE, API_V9_EPG_LIVE,
    API_V9_PLACEMENT_EXPLORE_PREFIX, API_V9_LIVE_HANDSHAKE,
    API_V9_PLACEMENT,
    API_V9_RECOMMEND_WITH, API_V9_RECOMMEND_FILTERED,
    API_V9_SEARCH, API_V9_SEARCH_PREFIX,
    API_V9_SEASON_ALL_EPISODES,
    API_V9_SERIES_EPISODES, API_V9_SERIES_PLAY, API_V9_SERIES_PREFIX,
    API_V9_SERIES_SEASON_EPISODES,
    API_V9_STREAM_HANDSHAKE, API_V9_TRACKED_SERIES,
    API_V9_VOD_HANDSHAKE, API_V9_WATCH_IN_ADVANCE,
    APPCONFIG_CACHE_KEY, APPCONFIG_CACHE_TTL,
    EPG_ENRICH_BATCH_SIZE, EPG_SIGNAL_FILE_NAME,
)
import epg_enrichment


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        self.noImage = channel_info.icon
        self.mainListUri = "#mainlist"
        self.baseUrl = "https://api.nlziet.nl"
        self.__register_parsers()

        self.__handler = NLZIETOAuth2Handler()
        self.__authenticator = Authenticator(self.__handler)

    def __register_parsers(self):
        """Register URL data parsers for all supported API endpoints."""

        self._add_data_parser("#mainlist",
                              preprocessor=self.get_initial_folder_items,
                              requires_logon=True)

        self._add_data_parser(API_V9_PLACEMENT_EXPLORE_PREFIX,
                              name="Explore category page",
                              preprocessor=self.get_explore_items,
                              requires_logon=True)

        self._add_data_parser(API_V9_EPG_LIVE,
                              name="Live TV channels", json=True,
                              requires_logon=True,
                              parser=["data"],
                              creator=self.create_live_channel_item,
                              updater=self.update_live_item)

        self._add_data_parser(API_V9_RECOMMEND_WITH,
                              name="VOD content list (v9)", json=True,
                              requires_logon=True,
                              parser=["data"],
                              creator=self.create_vod_item,
                              updater=self.update_vod_item)

        self._add_data_parser(API_V9_RECOMMEND_FILTERED,
                              name="Genre-filtered content", json=True,
                              requires_logon=True,
                              parser=["data"],
                              creator=self.create_vod_item,
                              updater=self.update_vod_item)

        self._add_data_parser(API_V8_RECOMMEND,
                              name="VOD content list", json=True,
                              requires_logon=True,
                              parser=["data"],
                              creator=self.create_vod_item,
                              updater=self.update_vod_item)

        self._add_data_parser(API_V9_TRACKED_SERIES,
                              name="Watchlist (v9)", json=True,
                              requires_logon=True,
                              parser=["data"],
                              creator=self.create_vod_item,
                              updater=self.update_vod_item)

        self._add_data_parser(API_V8_TRACKED_SERIES,
                              name="Watchlist", json=True,
                              requires_logon=True,
                              parser=[],
                              creator=self.create_vod_item,
                              updater=self.update_vod_item)

        self._add_data_parser(API_V9_CONTINUE_WATCHING,
                              name="Continue watching (v9)", json=True,
                              requires_logon=True,
                              parser=["data"],
                              creator=self.create_vod_item,
                              updater=self.update_vod_item)

        self._add_data_parser(API_V7_CONTINUE_WATCHING,
                              name="Continue watching", json=True,
                              requires_logon=True,
                              parser=[],
                              creator=self.create_vod_item,
                              updater=self.update_vod_item)

        self._add_data_parser(API_V9_WATCH_IN_ADVANCE,
                              name="Watch in advance", json=True,
                              requires_logon=True,
                              parser=["data"],
                              creator=self.create_vod_item,
                              updater=self.update_vod_item)

        self._add_data_parser(API_V8_SERIES_PREFIX,
                              name="Series detail (v8)", json=True,
                              requires_logon=True,
                              preprocessor=self.extract_series_data)

        self._add_data_parser(API_V9_SERIES_PREFIX,
                              name="Series episodes (v9)", json=True,
                              requires_logon=True,
                              preprocessor=self.extract_series_title,
                              parser=["data"],
                              creator=self.create_episode_item,
                              postprocessor=self.deduplicate_episode_titles,
                              updater=self.update_vod_item)

        self._add_data_parser(API_V9_SEARCH_PREFIX,
                              name="Search results", json=True,
                              requires_logon=True,
                              parser=["data"],
                              creator=self.create_search_result_item,
                              updater=self.update_vod_item)

        self._add_data_parser(API_V9_STREAM_HANDSHAKE,
                              name="VOD stream resolver",
                              requires_logon=True,
                              updater=self.update_vod_item)

    # -- Authentication ----------------------------------------------------

    @property
    def search_profile_id(self) -> Optional[str]:
        """Return the active NLZIET profile ID for search history scoping.

        Returns None if no profile is active (e.g. during menu operations
        before login), which falls back to the plain "search" key.
        """
        profile_id = AddonSettings.get_setting(
            f"{self.__handler.prefix}profile_id", store=LOCAL)
        return profile_id or None

    def log_on(self, username=None, password=None, interactive=True) -> bool:
        if self.loggedOn:
            return True

        result = self.__handler.active_authentication()
        if result.logged_on:
            if not self.__validate_token():
                return False
            self.loggedOn = True
            self.__set_auth_headers()
            self.__select_profile_if_needed()
            self.__set_auth_headers()
            return True

        username = username or self._get_setting("nlziet_username", value_for_none=None)
        password = password or self._get_setting("nlziet_password", value_for_none=None)

        if username and password:
            if self.__handler.use_device_flow:
                self.__handler = NLZIETOAuth2Handler(use_device_flow=False)
                self.__authenticator = Authenticator(self.__handler)
            result = self.__authenticator.log_on(username=username, password=password,
                channel_guid=self.guid, setting_id="nlziet_password")
            if not result.logged_on:
                XbmcWrapper.show_dialog(
                    "NLZIET",
                    LanguageHelper.get_localized_string(LanguageHelper.LoginFirst))
                return False
        else:
            if not interactive:
                return False
            if not self.__run_device_flow():
                return False

        self.loggedOn = True
        self.__set_auth_headers()
        self.__welcome_and_select_profile()
        self.__set_auth_headers()
        return True

    def __validate_token(self) -> bool:
        """Validate the current token against the NLZiet API.

        :return: True if the token is valid, False otherwise.
        """

        token = self.__handler.get_valid_token()
        if not token:
            msg = LanguageHelper.get_localized_string(LanguageHelper.SessionExpired)
            XbmcWrapper.show_dialog("NLZIET", msg)
            return False

        headers = {
            "Authorization": "Bearer {}".format(token),
            "Accept": "application/json"
        }
        try:
            response = UriHandler.open(API_V8_PROFILE,
                                       additional_headers=headers, no_cache=True)
            status = UriHandler.instance().status
            if status.error:
                if status.code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                    msg = LanguageHelper.get_localized_string(LanguageHelper.SessionExpired)
                    XbmcWrapper.show_dialog("NLZIET", msg)
                else:
                    msg = LanguageHelper.get_localized_string(LanguageHelper.ConnectionError)
                    XbmcWrapper.show_dialog("NLZIET", msg)
                return False
        except Exception:
            Logger.error("NLZIET: Token validation failed", exc_info=True)
            msg = LanguageHelper.get_localized_string(LanguageHelper.ConnectionError)
            XbmcWrapper.show_dialog("NLZIET", msg)
            return False

        return True

    def __set_auth_headers(self):
        """Set the Bearer token and required app headers for API requests."""

        token = self.__handler.get_valid_token()
        if token:
            self.httpHeaders["Authorization"] = "Bearer {}".format(token)
        self.httpHeaders["Nlziet-AppName"] = "WebApp"
        self.httpHeaders["Nlziet-AppVersion"] = "5.65.5"

    # -- Main list ---------------------------------------------------------

    def get_initial_folder_items(self, data):
        """Create the initial folder items by fetching placement rows.

        Fetches ``/v9/placement/rows/home`` for adult profiles or
        ``/v9/placement/rows/kids-home`` for kids profiles and creates
        folder items from the returned components.

        :param str data: The retrieve data that was loaded for the current item and URL.
        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []

        if not self.loggedOn:
            return data, items

        page = "kids-home" if self.__handler.profile_type == "ChildYoung" else "home"
        placement_url = API_V9_PLACEMENT.format(page)
        Logger.debug("NLZIET: Fetching placement rows from %s", placement_url)

        placement_data = UriHandler.open(
            placement_url, additional_headers=self.httpHeaders, no_cache=True)
        if not placement_data:
            Logger.warning("NLZIET: Empty placement response, falling back to search only")
            return data, items

        search = FolderItem(LanguageHelper.get_localized_string(LanguageHelper.Search),
                             self.search_url, content_type=contenttype.TVSHOWS)
        search.complete = True
        search.dontGroup = True
        items.append(search)

        placement = JsonHelper(placement_data)
        components = placement.get_value("components") or []

        for component in components:
            result = self.__create_placement_item(component)
            if isinstance(result, list):
                items.extend(result)
            elif result:
                items.append(result)

        return data, items

    def get_explore_items(self, data):
        """Create folder items for an explore category page.

        Fetches a placement page (e.g. ``explore-series``) and turns each
        ``ItemTileList`` component into a navigable genre folder.

        :param str data: The retrieve data that was loaded for the current item and URL.
        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        items = []
        if not data:
            return data, items

        placement = JsonHelper(data)
        components = placement.get_value("components") or []

        for component in components:
            result = self.__create_placement_item(component)
            if isinstance(result, list):
                items.extend(result)
            elif result:
                items.append(result)

        return data, items

    _PLACEMENT_TYPES = {"ItemTileList", "ItemTileListWithFolder",
                        "PersonalizedProgramLocationsLive"}

    def __create_placement_item(self, component):
        """Create a FolderItem from a placement row component.

        Handles ``Placements`` components by expanding their sub-items into
        individual explore-page folders.

        :param dict component: A single component from the placement response.
        :return: A FolderItem, a list of FolderItems, or None.
        :rtype: FolderItem|list[FolderItem]|None

        """

        comp_type = component.get("type", "")

        if comp_type == "Placements":
            return self.__create_explore_items(component.get("items", []))
        url = component.get("url") or component.get("parameters", {}).get("url")
        title = component.get("title") or component.get("parameters", {}).get("title")
        if comp_type not in self._PLACEMENT_TYPES or not url or not title:
            return None

        item = FolderItem(title, url, content_type=contenttype.VIDEOS)
        if comp_type == "PersonalizedProgramLocationsLive":
            item.isLive = True
            item.dontGroup = True
        item.complete = True
        item.HttpHeaders = self.httpHeaders
        return item

    def __create_explore_items(self, placement_items):
        """Create folder items for each explore category.

        :param list placement_items: Items from a Placements component.
        :return: A list of FolderItems for explore pages.
        :rtype: list[FolderItem]

        """

        items = []
        for entry in placement_items:
            entry_id = entry.get("id")
            title = entry.get("title")
            if not entry_id or not title:
                continue
            url = API_V9_PLACEMENT.format(entry_id)
            item = FolderItem(title, url, content_type=contenttype.TVSHOWS)
            item.dontGroup = True
            item.complete = True
            item.HttpHeaders = self.httpHeaders
            items.append(item)
        return items

    # -- Live TV channels --------------------------------------------------

    def create_live_channel_item(self, result_set: dict) -> Optional[MediaItem]:
        """Create a MediaItem for a live TV channel.

        :param dict result_set: A single entry from the ``data`` array of the
            ``/v9/epg/programlocations/live`` response.
        :return: A playable MediaItem or None.

        """

        channel = result_set.get("channel")
        if not channel:
            return None

        content = channel.get("content", {})
        channel_id = content.get("id")
        title = content.get("title", "")
        if not channel_id or not title:
            return None

        # The item URL encodes the channel ID so the updater can find the
        # correct assetId at playback time.
        url = API_V9_EPG_LIVE_CHANNEL.format(channel_id)

        item = MediaItem(title, url, media_type=mediatype.VIDEO)
        item.isLive = True
        item.isGeoLocked = True
        item.isDrmProtected = True
        item.complete = False

        logo = content.get("logo", {})
        logo_url = logo.get("normalUrl")
        if logo_url:
            item.thumb = logo_url
            item.icon = logo_url

        # Store the current program's assetId for direct playback if available.
        program_locations = result_set.get("programLocations", [])
        if program_locations:
            first_program = program_locations[0].get("content", {})
            asset_id = first_program.get("assetId")
            if asset_id:
                item.metaData["asset_id"] = asset_id

            # Add current program info if available.
            program_title = first_program.get("title", "")
            if program_title:
                item.description = program_title

        if channel.get("missingSubscriptionFeature") is not None:
            item.isPaid = True

        item.HttpHeaders = self.httpHeaders
        return item

    def update_live_item(self, item: MediaItem) -> MediaItem:
        """Fetch the DASH stream URL for a live channel.

        :param MediaItem item: The item to update with stream info.
        :return: The updated item.

        """

        Logger.debug("Updating live stream for: %s", item.name)

        channel_id = item.url.rsplit("channel=", 1)[-1] if "channel=" in item.url else ""
        if not channel_id:
            Logger.error("No channel ID in URL for: %s", item.name)
            return item

        try:
            adjustment = AddonSettings.get_channel_setting(self, "nlziet_live_start_offset")
            adjustment = int(float(adjustment)) if adjustment else 0
            adjustment = max(-120, min(120, adjustment))
        except (ValueError, TypeError):
            adjustment = 0

        appconfig = self.__load_appconfig()
        base_offset = appconfig.get("liveStreamRestartStartPadding", 180)
        start_offset = base_offset + adjustment
        start_offset = max(0, start_offset)

        handshake_url = API_V9_LIVE_HANDSHAKE.format(channel_id)
        if start_offset != 0:
            handshake_url = f"{handshake_url}&startOffsetInSeconds={start_offset}"

        item = self.__handle_stream_handshake(
            item, handshake_url, manifest_update="full")
        if start_offset > 0 and item.streams:
            item.streams[-1].add_property(
                "inputstream.adaptive.live_offset", str(start_offset))
        return item

    # -- VOD content (movies, series, trending) ----------------------------

    def create_vod_item(self, result_set: dict) -> Optional[MediaItem]:
        """Create an item from a ``/v8/recommend/*`` or watchlist response.

        Items without a ``type`` field (the ``/v8/recommend/series`` endpoint)
        are treated as series folders.  Items tagged ``"Movie"`` become
        playable movie items.  Everything else (``Vod``, ``Epg``) becomes a
        playable video item.

        :param dict result_set: A single ``data[]`` entry (contains ``content``).
        :return: A MediaItem, FolderItem, or None.

        """

        content = result_set.get("content", {})
        if not content:
            return None

        # Skip items explicitly marked as unavailable.
        if content.get("isAvailable") is False:
            return None

        item_id = content.get("id")
        title = content.get("title", "")
        if not item_id or not title:
            return None

        item_type = content.get("type")
        tags = content.get("tags") or []
        is_movie = "Movie" in tags

        if item_type is None or item_type == "Series":
            url = API_V8_SERIES.format(item_id)
            item = FolderItem(title, url, content_type=contenttype.EPISODES)
            item.complete = True
            item.dontGroup = True
        elif is_movie:
            url = self.__vod_handshake_url(item_id)
            item = MediaItem(title, url, media_type=mediatype.MOVIE)
            item.isDrmProtected = True
            item.isGeoLocked = True
            item.dontGroup = True
        else:
            url = self.__vod_handshake_url(item_id)
            item = MediaItem(title, url, media_type=mediatype.EPISODE)
            item.isDrmProtected = True
            item.isGeoLocked = True
            item.dontGroup = True

        # Trending/recommended items can carry episode numbering.
        numbering = content.get("formattedEpisodeNumbering") or ""
        if numbering:
            match = re.match(r"S(\d+):A(\d+)", numbering)
            if match:
                item.set_season_info(match.group(1), match.group(2))

        self.__set_vod_metadata(item, content)
        item.HttpHeaders = self.httpHeaders
        return item

    def extract_series_title(self, data):
        """Preprocessor for ``/v9/series/{id}/episodes`` URLs.

        Reads the series title stored in the parent season folder's metaData
        (set by :meth:`extract_series_data`) and caches it on this instance so
        that :meth:`create_episode_item` can populate ``tv_show_title`` for
        the Up Next integration.

        :param str data: Raw JSON response (passed through unchanged).
        :return: Tuple of (data, empty item list) — data is not modified.
        :rtype: tuple[str, list]

        """

        series_title = ""
        if self.parentItem:
            series_title = self.parentItem.metaData.get("nlziet:series_title", "")
        self.__current_series_title = series_title
        return data, []

    def create_episode_item(self, result_set: dict) -> Optional[MediaItem]:
        """Create a playable item from a ``/v9/series/{id}/episodes`` entry.

        :param dict result_set: A single ``data[]`` entry.
        :return: A playable MediaItem or None.

        """

        content = result_set.get("content", {})
        if not content:
            return None

        item_id = content.get("id")
        title = content.get("title") or content.get("subtitle", "")
        if not item_id or not title:
            return None

        url = self.__vod_handshake_url(item_id)
        series_title = getattr(self, "_Channel__current_series_title", "")
        item = MediaItem(title, url, media_type=mediatype.EPISODE,
                         tv_show_title=series_title or None)
        item.isDrmProtected = True
        item.isGeoLocked = True
        item.dontGroup = True

        subtitle = content.get("subtitle", "")
        # Episode numbering is embedded in the subtitle (e.g. "S1:A6 Title").
        numbering = content.get("formattedEpisodeNumbering") or ""
        match = re.match(r"S(\d+):A(\d+)", numbering or subtitle)
        if match:
            item.set_season_info(match.group(1), match.group(2))
            # Strip numbering prefix from subtitle for display.
            clean = re.sub(r"^S\d+:A\d+\s*", "", subtitle)
            if clean and clean != title:
                item.metaData["nlziet:subtitle"] = clean
        elif subtitle and subtitle != title:
            item.metaData["nlziet:subtitle"] = subtitle

        self.__set_vod_metadata(item, content)
        item.HttpHeaders = self.httpHeaders
        return item

    def deduplicate_episode_titles(self, data, items):
        """Disambiguate duplicate episode titles using subtitles.

        When all episodes share the same title (common for kids shows), each
        title is replaced by its subtitle.  When only some titles are
        duplicated (2+), those get ``subtitle (title)`` format while unique
        titles are left untouched.

        :param data:             Unused (required by post-processor signature).
        :param list[MediaItem] items: The items produced by the parser/creator.
        :return: The (potentially modified) list of items.
        :rtype: list[MediaItem]

        """

        episodes = [i for i in items if not i.is_folder]
        if len(episodes) < 2:
            return items

        from collections import Counter
        counts = Counter(e.name for e in episodes)
        unique_titles = len(counts)

        if unique_titles == 1:
            # All identical — use "subtitle (title)" to preserve context.
            for episode in episodes:
                subtitle = episode.metaData.get("nlziet:subtitle")
                if subtitle:
                    episode.name = "{} ({})".format(subtitle, episode.name)
        elif any(c >= 2 for c in counts.values()):
            # Partial duplicates — "subtitle (title)" for duplicated ones.
            for episode in episodes:
                if counts[episode.name] >= 2:
                    subtitle = episode.metaData.get("nlziet:subtitle")
                    if subtitle:
                        episode.name = "{} ({})".format(subtitle, episode.name)

        return items

    def create_search_result_item(self, result_set: dict) -> Optional[MediaItem]:
        """Create an item from a ``/v9/search`` response entry.

        The search response uses ``type`` values ``"Movie"`` and ``"Series"``
        (different from the recommend endpoints).

        :param dict result_set: A single ``data[]`` entry.
        :return: A MediaItem, FolderItem, or None.

        """

        content = result_set.get("content", {})
        if not content:
            Logger.debug("NLZIET search: skipping entry with empty content")
            return None

        item_id = content.get("id")
        title = content.get("title", "")
        item_type = content.get("type", "")
        if not item_id or not title:
            Logger.debug("NLZIET search: skipping entry without id/title: "
                        "id=%s, title=%s, type=%s", item_id, title, item_type)
            return None

        Logger.debug("NLZIET search result: id=%s, title='%s', type='%s'",
                     item_id, title, item_type)
        tags = content.get("tags") or []

        if item_type == "Series" or item_type is None:
            url = API_V8_SERIES.format(item_id)
            item = FolderItem(title, url, content_type=contenttype.EPISODES)
            item.complete = True
            item.dontGroup = True
        elif item_type == "Movie" or "Movie" in tags:
            url = self.__vod_handshake_url(item_id)
            item = MediaItem(title, url, media_type=mediatype.MOVIE)
            item.isDrmProtected = True
            item.isGeoLocked = True
            item.dontGroup = True
        else:
            url = self.__vod_handshake_url(item_id)
            item = MediaItem(title, url, media_type=mediatype.EPISODE)
            item.isDrmProtected = True
            item.isGeoLocked = True
            item.dontGroup = True

        self.__set_vod_metadata(item, content)
        item.HttpHeaders = self.httpHeaders
        return item

    def extract_series_data(self, data):
        """Preprocessor for ``/v8/series/{id}`` detail URLs.

        Parses the season list from the series detail response and returns
        them as folder items pointing to ``/v9/series/{id}/episodes?`` URLs.
        The downstream parser is skipped because the data is replaced with
        an empty string.

        Shortcut items (Continue Watching, Most Recent Episode, First Episode)
        are prepended before the season folders so users can jump straight to
        an episode without drilling into seasons.

        :param str data: Raw JSON response.
        :return: Tuple of (data, items).
        :rtype: tuple[str, list[MediaItem]]

        """

        # Series detail — extract seasons.
        json_data = JsonHelper(data)
        # The API may return {"content": {...}} or {"data": {"content": {...}}}.
        series_content = json_data.get_value("content", fallback=None)
        if not series_content:
            series_content = json_data.get_value("data", "content", fallback={})
        if not series_content:
            return "", []

        series_id = series_content.get("id", "")
        series_title = series_content.get("title", "")
        # API returns seasons newest-first; reverse so seasons[0] = oldest
        # (used by shortcuts) and present newest-first to the user below.
        seasons = list(reversed(series_content.get("seasons", [])))

        items = []
        if seasons:
            # Present newest season first in the folder listing.
            for season in reversed(seasons):
                season_id = season.get("id")
                season_title = season.get("title", "")
                if not season_id:
                    continue

                url = API_V9_SERIES_SEASON_EPISODES.format(
                    series_id, season_id)
                folder = FolderItem(season_title or series_title, url,
                                    content_type=contenttype.EPISODES)
                folder.complete = True
                folder.metaData["nlziet:series_title"] = series_title
                items.append(folder)
        else:
            # Seasonless series — fetch episodes directly to avoid an
            # intermediate folder that just duplicates the series name.
            url = API_V9_SERIES_EPISODES.format(series_id)
            episodes_item = MediaItem(series_title, url, media_type=mediatype.VIDEO)
            episodes = self.process_folder_list(episodes_item)
            items.extend(episodes)

        shortcuts = self.__build_episode_shortcuts(series_id, seasons)
        # Return empty data so the parser does not run again.
        return "", shortcuts + items

    def update_vod_item(self, item: MediaItem) -> MediaItem:
        """Fetch the DASH stream URL for a VOD or replay item.

        :param MediaItem item: The item to update.
        :return: The updated item.

        """

        Logger.debug("Updating VOD stream for: %s", item.name)
        return self.__handle_stream_handshake(item, item.url)

    def search_site(self, url=None, needle=None):
        """Search the NLZiet catalogue.

        :param str|None url:    Unused (search URL is constructed here).
        :param str|None needle: The search query.
        :return: A list of search result items.
        :rtype: list[MediaItem]

        """

        Logger.debug("NLZIET search_site: needle=%r", needle)
        Logger.debug("NLZIET search_site: url template=%s", API_V9_SEARCH)
        items = chn_class.Channel.search_site(self, API_V9_SEARCH, needle)
        Logger.debug("NLZIET search_site: returned %d items", len(items))
        return items

    def __build_episode_shortcuts(self, series_id, seasons):
        """Build Continue / Most Recent / First episode shortcut items.

        :param str series_id:    The series ID.
        :param list[dict] seasons: Season dicts from the series detail response,
                                   newest-first (as returned by the API).
        :return: Up to three playable shortcut items.
        :rtype: list[MediaItem]

        """

        if not series_id or not seasons:
            return []

        continue_item = self.__fetch_continue_item(series_id)

        # ``seasons`` is oldest-first after the reversal in ``get_series_detail``.
        oldest_season_id = seasons[0].get("id", "")
        newest_season_id = seasons[-1].get("id", "")

        newest_eps = self.__fetch_season_episodes(series_id, newest_season_id)
        if oldest_season_id != newest_season_id:
            oldest_eps = self.__fetch_season_episodes(series_id, oldest_season_id)
        else:
            oldest_eps = newest_eps

        first_item = self.__pick_boundary_episode(oldest_eps, pick_first=True)
        recent_item = self.__pick_boundary_episode(newest_eps, pick_first=False)

        if first_item and recent_item and first_item.url == recent_item.url:
            recent_item = None

        if first_item:
            first_item.name = self.__shortcut_label(
                first_item, LanguageHelper.FirstEpisode)
        if recent_item:
            recent_item.name = self.__shortcut_label(
                recent_item, LanguageHelper.MostRecentEpisode)

        shortcuts = []
        if continue_item:
            first_id = first_item.url if first_item else None
            if continue_item.url != first_id:
                shortcuts.append(continue_item)
        if recent_item:
            shortcuts.append(recent_item)
        if first_item:
            shortcuts.append(first_item)

        return shortcuts

    @staticmethod
    def __shortcut_label(item, label_id):
        """Build a shortcut display name like ``First Episode: Title``.

        :param MediaItem item:  The shortcut item with metaData.
        :param int label_id:    LanguageHelper string ID for the label.
        :return: The formatted name.
        :rtype: str

        """

        label = LanguageHelper.get_localized_string(label_id)
        ep_title = item.metaData.get("nlziet:ep_title", "")
        if ep_title:
            return "{}: {}".format(label, ep_title)
        return label

    def __fetch_continue_item(self, series_id):
        """Fetch the "Continue Watching" episode via ``/v9/series/{id}/play``.

        :param str series_id: The series ID.
        :return: A playable MediaItem or None.
        :rtype: MediaItem|None

        """

        url = API_V9_SERIES_PLAY.format(series_id)
        data = UriHandler.open(url, additional_headers=self.httpHeaders,
                               no_cache=True)
        if not data:
            return None

        play_json = JsonHelper(data)
        content = play_json.get_value("content", fallback=None)
        if not content:
            return None

        content_id = content.get("id")
        ep_title = content.get("title", "")
        if not content_id:
            return None

        label = LanguageHelper.get_localized_string(LanguageHelper.ContinueWatching)
        name = "{}: {}".format(label, ep_title) if ep_title else label
        item = MediaItem(name, self.__vod_handshake_url(content_id),
                         media_type=mediatype.EPISODE)
        item.isDrmProtected = True
        item.isGeoLocked = True
        item.dontGroup = True
        self.__set_vod_metadata(item, content)
        item.HttpHeaders = self.httpHeaders
        return item

    def __fetch_season_episodes(self, series_id, season_id):
        """Fetch all episodes for a season.

        :param str series_id:  The series ID.
        :param str season_id:  The season ID.
        :return: List of ``(broadcastAt, item)`` tuples in API response order.
                 Date strings are ISO-8601 or empty when absent.
        :rtype: list[tuple[str, MediaItem]]

        """

        if not season_id:
            return []

        url = API_V9_SEASON_ALL_EPISODES.format(series_id, season_id)
        data = UriHandler.open(url, additional_headers=self.httpHeaders,
                               no_cache=True)
        if not data:
            return []

        episodes = JsonHelper(data).get_value("data", fallback=[])
        result = []
        for episode in episodes:
            content = episode.get("content", {})
            content_id = content.get("id")
            if not content_id:
                continue

            subtitle = content.get("subtitle") or content.get("title", "")
            item = MediaItem(subtitle, self.__vod_handshake_url(content_id),
                             media_type=mediatype.EPISODE)
            item.isDrmProtected = True
            item.isGeoLocked = True
            item.dontGroup = True
            item.metaData["nlziet:ep_title"] = subtitle
            self.__set_vod_metadata(item, content)
            item.HttpHeaders = self.httpHeaders
            broadcast_at = content.get("broadcastAt") or ""
            result.append((broadcast_at, item))

        return result

    @staticmethod
    def __pick_boundary_episode(eps, pick_first):
        """Pick the earliest or most-recent episode from API results.

        The API always returns episodes in a logically correct order (episode
        numbers are monotonic), but the direction varies per series: some are
        newest-first (descending), others oldest-first (ascending).

        Direction is detected by checking whether ``broadcastAt`` timestamps
        are monotonically increasing or decreasing.  When ``broadcastAt`` is
        non-monotonic (re-broadcasts, bulk imports) or absent, we default to
        descending — the most common ordering across the NLZIET catalogue.

        :param list[tuple[str, MediaItem]] eps: (broadcastAt, item) tuples
               in API response order.
        :param bool pick_first: True for the earliest episode; False for the
               most-recent.
        :return: The selected MediaItem or None.
        :rtype: MediaItem|None

        """

        if not eps:
            return None
        if len(eps) == 1:
            return eps[0][1]

        ascending = Channel.__is_ascending(eps)

        if pick_first:
            return eps[0][1] if ascending else eps[-1][1]
        return eps[-1][1] if ascending else eps[0][1]

    @staticmethod
    def __is_ascending(eps):
        """Detect whether the API returned episodes oldest-first.

        Checks ``broadcastAt`` monotonicity: if every adjacent pair has a
        non-decreasing timestamp the list is ascending; if non-increasing it
        is descending.  Non-monotonic or missing timestamps default to
        descending (the most common API ordering).

        :param list[tuple[str, MediaItem]] eps: (broadcastAt, item) tuples.
        :return: True if the episode list is oldest-first (ascending).
        :rtype: bool

        """

        dates = [ba for ba, _ in eps if ba]
        if len(dates) < 2:
            return False

        is_asc = all(dates[i] <= dates[i + 1] for i in range(len(dates) - 1))
        if is_asc:
            return True

        # Not ascending — could be descending or non-monotonic; both → False.
        return False

    @staticmethod
    def __vod_handshake_url(content_id):
        """Build a v9 stream handshake URL for on-demand playback.

        :param str content_id: The content ID.
        :return: The handshake URL.
        :rtype: str

        """

        return API_V9_VOD_HANDSHAKE.format(content_id)

    def __handle_stream_handshake(self, item, handshake_url,
                                  manifest_update=None):
        """Perform a v9 stream handshake and configure the item for playback.

        :param MediaItem item:          The item to update.
        :param str handshake_url:       The full handshake URL.
        :param str|None manifest_update: If set, passed as manifest_update_params.
        :return: The updated item.
        :rtype: MediaItem

        """

        data = UriHandler.open(handshake_url, additional_headers=self.httpHeaders,
                               no_cache=True)
        if not data:
            Logger.error("Empty handshake response for: %s", item.name)
            return item

        json_data = JsonHelper(data)

        errors = json_data.get_value("errors", fallback=None)
        if errors:
            self.__handle_handshake_error(item, errors)
            return item

        mpd_url = json_data.get_value("manifestUrl", fallback=None)
        if not mpd_url:
            Logger.error("No stream URI in handshake for: %s", item.name)
            return item

        stream = item.add_stream(mpd_url, 0)

        drm = json_data.get_value("drm", fallback={})
        license_url = drm.get("licenseUrl") if drm else None
        if license_url:
            license_headers = drm.get("headers", {})
            license_key = Mpd.get_license_key(
                license_url, key_type="R", key_headers=license_headers)
            kwargs = {"license_key": license_key}
            if manifest_update:
                kwargs["manifest_update_params"] = manifest_update
            Mpd.set_input_stream_addon_input(stream, **kwargs)
        else:
            Mpd.set_input_stream_addon_input(stream)

        item.complete = True
        return item

    @staticmethod
    def __handle_handshake_error(item, errors):
        """Log and handle errors from a stream handshake response.

        :param MediaItem item: The item that failed.
        :param errors: Error data from the API (list or dict).

        """

        if isinstance(errors, dict):
            errors = [e for v in errors.values()
                      for e in (v if isinstance(v, list) else [v])]
        if not errors:
            return

        first = errors[0]
        if isinstance(first, str):
            Logger.error("Handshake error for %s: %s", item.name, first)
            return

        error_type = first.get("type", "")
        error_msg = first.get("message", "")
        Logger.error("Handshake error for %s: %s - %s",
                     item.name, error_type, error_msg)

        if error_type == "MaximumStreamsReached":
            error_data = errors[0].get("data", {})
            max_streams = str(error_data.get("maximumNumberOfStreams", "?"))
            msg = LanguageHelper.get_localized_string(LanguageHelper.MaxStreamsReached)
            msg = msg.replace("{0}", max_streams).replace("{1}", max_streams)
            XbmcWrapper.show_dialog("NLZIET", msg)

    def __set_vod_metadata(self, item, content):
        """Set common metadata fields on a VOD item.

        :param MediaItem item: The item to update.
        :param dict content:   The ``content`` dict from the API response.

        """

        subtitle = content.get("subtitle", "")
        description = content.get("description", "")
        if subtitle and description and subtitle != description:
            description = "[B]{}[/B]\n{}".format(subtitle, description)
        elif not description:
            description = subtitle
        availability = content.get("formattedAvailabilityWindow", "")
        if availability and description:
            description = "{}\n\n{}".format(description, availability)
        if description:
            item.description = description

        image = content.get("image") or {}
        item.thumb = image.get("landscapeUrl") or image.get("portraitUrl") or item.thumb
        item.poster = image.get("portraitUrl") or item.poster

        logo = content.get("logo") or {}
        if logo.get("normalUrl"):
            item.icon = logo["normalUrl"]

        provider = content.get("contentProvider", "")
        if provider:
            item.set_info_label("studio", provider)

        duration = content.get("formattedDuration", "")
        if duration:
            item.set_info_label("duration", self.__parse_duration(duration))

        broadcast = content.get("broadcastedAt", "")
        if broadcast:
            # "2026-02-19T20:30:00+01:00"
            match = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", broadcast)
            if match:
                item.set_date(*[int(g) for g in match.groups()],
                              text=content.get("formattedDate"))

        expires = content.get("availableUntil", "")
        if expires:
            match = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", expires)
            if match:
                item.set_expire_datetime(None, *[int(g) for g in match.groups()])

    @staticmethod
    def __parse_duration(formatted):
        """Parse a formatted duration string like ``"1u 23m"`` into seconds.

        :param str formatted: Duration string from the API.
        :return: Duration in seconds, or 0 if unparseable.
        :rtype: int

        """

        total = 0
        hours = re.search(r"(\d+)\s*u", formatted)
        if hours:
            total += int(hours.group(1)) * 3600
        minutes = re.search(r"(\d+)\s*m", formatted)
        if minutes:
            total += int(minutes.group(1)) * 60
        return total

    # -- Welcome & Profile -------------------------------------------------

    def __welcome_and_select_profile(self):
        """Show welcome dialog and prompt for profile selection if needed."""

        user_info = self.__handler.get_user_info()
        if user_info:
            display_name = user_info.get("name") or user_info.get("email", "NLZiet User")
        else:
            display_name = "NLZiet User"

        welcome = LanguageHelper.get_localized_string(LanguageHelper.WelcomeUser)
        XbmcWrapper.show_dialog("NLZIET", welcome.replace("{0}", display_name))
        self.__select_profile_if_needed()

    def __select_profile_if_needed(self):
        """Prompt for profile selection if no profile is currently selected.

        When a profile is already stored, performs a token exchange so the
        access token is scoped to that profile (required for server-side
        content filtering such as kids profiles).
        """

        current = self.__handler.get_profile()
        if current:
            # Re-exchange token for the stored profile so API filtering works.
            self.__handler.set_profile(current["id"])
            return

        profiles = self.__handler.list_profiles()
        if not profiles:
            Logger.warning("NLZIET: No profiles available")
            return

        if len(profiles) == 1:
            self.__handler.set_profile(profiles[0]["id"])
            Logger.info("NLZIET: Auto-selected only available profile: %s", profiles[0]["displayName"])
            return

        options = [p["displayName"] for p in profiles]
        label = LanguageHelper.get_localized_string(LanguageHelper.SelectProfile)
        selected = XbmcWrapper.show_selection_dialog(label, options)
        if selected < 0:
            Logger.info("NLZIET: Profile selection cancelled")
            return

        self.__handler.set_profile(profiles[selected]["id"])

    # -- Device flow -------------------------------------------------------

    def __run_device_flow(self) -> bool:
        """Run device flow authentication with progress dialog and retry logic.

        :return: True if authentication succeeded, False otherwise.
        """

        while True:
            device_name = xbmc.getInfoLabel("System.FriendlyName") or "Kodi Retrospect"
            try:
                flow = self.__handler.start_device_flow(device_name)
            except OSError:
                msg = LanguageHelper.get_localized_string(LanguageHelper.ConnectionError)
                XbmcWrapper.show_dialog("NLZIET", msg)
                return False
            if not flow:
                msg = LanguageHelper.get_localized_string(LanguageHelper.DeviceSetupFailed)
                XbmcWrapper.show_dialog("NLZIET", msg)
                return False

            from urllib.parse import quote
            qr_url = "{}?code={}&name={}".format(
                NLZIETOAuth2Handler.DEVICE_PORTAL_URL,
                quote(flow["user_code"]), quote(device_name))

            result = self.__poll_with_progress(flow, qr_url)
            if result == "success":
                return True
            if result == "cancelled":
                return False
            if result == "manual":
                return self.__manual_login()

            timeout_msg = LanguageHelper.get_localized_string(LanguageHelper.DeviceSetupTimeout)
            if not XbmcWrapper.show_yes_no("NLZIET", timeout_msg):
                return False

    def __poll_with_progress(self, flow: dict, qr_url: str) -> str:
        """Poll device flow with a progress dialog.

        :param flow:   The device flow response from start_device_flow()
        :param qr_url: URL to encode as a QR code, passed to the dialog.
        :return: "success", "cancelled", "manual", or "timeout"
        """

        user_code = flow["user_code"]
        verification_uri = flow["verification_uri"]
        device_code = flow["device_code"]
        interval = max(flow.get("interval", 5), 1)
        expires_in = flow.get("expires_in", 900)

        title = LanguageHelper.get_localized_string(LanguageHelper.DeviceSetupTitle)
        visit_text = LanguageHelper.get_localized_string(LanguageHelper.DeviceSetupVisit)
        enter_code = LanguageHelper.get_localized_string(LanguageHelper.DeviceSetupEnterCode)
        cancel_lbl = LanguageHelper.get_localized_string(LanguageHelper.Cancel)
        manual_lbl = LanguageHelper.get_localized_string(LanguageHelper.ManualLogin)

        from resources.lib.deviceauthdialog import DeviceAuthDialog
        from resources.lib.retroconfig import Config
        addon_path = Config.rootDir.rstrip("/\\")
        dialog = DeviceAuthDialog("DeviceAuthDialog.xml", addon_path)
        dialog.set_content(
            title, visit_text, verification_uri, enter_code,
            user_code, expires_in, cancel_lbl, manual_label=manual_lbl,
            qr_url=qr_url, logo_path=self.icon)

        monitor = xbmc.Monitor()
        start_time = time.time()
        end_time = start_time + expires_in
        auth_result = []

        def _poll_worker():
            _interval = interval
            _time_since_poll = _interval
            _attempts = 0
            try:
                while time.time() < end_time:
                    if dialog.stop_event.wait(0.5):
                        return

                    if monitor.abortRequested():
                        auth_result.append("cancelled")
                        dialog.close()
                        return

                    elapsed = time.time() - start_time
                    pct = max(0.0, 100.0 - (elapsed / expires_in) * 100.0)
                    remaining = max(0, int(end_time - time.time()))
                    dialog.update_progress(pct, remaining)

                    _time_since_poll += 0.5
                    if _time_since_poll < _interval:
                        continue
                    _time_since_poll = 0.0
                    _attempts += 1

                    result = self.__handler.poll_device_flow_once(device_code)
                    if result == "success":
                        auth_result.append("success")
                        dialog.close()
                        return
                    elif result == "slow_down":
                        _interval += 1
                    elif result == "authorization_pending":
                        if _attempts > 10:
                            _interval = min(_interval + 1, 5)
                    elif result != "error":
                        auth_result.append("timeout")
                        dialog.close()
                        return

                auth_result.append("timeout")
                dialog.close()
            except Exception:
                Logger.error("Device flow poll worker failed", exc_info=True)
                try:
                    dialog.close()
                except Exception:
                    pass

        poll_thread = threading.Thread(target=_poll_worker, daemon=True)
        poll_thread.start()
        dialog.doModal()
        poll_thread.join(timeout=2.0)

        if dialog.manual_login:
            return "manual"
        if dialog.cancelled:
            return "cancelled"
        return auth_result[0] if auth_result else "timeout"

    def __manual_login(self) -> bool:
        """Prompt for username/password and attempt login."""

        import xbmcgui
        dialog = xbmcgui.Dialog()
        username_label = LanguageHelper.get_localized_string(30035)
        username = dialog.input("NLZIET - {}".format(username_label))
        if not username:
            return False
        pw_label = LanguageHelper.get_localized_string(30036)
        password = dialog.input("NLZIET - {}".format(pw_label), option=xbmcgui.ALPHANUM_HIDE_INPUT)
        if not password:
            return False

        self.__handler = NLZIETOAuth2Handler(use_device_flow=False)
        self.__authenticator = Authenticator(self.__handler)
        result = self.__handler.log_on(username, password)
        return result.logged_on

    # -- Settings actions --------------------------------------------------

    def setup_device(self):
        """Device flow authentication triggered from settings."""

        if self.__run_device_flow():
            self.__welcome_and_select_profile()

    def select_profile(self):
        """Re-trigger profile selection from settings."""

        if not self.__handler.active_authentication().logged_on:
            XbmcWrapper.show_dialog(
                "NLZIET",
                LanguageHelper.get_localized_string(LanguageHelper.LoginFirst))
            return

        self.__handler.clear_profile()
        self.__select_profile_if_needed()
        self.__set_auth_headers()
        xbmc.executebuiltin("Container.Refresh()")

    # -- IPTV Manager integration ------------------------------------------

    def create_iptv_streams(self, parameter_parser):
        """Provide live channel data for IPTV Manager.

        :param ActionParser parameter_parser: Action parser for building URLs.
        :return: List of IPTV stream dicts.
        :rtype: list

        """

        if not self.loggedOn:
            self.loggedOn = self.log_on(interactive=False)
        if not self.loggedOn:
            Logger.warning("NLZIET IPTV: Not authenticated, returning empty streams")
            return []

        live_data = UriHandler.open(API_V9_EPG_LIVE, additional_headers=self.httpHeaders)
        if not live_data:
            Logger.warning("NLZIET IPTV: Empty live channel response")
            return []

        json_data = JsonHelper(live_data)
        channels = json_data.get_value("data", fallback=json_data.json)
        if not isinstance(channels, list):
            channels = []

        parent_item = MediaItem("Live", API_V9_EPG_LIVE, media_type=mediatype.FOLDER)
        subscribed_only = (
            AddonSettings.get_channel_setting(self, "nlziet_epg_subscribed_only", "true") == "true"
        )

        items = []
        iptv_streams = []

        for channel_entry in channels:
            if subscribed_only:
                miss = channel_entry.get("channel", {}).get("missingSubscriptionFeature")
                if miss is not None:
                    continue

            item = self.create_live_channel_item(channel_entry)
            if item is None:
                continue
            items.append(item)

            content = channel_entry["channel"]["content"]
            logo_url = content.get("logo", {}).get("normalUrl", "")
            iptv_streams.append(dict(id=content["id"],
                name=content["title"],
                logo=logo_url,
                group=self.channelName,
                stream=parameter_parser.create_action_url(
                    self, action=action.PLAY_VIDEO, item=item,
                    store_id=parent_item.guid),
            ))

        parameter_parser.pickler.store_media_items(
            parent_item.guid, parent_item, items)
        Logger.info("NLZIET IPTV: Returning %d streams", len(iptv_streams))
        return iptv_streams

    def create_iptv_epg(self, parameter_parser):
        """Provide EPG data for IPTV Manager.

        The date window (past/future days) is read from the cached
        ``/v7/appconfig`` payload.  Programme-location data is fetched once
        per ``APPCONFIG_CACHE_TTL`` (300s) and cached locally; drain cycles
        reuse cached data so only the 10 item/detail enrichment calls hit
        the network.

        At the end of every call this method signals IPTV Manager to call
        again — with an adaptive delay that starts at 30s and backs off by
        30s per "empty cycle" (no new data) up to a 10-minute cap.  This
        keeps the EPG perpetually fresh while avoiding unnecessary load
        when the schedule is stable.

        :param ActionParser parameter_parser: Action parser for building URLs.
        :return: EPG dict keyed by channel ID.
        :rtype: dict

        """

        if not self.loggedOn:
            self.loggedOn = self.log_on(interactive=False)
        if not self.loggedOn:
            Logger.warning("NLZIET IPTV: Not authenticated, returning empty EPG")
            return {}

        # Load appconfig (cached); abort if the server has blocked the app.
        appconfig = self.__load_appconfig()
        if self.__check_app_blocked(appconfig):
            return {}

        days_past = appconfig.get("epgDateRangePastDays", 7)
        days_future = appconfig.get("epgDateRangeFutureDays", 7)

        # Pipeline: drain the batch queued by the previous call so newly-fetched
        # details are immediately included in the EPG we are about to build.
        prev_queue = epg_enrichment.load_enrich_queue()
        if prev_queue:
            batch = prev_queue[:EPG_ENRICH_BATCH_SIZE]
            epg_enrichment.fetch_and_cache(batch, self.httpHeaders)

        cache = epg_enrichment.load_detail_cache()
        subscribed_only = (
            AddonSettings.get_channel_setting(self, "nlziet_epg_subscribed_only", "true") == "true"
        )

        parent = MediaItem("EPG", API_V9_EPG, media_type=mediatype.FOLDER)
        iptv_epg = {}
        media_items = []
        all_programmes = []  # (contentItemId, assetId, start_ts, is_now, is_past)
        now_ts = time.time()

        # Load programme-location cache.  A stale cache triggers a full API
        # fetch and counts as an "interesting" cycle (resets backoff).
        progloc_cache, is_stale = epg_enrichment.load_progloc_cache()
        interesting_cycle = is_stale  # also set True if queue non-empty

        if is_stale:
            new_progloc = {"fetched_at": now_ts}
            subscribed_channels = set()  # populated from first stale fetch
        else:
            new_progloc = progloc_cache  # reuse; fetched_at is preserved
            subscribed_channels = set(progloc_cache.get("subscribed_channels", []))

        start = datetime.datetime.now() - datetime.timedelta(days=days_past)
        for day_offset in range(days_past + days_future + 1):
            air_date = start + datetime.timedelta(days=day_offset)
            date_str = air_date.strftime("%Y-%m-%d")

            if is_stale:
                epg_data = UriHandler.open(
                    API_V9_EPG_DATE.format(date_str),
                    additional_headers=self.httpHeaders)
                if not epg_data:
                    Logger.warning("NLZIET IPTV: No EPG data for %s", date_str)
                    continue
                json_data = JsonHelper(epg_data)
                channels = json_data.get_value("data", fallback=json_data.json)
                if not isinstance(channels, list):
                    continue

                day_entries = []
                for channel_entry in channels:
                    channel_data = channel_entry.get("channel", {})
                    channel_id = channel_data.get("content", {}).get("id")
                    if not channel_id:
                        continue
                    if channel_data.get("missingSubscriptionFeature") is None:
                        subscribed_channels.add(channel_id)
                    for prog in channel_entry.get("programLocations", []):
                        cdata = prog.get("content", {})
                        cid = cdata.get("contentItemId")
                        asset_id = cdata.get("assetId")
                        start_at = cdata.get("startAt")
                        end_at = cdata.get("endAt")
                        if not cid or not asset_id or not start_at or not end_at:
                            continue
                        try:
                            s_ts = datetime.datetime.fromisoformat(start_at).timestamp()
                            e_ts = datetime.datetime.fromisoformat(end_at).timestamp()
                        except (ValueError, AttributeError):
                            s_ts = e_ts = now_ts
                        day_entries.append([
                            cid, asset_id, s_ts, e_ts, channel_id,
                            start_at, end_at,
                            cdata.get("title"),
                            cdata.get("image", {}),
                            cdata.get("isMovie", False),
                            cdata.get("isReplayAllowed", False),
                            cdata,
                        ])
                new_progloc[date_str] = day_entries
            else:
                day_entries = progloc_cache.get(date_str, [])

            for entry in day_entries:
                (cid, asset_id, s_ts, e_ts, channel_id,
                 start_at, end_at, title, image, is_movie,
                 is_replay, cdata) = entry

                if not title or not start_at or not end_at:
                    continue

                if subscribed_only and subscribed_channels and channel_id not in subscribed_channels:
                    continue

                if channel_id not in iptv_epg:
                    iptv_epg[channel_id] = []

                epg_item = dict(start=start_at, stop=end_at, title=title)
                landscape = image.get("landscapeUrl") if isinstance(image, dict) else None
                if landscape:
                    epg_item["image"] = landscape

                cached = cache.get(cid) if cid else None
                if cached:
                    if cached.get("description"):
                        epg_item["description"] = cached["description"]
                    if cached.get("genre"):
                        epg_item["genre"] = cached["genre"]
                elif is_movie:
                    epg_item["genre"] = "Film"

                if is_replay and isinstance(cdata, dict):
                    replay_item = self.__create_replay_item(cdata, channel_id)
                    if replay_item:
                        media_items.append(replay_item)
                        epg_item["stream"] = parameter_parser.create_action_url(
                            self, action=action.PLAY_VIDEO,
                            item=replay_item, store_id=parent.guid)

                iptv_epg[channel_id].append(epg_item)

                if cid and asset_id:
                    is_now = s_ts <= now_ts < e_ts
                    is_past = e_ts < now_ts
                    all_programmes.append((cid, asset_id, s_ts, is_now, is_past))

        if is_stale:
            new_progloc["subscribed_channels"] = sorted(subscribed_channels)
            epg_enrichment.save_progloc_cache(new_progloc)

        parameter_parser.pickler.store_media_items(parent.guid, parent, media_items)

        # Rebuild enrichment queue with fresh time-relative priority ordering
        queue = epg_enrichment.build_enrich_queue(all_programmes, cache)
        epg_enrichment.save_enrich_queue(queue)
        Logger.debug("NLZIET IPTV: Enrich queue rebuilt (%d items)", len(queue))

        if queue:
            interesting_cycle = True

        # Adaptive backoff: slow down when idle, reset when there is work to do
        backoff_cycles = epg_enrichment.load_backoff_cycles()
        if interesting_cycle:
            backoff_cycles = 0
        else:
            backoff_cycles = min(
                backoff_cycles + 1,
                epg_enrichment._MAX_BACKOFF_CYCLES)  # NOSONAR
        epg_enrichment.save_backoff_cycles(backoff_cycles)

        delay = epg_enrichment.compute_signal_delay(backoff_cycles)
        Logger.debug("NLZIET IPTV: Signalling IPTV Manager (delay=%ds, backoff=%d)",
                     delay, backoff_cycles)
        self.__signal_iptv_manager(delay)

        Logger.info("NLZIET IPTV: Returning EPG for %d channels", len(iptv_epg))
        return iptv_epg

    def __create_replay_item(self, content, channel_id):
        """Create a playable MediaItem for an EPG replay stream.

        :param dict content: The program content dict from the EPG response.
        :param str channel_id: The channel ID for the replay URL.
        :return: A MediaItem or None if no assetId is available.
        :rtype: MediaItem|None

        """

        asset_id = content.get("assetId")
        if not asset_id:
            return None

        replay_url = API_V9_EPG_LIVE_CHANNEL.format(channel_id)
        item = MediaItem(content["title"], replay_url, media_type=mediatype.VIDEO)
        item.isGeoLocked = True
        item.isDrmProtected = True
        item.metaData["asset_id"] = asset_id
        item.HttpHeaders = self.httpHeaders
        return item

    def log_off(self):
        """Force a logoff for the channel."""

        self.__authenticator.log_off("", force=True)
        self.loggedOn = False
        msg = LanguageHelper.get_localized_string(LanguageHelper.LoggedOutSuccessfully)
        XbmcWrapper.show_dialog("NLZIET", msg)
        xbmc.executebuiltin("Container.Refresh()")

    # -- private helpers ---------------------------------------------------

    def __load_appconfig(self) -> dict:
        """Fetch and cache the /v7/appconfig payload.

        The response is cached in LocalSettings for ``APPCONFIG_CACHE_TTL``
        seconds (default 300s, matches the server's own ``epgCacheTime``).
        A fresh fetch is forced when the cache is absent or stale.

        Side-effects:
        - Logs a prominent warning if ``isUpdateRequired`` is True.
        - Shows an error notification and returns empty dict if ``isAppBlocked``
          is True (caller should bail out of its API work immediately).

        :return: Appconfig payload dict, or empty dict on failure.
        :rtype: dict
        """
        raw_cached = AddonSettings.get_setting(APPCONFIG_CACHE_KEY, store=LOCAL) or ""
        if raw_cached:
            try:
                cached = json.loads(raw_cached)
                age = time.time() - cached.get("_fetched_at", 0)
                if age < APPCONFIG_CACHE_TTL:
                    return cached
            except (ValueError, TypeError):
                pass

        raw = UriHandler.open(API_V7_APPCONFIG, additional_headers=self.httpHeaders)
        if not raw:
            Logger.warning("NLZIET: Could not fetch appconfig")
            return {}

        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            Logger.warning("NLZIET: Could not parse appconfig")
            return {}

        data["_fetched_at"] = time.time()
        AddonSettings.set_setting(APPCONFIG_CACHE_KEY, json.dumps(data), store=LOCAL)

        if data.get("isUpdateRequired"):
            Logger.warning(
                "NLZIET: *** APP DEPRECATION WARNING — isUpdateRequired=True *** "
                "The NLZIET API client may need to be updated. "
                "Update text: %s", data.get("updateText", ""))

        return data

    def __check_app_blocked(self, appconfig: dict) -> bool:
        """Check the appconfig ``isAppBlocked`` flag and notify the user if set.

        :param dict appconfig: Appconfig payload from ``__load_appconfig()``.
        :return: True if the app is blocked (caller should abort API work).
        :rtype: bool
        """
        if not appconfig.get("isAppBlocked"):
            return False

        reason = appconfig.get("appBlockedReason") or \
            LanguageHelper.get_localized_string(LanguageHelper.ConnectionError)
        Logger.error("NLZIET: App is blocked by server: %s", reason)
        XbmcWrapper.show_notification("NLZIET", reason, XbmcWrapper.Error, display_time=8000)
        return True

    @staticmethod
    def __signal_iptv_manager(delay_seconds: int) -> None:
        """Write a signal file so retroservice.py can trigger IPTV Manager refresh.

        ``Addon.refresh()`` in service.iptv.manager overwrites ``last_refreshed``
        *after* ``create_iptv_epg`` returns, so we cannot write to IPTV Manager
        settings from here.  Instead we write a plain file containing the Unix
        timestamp at which the next refresh should fire.  retroservice.py checks
        this file every 30s and writes ``last_refreshed = "0"`` once the time
        arrives — i.e. after ``Addon.refresh()`` has already finished.

        :param int delay_seconds: Desired gap before the next call (30 – 600).
        """
        import os
        import xbmcvfs
        try:
            addon_data = xbmcvfs.translatePath(
                "special://profile/addon_data/plugin.video.retrospect/")
            signal_path = os.path.join(addon_data, EPG_SIGNAL_FILE_NAME)
            with open(signal_path, "w") as fh:
                fh.write(str(time.time() + delay_seconds))
        except Exception:  # NOSONAR — best-effort IPC
            pass
