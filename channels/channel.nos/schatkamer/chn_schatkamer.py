# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Tuple
from resources.lib.helpers.jsonhelper import JsonHelper
from typing import Optional
from urllib.parse import urlparse
from urllib.parse import parse_qs

from resources.lib.helpers.datehelper import DateHelper
from resources.lib.streams.m3u8 import M3u8
from resources.lib.parserdata import ParserData
from resources.lib import mediatype
from resources.lib.helpers.reactrsc import NextJsParser, RSCHelper
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
                              preprocessor=self.main_list_preprocessor)

        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              parser=["carousel"],
                              creator=self.create_swimlane_item)

        self._add_data_parser("https://schatkamer.beeldengeluid.nl/verhaal/",
                              preprocessor=NextJsParser(key="modules", return_parent=True), json=True,
                              parser=["modules"], creator=self.create_swimlane_item)

        self._add_data_parser("https://schatkamer.beeldengeluid.nl/serie/",
                              preprocessor=NextJsParser(key="results", skip=1), json=True,
                              parser=[], creator=self.create_video_item)

        self._add_data_parser("https://schatkamer.beeldengeluid.nl/verhaal/.+",
                              updater=self.update_video_item, match_type=ParserData.MatchRegex)
        self._add_data_parser("https://schatkamer.beeldengeluid.nl/serie/.+/aflevering",
                              updater=self.update_video_item, match_type=ParserData.MatchRegex)
        self._add_data_parser("https://schatkamer.beeldengeluid.nl/programma/",
                              updater=self.update_video_item)

    def main_list_preprocessor(self, data: str) -> Tuple[JsonHelper, List[MediaItem]]:
        rsc = RSCHelper(data)
        helper = JsonHelper(rsc.convert_to_json())

        results = []
        result_data = {"carousel": []}
        for carousel_id in ["module-stories-carousel-0", "module-stories-carousel-3", "module-stories-carousel-6"]:
            item_data = helper.find_dict_by_key_value("id", carousel_id)
            if item_data:
                result_data["carousel"].append(item_data)

        for program_id in ["module-program-carousel-1", "module-program-carousel-4", "module-program-carousel-7"]:
            item_data = helper.find_dict_by_key_value("id", program_id)
            if item_data:
                result_data["carousel"].append(item_data)

        for serie_id in ["module-serie-carousel-5", "module-serie-carousel-8", "module-serie-carousel-10"]:
            item_data = helper.find_dict_by_key_value("id", serie_id)
            if item_data:
                result_data["carousel"].append(item_data)

        result = JsonHelper("[]")
        result.json = result_data
        return result, results

    def create_swimlane_item(self, result_set: Dict) -> Union[MediaItem, List[MediaItem], None]:
        if result_set["type"] not in ("swimlane",):
            return None

        title = result_set["title"].title()
        parent = FolderItem(title, "", content_type=contenttype.EPISODES)

        if "items" not in result_set:
            return parent

        for result in result_set["items"]:
            if "/verhaal/" in result["url"]:
                item = self.create_serie_item(result)
            elif "/aflevering/" in result["url"] or "/programma/" in result["url"]:
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
