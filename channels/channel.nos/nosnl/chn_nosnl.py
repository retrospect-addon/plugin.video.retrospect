# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Dict
from typing import List

from resources.lib import chn_class, mediatype, contenttype
from resources.lib.chn_class import CreatorResult
from resources.lib.helpers.datehelper import DateHelper
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
                              parser=r"<li>\W*<a[^>]+(?:nieuws|sport)[^>]+href=\"(/[^\"]+)\"[^>]*>([^<]+)",
                              creator=self.create_category_item)

        self._add_data_parser("https://nos.nl/_next/data/", json=True,
                              parser=["pageProps", "items"], creator=self.create_video_item)

        self._add_data_parser("https://nos.nl/video/", updater=self.update_video_item)

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

    def create_category_item(self, result_set: List[str]) -> CreatorResult:
        name = result_set[1]
        # https://nos.nl/_next/data/SE_PTjV3sJH9fMkxyA0z6/nieuws/laatste/videos.json
        url = f"https://nos.nl/_next/data/{self.build_version}/{result_set[0]}/videos.json"
        if "sport" in url:
            name = f"Sport: {name}"
        elif "nieuws" in url:
            name = f"Nieuws: {name}"

        item = FolderItem(name, url, content_type=contenttype.VIDEOS)
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

        _, url = UriHandler.header(item.url)
        item.complete = M3u8.update_part_with_m3u8_streams(item, url, bitrate=0)
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
