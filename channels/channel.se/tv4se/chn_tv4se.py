# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later
from random import randrange
from typing import Optional, Union, List, Tuple

import pytz
import datetime

from resources.lib import chn_class, mediatype, contenttype
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.encodinghelper import EncodingHelper
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.helpers.jsonhelper import JsonHelper

from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.streams.mpd import Mpd
from resources.lib.webdialogue import WebDialogue
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler
from resources.lib.helpers.subtitlehelper import SubtitleHelper


class Channel(chn_class.Channel):

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.__max_page_size = 500
        self.__access_token = None

        if self.channelCode == "tv4segroup":
            self.noImage = "tv4image.png"
            self.httpHeaders = {"Content-Type": "application/json", "Client-Name": "tv4-web",
                                "Client-Version": "4.0.0"}
        else:
            raise Exception("Invalid channel code")

        self._add_data_parser("https://client-gateway.tv4.a2d.tv/graphql?operationName=PageList&",
                              name="Main TV4 pages", json=True, requires_logon=True,
                              parser=["data", "pageList", "content"],
                              creator=self.create_api_typed_item)

        self.mainListUri = "#mainlist"
        self._add_data_parser(
            "#mainlist", name="Main TV4 page", json=True, preprocessor=self.list_main_content)

        self._add_data_parser(
            "https://client-gateway.tv4.a2d.tv/graphql?operationName=Page&",
            name="Main TV4 pages", json=True, requires_logon=True,
            parser=["data", "page", "content", "panels"],
            creator=self.create_api_typed_item)

        self._add_data_parser(
            "https://client-gateway.tv4.a2d.tv/graphql?operationName=MediaIndex&",
            name="Main show/movie list", json=True,
            preprocessor=self.fetch_mainlist_pages,
            parser=["data", "mediaIndex", "contentList", "items"],
            creator=self.create_api_typed_item)

        self._add_data_parser(
            "https://client-gateway.tv4.a2d.tv/graphql?operationName=ContentDetailsPage&",
            name="Seasons for show", json=True, requires_logon=True,
            parser=["data", "media", "allSeasonLinks"], creator=self.create_api_typed_item,
            postprocessor=self.check_for_seasons)

        self._add_data_parser(
            "https://client-gateway.tv4.a2d.tv/graphql?operationName=Panel&",
            name="Panel results", json=True, requires_logon=True,
            parser=["data", "panel", "content", "items"],
            creator=self.create_api_typed_item)

        self._add_data_parser(
            "https://client-gateway.tv4.a2d.tv/graphql?operationName=SeasonEpisodes&",
            name="Episodes for a season", json=True, requires_logon=True,
            parser=["data", "season", "episodes", "items"],
            creator=self.create_api_typed_item)

        self._add_data_parser("*", updater=self.update_video_item, requires_logon=True)

        # ===============================================================================================================
        # non standard items
        self.__timezone = pytz.timezone("Europe/Stockholm")
        self.__refresh_token_setting_id = "refresh_token"

        # ===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def fetch_token(self) -> Optional[str]:
        wd = WebDialogue()
        token, cancelled = wd.input(
            LanguageHelper.SetRefreshToken, LanguageHelper.PasteRefreshToken, time_out=120)

        if not token or cancelled:
            return None

        split_data = token.split(".")
        if len(split_data) != 3:
            AddonSettings.set_channel_setting(
                self, self.__refresh_token_setting_id, "", store=LOCAL)
            XbmcWrapper.show_notification(
                LanguageHelper.InvalidRefreshToken, LanguageHelper.InvalidRefreshToken)
            # Retry
            return self.fetch_token()

        header, payload, signature = split_data
        payload_data = EncodingHelper.decode_base64(payload + '=' * (-len(payload) % 4))
        payload = JsonHelper(payload_data)
        expires_at = payload.get_value("exp")
        expire_date = DateHelper.get_date_from_posix(float(expires_at), tz=pytz.UTC)
        if expire_date < datetime.datetime.now(tz=pytz.UTC).astimezone(tz=pytz.UTC):
            Logger.info("Found expired TV4Play token (valid until: %s)", expire_date)
            AddonSettings.set_channel_setting(
                self, self.__refresh_token_setting_id, "", store=LOCAL)
            XbmcWrapper.show_notification(
                LanguageHelper.InvalidRefreshToken, LanguageHelper.ExpireRefreshToken)
            # Retry
            return self.fetch_token()

        # (Re)Store the valid token.
        Logger.info("Found existing valid TV4Play token (valid until: %s)", expire_date)
        AddonSettings.set_channel_setting(self, self.__refresh_token_setting_id, token, store=LOCAL)
        return token

    # No logon for now
    def log_on(self) -> bool:
        """ Makes sure that we are logged on. """

        if self.__access_token:
            return True

        # Fetch an existing token
        token: str = AddonSettings.get_channel_setting(
            self, self.__refresh_token_setting_id, store=LOCAL)
        if not token:
            token = self.fetch_token()

        if not token:
            return False

        url = "https://avod-auth-alb.a2d.tv/oauth/refresh"
        result = UriHandler.open(
            url, json={"refresh_token": token, "client_id": "tv4-web"}, no_cache=True)
        result = JsonHelper(result)
        self.__access_token = result.get_value("access_token", fallback=None)

        # Update headers for future calls
        self.httpHeaders.update({
            "Authorization": f"Bearer {self.__access_token}"
        })

        # Also update headers for the current parent item
        if self.parentItem:
            self.parentItem.HttpHeaders.update(self.httpHeaders)
        return bool(self.__access_token)

    def list_main_content(self, data: str) -> Tuple[str, List[MediaItem]]:
        items: List[MediaItem] = []

        def __create_item(lang_id: int, url: str):
            name = LanguageHelper.get_localized_string(lang_id)
            item = FolderItem(name, url, content_type=contenttype.VIDEOS)
            item.dontGroup = True
            return item

        main_list_url = self.__get_api_url(
            "MediaIndex",
            "423ba183684c9ea464c94e200696c8f6ec190fe9837f542a672623fa87ef0f4e",
            {"input": {"letterFilters": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                       "limit": self.__max_page_size + randrange(25) * 0,
                       "offset": 0}
             }
        )
        items.append(__create_item(LanguageHelper.TvShows, main_list_url))

        recent_url = self.__get_api_url(
            "Panel", "3ef650feea500555e560903fee7fc06f8276d046ea880c5540282a5341b65985",
            {"panelId": "1pDPvWRfhEg0wa5SvlP28N", "limit": self.__max_page_size, "offset": 0}
        )
        items.append(__create_item(LanguageHelper.Recent, recent_url))

        popular_url = self.__get_api_url(
            "Panel", "3ef650feea500555e560903fee7fc06f8276d046ea880c5540282a5341b65985",
            {"panelId": "3QnNaigt4Szgkyz8yMU9oF", "limit": self.__max_page_size, "offset": 0}
        )
        items.append(__create_item(LanguageHelper.Popular, popular_url))

        latest_news_url = self.__get_api_url(
            "Panel", "3ef650feea500555e560903fee7fc06f8276d046ea880c5540282a5341b65985",
            {"panelId": "5Rqb0w0SN16A6YHt5Mx8BU", "limit": self.__max_page_size, "offset": 0}
        )
        items.append(__create_item(LanguageHelper.LatestNews, latest_news_url))

        # Categories
        # PageList
        # variables: {"pageListId":"categories"}
        # extensions: {"persistedQuery":{"version":1,"sha256Hash":"58da321b8e31df2b746f1d1f374151a450a4c24bda6415182fe81551c90e7d25"}}
        category_url = self.__get_api_url(
            "PageList", "58da321b8e31df2b746f1d1f374151a450a4c24bda6415182fe81551c90e7d25",
            {"pageListId": "categories"})
        items.append(__create_item(LanguageHelper.Categories, category_url))
        return data, items

    def fetch_mainlist_pages(self, data: str) -> Tuple[str, List[MediaItem]]:
        items = []
        data = JsonHelper(data)
        page_data = data

        while True:
            next_offset = page_data.get_value("data", "mediaIndex", "contentList", "pageInfo",
                                              "nextPageOffset")
            if not next_offset or next_offset <= 0:
                break

            url = self.__get_api_url(
                "MediaIndex",
                "423ba183684c9ea464c94e200696c8f6ec190fe9837f542a672623fa87ef0f4e",
                {"input": {"letterFilters": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                           "limit": self.__max_page_size + randrange(25) * 0,
                           "offset": next_offset}
                 }
            )
            page_data = UriHandler.open(url, additional_headers=self.httpHeaders)
            page_data = JsonHelper(page_data)
            data_items = page_data.get_value(*self.currentParser.Parser)
            list_items = data.get_value(*self.currentParser.Parser)
            list_items += data_items

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_api_typed_item(self, result_set):
        """ Creates a new MediaItem based on the __typename attribute.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        api_type = result_set["__typename"]

        if api_type == "Series":
            item = self.create_api_series(result_set)
        elif api_type == "MediaPanelSeriesItem":
            item = self.create_api_series(result_set["series"])
        elif api_type == "MediaIndexSeriesItem":
            item = self.create_api_typed_item(result_set["series"])

        elif api_type == "Clip":
            item = self.create_api_clip(result_set)
        elif api_type == "ClipsPanelItem":
            item = self.create_api_typed_item(result_set["clip"])

        elif api_type == "Episode":
            item = self.create_api_episode(result_set)

        elif api_type == "Movie":
            item = self.create_api_movie(result_set)
        elif api_type == "MediaPanelMovieItem":
            item = self.create_api_movie(result_set["movie"])
        elif api_type == "MediaIndexMovieItem":
            item = self.create_api_typed_item(result_set["movie"])

        elif api_type == "SeasonLink":
            item = self.create_api_season(result_set)
        elif api_type == "PageReferenceItem":
            item = self.create_api_page_ref(result_set)
        elif api_type == "StaticPageItem":
            item = self.create_api_static_page(result_set)

        elif api_type == "MediaPanel" or api_type == "ClipsPanel":
            item = self.create_api_panel(result_set)

        else:
            Logger.warning("Missing type: %s", api_type)
            return None

        return item

    def create_api_movie(self, result_set: dict) -> Optional[MediaItem]:
        video_id: str = result_set["id"]
        url = self.__get_video_url(video_id)
        title = result_set["title"]
        if not title:
            return None

        item = MediaItem(title, url, media_type=mediatype.MOVIE)
        item.isGeoLocked = True
        item = self.__update_base_typed_item(item, result_set)
        return item

    def create_api_clip(self, result_set: dict) -> Optional[MediaItem]:
        clip_id = result_set["id"]
        url = self.__get_video_url(clip_id)
        title = result_set["title"]
        if not title:
            return None

        item = MediaItem(title, url, media_type=mediatype.VIDEO)
        item = self.__update_base_typed_item(item, result_set)
        item.isPaid = not JsonHelper.get_from(
            result_set, "clipVideo", "access", "hasAccess", fallback=True)
        item.isLive = result_set.get("isLiveContent", False)

        duration = JsonHelper.get_from(result_set, "clipVideo", "duration", "seconds", fallback=0)
        if duration:
            item.set_info_label(MediaItem.LabelDuration, duration)
        return item

    def create_api_episode(self, result_set: dict) -> Optional[MediaItem]:
        video_id: str = result_set["id"]
        url = self.__get_video_url(video_id)
        title = result_set["title"]
        if not title:
            return None

        item = MediaItem(title, url, media_type=mediatype.MOVIE)
        item = self.__update_base_typed_item(item, result_set)
        item.isGeoLocked = True
        item.isPaid = not JsonHelper.get_from(
            result_set, "video", "access", "hasAccess", fallback=True)
        item.isLive = result_set.get("isLiveContent", False)
        item.description = result_set.get("synopsis", {}).get("medium", "")

        duration = JsonHelper.get_from(result_set, "video", "duration", "seconds", fallback=0)
        if duration:
            item.set_info_label(MediaItem.LabelDuration, duration)

        # Playable from
        if "playableFrom" in result_set:
            from_date = result_set["playableFrom"]["isoString"]
            # isoString=2022-07-27T22:01:00.000Z
            time_stamp = DateHelper.get_date_from_string(from_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            item.set_date(*time_stamp[0:6])

        # Playable to
        if "playableUntil" in result_set:
            until_data = result_set["playableUntil"]["humanDateTime"]
            expires = "[COLOR gold]{}: {}[/COLOR]".format(MediaItem.ExpiresAt, until_data)
            item.description = f"{expires}\n\n{item.description}"
        return item

    def create_api_series(self, result_set: dict) -> Optional[MediaItem]:
        series_id = result_set["id"]
        url = self.__get_api_url(
            "ContentDetailsPage",
            "fb3501e05a23d910fc9c636467df8578cb69d80abc0225062d8a86e77041225a", {
                "mediaId": series_id, "panelsInput": {"offset": 0, "limit": 20}
            })
        title = result_set["title"]
        if not title:
            return None

        item = FolderItem(title, url, content_type=contenttype.EPISODES,
                          media_type=mediatype.TVSHOW)
        item = self.__update_base_typed_item(item, result_set)
        item.HttpHeaders.update({"feature_flag_enable_season_upsell_on_cdp": "true"})
        item.isPaid = result_set.get("upsell") is not None
        return item

    def create_api_season(self, result_set: dict) -> Optional[MediaItem]:
        title = result_set["title"]
        season_id = result_set["seasonId"]
        url = self.__get_api_url(
            "SeasonEpisodes", "9f069a1ce297d68a0b4a3d108142919fb6d12827f35fc71b03976a251e239796",
            {"seasonId": season_id, "input": {"limit": 100, "offset": 0}})
        item = FolderItem(title, url, content_type=contenttype.EPISODES,
                          media_type=mediatype.FOLDER)
        item.metaData["seasonId"] = result_set["seasonId"]
        return item

    def create_api_page_ref(self, result_set: dict) -> Optional[MediaItem]:
        result_set = result_set["pageReference"]
        title = result_set["title"]
        page_id = result_set["id"]

        # Link goes to a page
        url = self.__get_api_url(
            "Page", "a30fb04a7dbabeaf3b08f66134c6ac1f1e4980de1f21024fa755d752608e6ad9",
            {"pageId": page_id, "input": {"limit": 100, "offset": 0}}
        )
        item = FolderItem(title, url, content_type=contenttype.TVSHOWS, media_type=mediatype.FOLDER)
        self.__set_art(item, result_set.get("images"))
        return item

    def create_api_panel(self, result_set: dict) -> Optional[MediaItem]:
        panel_id = result_set["id"]
        title = result_set["title"]
        url = self.__get_api_url(
            "Panel", "3ef650feea500555e560903fee7fc06f8276d046ea880c5540282a5341b65985", {
                "panelId": panel_id, "limit": self.__max_page_size, "offset": 0}
        )
        item = FolderItem(title, url, content_type=contenttype.TVSHOWS)
        return item

    def create_api_static_page(self, result_set: dict) -> Optional[MediaItem]:
        result_set = result_set["staticPage"]
        page_id = result_set["id"]
        if page_id != "alphabetical":
            return None

        title = result_set["title"]
        url = self.__get_api_url(
            "MediaIndex",
            "dba092c9af0e54e4e3e68dd84b16bb913a9e0e5fe83ff01cf59b6b453d0c75d4",
            {"input": {"letterFilters": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                       "limit": self.__max_page_size + randrange(25) * 0,
                       "offset": 0}})
        item = FolderItem(title, url, content_type=contenttype.VIDEOS, media_type=mediatype.FOLDER)
        self.__set_art(item, result_set.get("images"))
        return item

    # noinspection PyUnusedLocal
    def check_for_seasons(self, data: JsonHelper, items: List[MediaItem]) -> List[MediaItem]:
        # If not seasons, or just one, fetch the episodes
        if len(items) != 1:
            return items

        # Retry with just this url.
        season_id = items[0].metaData["seasonId"]
        url = self.__get_api_url("SeasonEpisodes",
                                 "9f069a1ce297d68a0b4a3d108142919fb6d12827f35fc71b03976a251e239796",
                                 {
                                     "seasonId": season_id, "input": {"limit": 100, "offset": 0}
                                 })
        self.parentItem.url = url
        return self.process_folder_list(self.parentItem)

    def __update_base_typed_item(
            self, item: Union[MediaItem, FolderItem], result_set: dict) -> Union[
        MediaItem, FolderItem]:

        self.__set_art(item, result_set.get("images"))
        return item

    def __get_video_url(self, program_id: str):
        # https://playback2.a2d.tv/play/8d1eb26ad728c9125de8?service=tv4play&device=browser&protocol=hls%2Cdash&drm=widevine&browser=GoogleChrome&capabilities=live-drm-adstitch-2%2Cyospace3
        url = "https://playback2.a2d.tv/play/{}?service=tv4play" \
              "&device=browser&browser=GoogleChrome" \
              "&protocol=hls%2Cdash" \
              "&drm=widevine" \
              "&capabilities=live-drm-adstitch-2%2Cexpired_assets". \
            format(program_id)
        return url

    def __set_art(self, item: MediaItem, art_info: Optional[dict]):
        if not art_info:
            return

        for k, v in art_info.items():
            if isinstance(v, str) or not v:
                continue

            encoded_url = v.get("sourceEncoded")
            if not encoded_url:
                continue

            url = HtmlEntityHelper.url_decode(encoded_url)
            if k == "cover2x3" or k == "image2x3":
                item.set_artwork(poster=url)
            elif k == "main16x9Annotated":
                item.set_artwork(thumb=url, fanart=url)
            elif k == "main16x9" or k == "image16x9":
                # Only thumbs should be set (not fanart)
                item.set_artwork(thumb=url)
            elif k == "image4x3":
                item.set_artwork(thumb=url)
            elif k == "logo":
                pass
            else:
                Logger.warning("Unknown image format: %s", k)

    def search_site(self, url=None):
        """ Creates a list of items by searching the site.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with an URL encoded representation of the
        text to search for.

        :param str|None url:     Url to use to search with a %s for the search parameters.

        :return: A list with search results as MediaItems.
        :rtype: list[MediaItem]

        """

        # url = self.__get_api_query(
        #     '{programSearch(q:"",perPage:100){totalHits,programs%s}}' % self.__program_fields)
        # url = url.replace("%", "%%")
        # url = url.replace("%%22%%22", "%%22%s%%22")
        return chn_class.Channel.search_site(self, url)

    def update_video_item(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaSteam then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        # noinspection PyStatementEffect
        """
                C:\temp\rtmpdump-2.3>rtmpdump.exe -z -o test.flv -n "cp70051.edgefcs.net" -a "tv
                4ondemand" -y "mp4:/mp4root/2010-06-02/pid2780626_1019976_T3MP48_.mp4?token=c3Rh
                cnRfdGltZT0yMDEwMDcyNjE2NDYyNiZlbmRfdGltZT0yMDEwMDcyNjE2NDgyNiZkaWdlc3Q9ZjFjN2U1
                NTRiY2U5ODMxMDMwYWQxZWEwNzNhZmUxNjI=" -l 2

                C:\temp\rtmpdump-2.3>rtmpdump.exe -z -o test.flv -r rtmpe://cp70051.edgefcs.net/
                tv4ondemand/mp4root/2010-06-02/pid2780626_1019976_T3MP48_.mp4?token=c3RhcnRfdGlt
                ZT0yMDEwMDcyNjE2NDYyNiZlbmRfdGltZT0yMDEwMDcyNjE2NDgyNiZkaWdlc3Q9ZjFjN2U1NTRiY2U5
                ODMxMDMwYWQxZWEwNzNhZmUxNjI=
                """

        # retrieve the mediaurl
        # needs an "x-jwt: Bearer"  header.
        token = self.__access_token
        headers = {
            "x-jwt": "Bearer {}".format(token)
        }
        data = UriHandler.open(item.url, additional_headers=headers)
        stream_info = JsonHelper(data)
        stream_url = stream_info.get_value("playbackItem", "manifestUrl")
        if stream_url is None:
            return item

        if ".mpd" in stream_url:
            return self.__update_dash_video(item, stream_info)

        subtitle = M3u8.get_subtitle(stream_url)
        stream = item.add_stream(stream_url, 0)
        M3u8.set_input_stream_addon_input(stream)
        item.complete = True

        if subtitle:
            subtitle = subtitle.replace(".m3u8", ".webvtt")
            item.subtitle = SubtitleHelper.download_subtitle(subtitle, format="m3u8srt")
        return item

    def update_live_item(self, item):
        """ Updates an existing MediaItem for a live stream with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaSteam then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_live_item for %s (%s)', item.name, self.channelName)

        item.streams = []
        for s, b in M3u8.get_streams_from_m3u8(item.url):
            item.add_stream(s, b)

        item.complete = True
        return item

    def __get_api_url(self, operation, hash_value, variables=None):  # NOSONAR
        """ Generates a GraphQL url

        :param str operation:   The operation to use
        :param str hash_value:  The hash of the Query
        :param dict variables:  Any variables to pass

        :return: A GraphQL string
        :rtype: str

        """

        extensions = {"persistedQuery": {"version": 1, "sha256Hash": hash_value}}
        extensions = HtmlEntityHelper.url_encode(JsonHelper.dump(extensions, pretty_print=False))

        final_vars = {"order_by": "NAME", "per_page": 1000}
        if variables:
            final_vars = variables
        final_vars = HtmlEntityHelper.url_encode(JsonHelper.dump(final_vars, pretty_print=False))

        url = "https://client-gateway.tv4.a2d.tv/graphql?" \
              "operationName={}&" \
              "variables={}&" \
              "extensions={}".format(operation, final_vars, extensions)
        return url

    def __get_api_query(self, query):
        return "https://graphql.tv4play.se/graphql?query={}".format(
            HtmlEntityHelper.url_encode(query))

    # def __get_api_folder_url(self, folder_id, offset=0):
    #     return self.__get_api_query(
    #         '{videoPanel(id: "%s"){name,videoList(limit: %s, offset:%d, '
    #         'sortOrder: "broadcastDateTime"){totalHits,videoAssets'
    #         '{title,id,description,season,episode,daysLeftInService,broadcastDateTime,image,'
    #         'freemium,drmProtected,live,duration}}}}' % (folder_id, self.__maxPageSize, offset))

    def __update_dash_video(self, item, stream_info):
        """

        :param MediaItem item:          The item that was updated
        :param JsonHelper stream_info:  The stream info
        """

        if not AddonSettings.use_adaptive_stream_add_on(with_encryption=True):
            XbmcWrapper.show_dialog(
                LanguageHelper.get_localized_string(LanguageHelper.DrmTitle),
                LanguageHelper.get_localized_string(LanguageHelper.WidevineLeiaRequired))
            return item

        playback_item = stream_info.get_value("playbackItem")

        stream_url = playback_item["manifestUrl"]
        stream = item.add_stream(stream_url, 0)

        license_info = playback_item.get("license", None)
        if license_info is not None:
            license_key_token = license_info["token"]
            auth_token = license_info["castlabsToken"]
            header = {
                "x-dt-auth-token": auth_token,
                "content-type": "application/octstream"
            }
            license_url = license_info["castlabsServer"]
            license_key = Mpd.get_license_key(
                license_url, key_value=license_key_token, key_headers=header)

            Mpd.set_input_stream_addon_input(
                stream, license_key=license_key)
            item.isDrmProtected = False
        else:
            Mpd.set_input_stream_addon_input(stream)

        item.complete = True
        return item
