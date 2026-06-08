# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional
from urllib.parse import urlparse
from urllib.parse import parse_qs

from resources.lib.helpers.datehelper import DateHelper
from resources.lib.streams.m3u8 import M3u8
from resources.lib.parserdata import ParserData
from resources.lib import mediatype
from resources.lib.helpers.reactrsc import NextJsParser
from typing import Dict, Union, List

from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib import chn_class, contenttype
from resources.lib.channelinfo import ChannelInfo
from resources.lib.regexer import Regexer
from resources.lib.urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channel_info: ChannelInfo):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "de-schatkamer-image.jpg"

        self.mainListUri = "https://schatkamer.beeldengeluid.nl/"
        self.baseUrl = "https://schatkamer.beeldengeluid.nl/"

        # We need React Server Components
        self.httpHeaders["rsc"] = "1"

        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              preprocessor=NextJsParser(key="id", value="module-stories-carousel-0"), json=True,
                              parser=["items"],
                              creator=self.create_genre_item)

        self._add_data_parser("https://schatkamer.beeldengeluid.nl/verhaal/",
                              preprocessor=NextJsParser(key="modules", return_parent=True), json=True,
                              parser=["modules"], creator=self.create_swimlane_item)

        self._add_data_parser("https://schatkamer.beeldengeluid.nl/serie/",
                              preprocessor=NextJsParser(key="results", skip=1), json=True,
                              parser=[], creator=self.create_video_item)

        self._add_data_parser("https://schatkamer.beeldengeluid.nl/serie/.+/aflevering",
                              updater=self.update_video_item, match_type=ParserData.MatchRegex)
        self._add_data_parser("https://schatkamer.beeldengeluid.nl/programma/",
                              updater=self.update_video_item)

    def create_genre_item(self, result_set: Dict) -> Union[MediaItem, List[MediaItem], None]:
        title = result_set["title"]
        genre_id = result_set["id"]
        item = FolderItem(title, f"https://schatkamer.beeldengeluid.nl/verhaal/{genre_id}", content_type=contenttype.TVSHOWS)
        item.metaData["slug"] = genre_id

        if "image" in result_set and result_set["image"]:
            item.set_artwork(thumb=result_set["image"]["url"])
        return item

    def create_swimlane_item(self, result_set: Dict) -> Union[MediaItem, List[MediaItem], None]:
        if result_set["type"] not in ("swimlane", ):
            return None

        title = result_set["title"].title()
        parent = FolderItem(title, "", content_type=contenttype.EPISODES)

        if "items" not in result_set:
            return parent

        for result in result_set["items"]:
            if "/aflevering/" in result["url"] or "/programma/" in result["url"]:
                item = self.create_video_item(result)
            else:
                item = self.create_serie_item(result)
            if item:
                parent.items.append(item)
        return parent

    def create_serie_item(self, result_set: Dict) -> Union[MediaItem, None]:
        title = result_set["title"].title()
        url = result_set["url"]

        item = FolderItem(title, url, content_type=contenttype.EPISODES)

        if "image" in result_set and result_set["image"]:
            image = result_set["image"]["url"]
            item.set_artwork(poster=image)

        return item

    # pyrefly: ignore [bad-override]
    def create_video_item(self, result_set: Dict) -> MediaItem:
        title = result_set["title"]
        tvshow = result_set.get("seriesTitle")
        if tvshow:
            tvshow = tvshow.title()
            title = f"{tvshow} - {title}"
        else:
            title = title.title()
        url = result_set["url"]

        item = MediaItem(title, url, tv_show_title=tvshow, media_type=mediatype.EPISODE)
        item.HttpHeaders["rsc"] = "1"

        if "image" in result_set and result_set["image"]:
            image = result_set["image"]["url"]
            item.set_artwork(thumb=image)

        date_info: Optional[str] = result_set.get("date")
        if date_info and "-" in date_info:
            item.set_date(*date_info.split("-"))
        elif date_info and " " in date_info:
            day, month_name, year = date_info.split(" ")
            month = DateHelper.get_month_from_name(month_name, "nl")
            item.set_date(year, month, day)

        return item

    def update_video_item(self, item: MediaItem) -> MediaItem:
        data = UriHandler.open(item.url, additional_headers=item.HttpHeaders, no_cache=True)
        url = Regexer.do_regex(r"(https:\/\/[^,]+\.m3u8[^:]+)\d\d:", data)[0]

        # We need to pass the parameters to both the manifest, stream and update parameter as a cookie.
        url_info = urlparse(url)
        url_parameters = parse_qs(url_info.query)
        url = f"{url_info.scheme}://{url_info.netloc}{url_info.path}"
        cookie_value = ""
        for key in ("CloudFront-Key-Pair-Id", "CloudFront-Policy", "CloudFront-Signature"):
            cookie = url_parameters[key][0]
            if cookie:
                cookie_value = f"{cookie_value};{key}={cookie}"
        cookie_value = cookie_value.strip(";")

        stream = item.add_stream(url, 0)
        M3u8.set_input_stream_addon_input(
            stream,
            manifest_headers={
                "cookie": cookie_value
            },
            stream_headers={
                "cookie": cookie_value
            },
            manifest_upd_params={
                "cookie": cookie_value
            }
        )

        item.complete = True
        return item
