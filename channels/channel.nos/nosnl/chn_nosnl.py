# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.streams.mpd import Mpd
from resources.lib.chn_class import PreProcessorResult
from typing import Dict
from typing import List

from resources.lib import chn_class, mediatype, contenttype
from resources.lib.chn_class import CreatorResult
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.regexer import Regexer
from resources.lib.streams.m3u8 import M3u8
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    __build_version: str

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.__build_version = ""

        self.noImage = "nosnlimage.png"

        # setup the urls
        self.mainListUri = "https://nos.nl/"

        self._add_data_parser(self.mainListUri, match_type="Exact",
                              preprocessor=self.add_live,
                              parser=r"<li>\W*<a[^>]+(nieuws|sport|live)[^>]+href=\"(/[^\"]+)\"[^>]*>([^<]+)",
                              creator=self.create_category_item)

        self._add_data_parser("https://nos.nl/_next/data/", json=True,
                              parser=["pageProps", "items"], creator=self.create_video_item)

        self._add_data_parser("https://nos.nl/api/live-livestreams", json=True,
                              parser=[], creator=self.create_live_stream_item)

        self._add_data_parser("https://nos.nl/video/",
                              updater=self.update_video_item)
        self._add_data_parser("https://resolver.streaming.api.nos.nl/stream?stream",
                              updater=self.update_resolved_stream)

    # noinspection PyPropertyDefinition
    @property
    def build_version(self) -> str:
        if not self.__build_version:
            data = UriHandler.open("https://nos.nl/")
            try:
                build_version = Regexer.do_regex(r"<script src=\"[^\"]+/([^/]+)/_buildManifest.js\"", data)[0]
            except:
                Logger.error(data)
                raise
            Logger.info(f"Found build version: {build_version}")
            self.__build_version = build_version

        return self.__build_version

    def add_live(self, data: str) -> PreProcessorResult:
        url = "https://nos.nl/api/live-livestreams"
        live_data = UriHandler.open(url, no_cache=True)
        live_json = JsonHelper(live_data)
        if not live_json.json:
            Logger.info("No live streams available for NOS.nl")
            return data, []

        name = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamsTitleId)
        live_item = MediaItem(name, url)
        return data, [live_item]

    def create_category_item(self, result_set: List[str]) -> CreatorResult:
        link_type = result_set[0]
        slug = result_set[1]
        name = result_set[2]

        # https://nos.nl/_next/data/SE_PTjV3sJH9fMkxyA0z6/nieuws/laatste/videos.json
        url = f"https://nos.nl/_next/data/{self.build_version}/{slug}/videos.json"

        if link_type == "sport":
            name = f"Sport: {name}"
        elif link_type == "nieuws":
            name = f"Nieuws: {name}"
        else:
            name = f"Live: {name}"

        item = FolderItem(name, url, content_type=contenttype.VIDEOS)
        return item

    def create_live_stream_item(self, result_set: Dict) -> CreatorResult:
        title = result_set["title"]
        desc = result_set["description"]
        online = result_set["isOnline"]

        url = None
        video_format: Dict[str, str]
        for video_format in result_set["formats"]:
            # Finish on Dash, but always return a stream.
            if "dash" in video_format["mimetype"]:
                url = video_format["url"]
                break
            elif "apple" in video_format["mimetype"]:
                url = video_format["url"]

        if not url or not online:
            return None

        item = MediaItem(title, url, media_type=mediatype.VIDEO)
        item.description = desc
        item.isLive = True
        item.isGeoLocked = True

        starts_at = result_set["startAt"]
        date_time = DateHelper.get_date_from_string(starts_at, date_format="%Y-%m-%dT%H:%M:%S%z")
        item.set_date(*date_time[0:6])

        image_infos: List = result_set["indexImage"]["Ratio16x9"]
        image_info: Dict
        fanart = None
        for image_info in image_infos:
            if image_info["width"] >= 1080 and not fanart:
                fanart = image_info["url"]
                continue
        item.set_artwork(thumb=fanart, fanart=fanart)
        return item

    def create_video_item(self, result_set: Dict) -> CreatorResult:
        title = result_set["title"]
        description = result_set["description"]
        video_id = result_set["id"]
        # https://nos.nl/_next/data/SE_PTjV3sJH9fMkxyA0z6/item/2618404-gejuich-in-de-zaal-pvda-en-groenlinks-stemmen-massaal-voor-fusie.json?slug=2618404-gejuich-in-de-zaal-pvda-en-groenlinks-stemmen-massaal-voor-fusie
        url = f"https://nos.nl/video/{video_id}"
        item = MediaItem(title, url, media_type=mediatype.VIDEO)
        item.description = description

        published_at = result_set["publishedAt"]
        date_time = DateHelper.get_date_from_string(published_at, date_format="%Y-%m-%dT%H:%M:%S%z")
        item.set_date(*date_time[0:6])

        image_infos: List = result_set["image"]["imagesByRatio"]["16:9"]
        image_info: Dict
        fanart = None
        for image_info in image_infos:
            if image_info["width"] >= 1080 and not fanart:
                fanart = image_info["url"]
                continue

        item.set_artwork(thumb=fanart, fanart=fanart)
        return item

    def update_resolved_stream(self, item: MediaItem) -> MediaItem:
        """ Updates an existing MediaItem via the NOS stream resolver.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item: %s', item.name)

        content_type, url = UriHandler.header(item.url)
        strm = item.add_stream(url)
        item.url = url

        if "dash" in content_type:
            Mpd.set_input_stream_addon_input(strm)
        else:
            M3u8.set_input_stream_addon_input(strm)

        item.complete = True
        return item

    def update_video_item(self, item: MediaItem) -> MediaItem:
        """ Updates an existing MediaItem with more data.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item: %s', item.name)

        data = UriHandler.open(item.url)
        stream_url = Regexer.do_regex(r"contentUrl\"\W+\"([^\"]+)\"", data)[0]
        item.url = stream_url
        return self.update_resolved_stream(item)
