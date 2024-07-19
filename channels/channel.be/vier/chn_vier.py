# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Tuple, List

import pytz

# noinspection PyUnresolvedReferences
from awsidp import AwsIdp
from resources.lib import chn_class, contenttype, mediatype
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem, MediaItemResult, FolderItem
from resources.lib.parserdata import ParserData
from resources.lib.regexer import Regexer
from resources.lib.streams.m3u8 import M3u8
from resources.lib.streams.mpd import Mpd
from resources.lib.urihandler import UriHandler
from resources.lib.vault import Vault
from resources.lib.xbmcwrapper import XbmcWrapper


class NextJsParser:
    def __init__(self, regex: str):
        self.__regex = regex

    def __call__(self, data: str) -> Tuple[JsonHelper, List[MediaItem]]:
        nextjs_regex = self.__regex
        try:
            nextjs_data = Regexer.do_regex(nextjs_regex, data)[0]
        except:
            Logger.debug(f"RAW NextJS: {data}")
            raise

        Logger.trace(f"NextJS: {nextjs_data}")
        nextjs_json = JsonHelper(nextjs_data)
        return nextjs_json, []

    def __str__(self):
        return f"NextJS parser: {self.__regex}"


class Channel(chn_class.Channel):
    """
    main class from resources.lib.which all channels inherit
    """

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # https://www.goplay.be/api/programs/popular/vier
        # https://www.goplay.be/api/epg/vier/2021-01-28

        # https://www.goplay.be/programmas?type=series
        # nextjs parsing from `\"results\":[` tot `,\"categories\":[`
        # https://www.goplay.be/hetisingewikkeld
        # nextjs parsing from `\"playlists\":[`

        # add header `rsc: 1`

        # https://www.goplay.be/tv-gids/vier?_rsc=fe9ep
        # https://www.goplay.be/tv-gids/vier/2024-07-14?_rsc=fe9ep
        # https://www.goplay.be/tv-gids/vijf?_rsc=fe9ep
        # https://www.goplay.be/tv-gids/zes?_rsc=fe9ep
        # https://www.goplay.be/tv-gids/zeven?_rsc=fe9ep
        # https://www.goplay.be/tv-gids/playcrime?_rsc=fe9ep
        # nextjs parsing from `"children":`

        # https://www.goplay.be/programmas?type=series  (&_rsc=fe9ep)
        # https://www.goplay.be/programmas?type=movies  (&_rsc=fe9ep)

        # https://api.goplay.be/web/v1/videos/long-form/ba6a5377-cfbe-4adf-9579-9e4eb7e38547
        # https://www.goplay.be/video/hetisingewikkeld/hetisingewikkeld-s2/hetisingewikkeld-s2-aflevering-2
        # https://pubads.g.doubleclick.net/ondemand/dash/content/2615619/vid/10137607496827527/GRQ/streams/518f68f5-8d43-4cc4-8565-38050183281d/manifest.mpd

        # setup the main parsing data
        self.baseUrl = "https://www.goplay.be"
        self.httpHeaders = {"rsc": "1"}

        if self.channelCode == "vijfbe":
            self.noImage = "vijfimage.png"
            self.mainListUri = "https://www.goplay.be/programmas/play-5"
            self.__channel_brand = "play5"
            self.__channel_slug = "vijf"

        elif self.channelCode == "zesbe":
            self.noImage = "zesimage.png"
            self.mainListUri = "https://www.goplay.be/programmas/play-6"
            self.__channel_brand = "play6"
            self.__channel_slug = "zes"

        elif self.channelCode == "zevenbe":
            self.noImage = "zevenimage.png"
            self.mainListUri = "https://www.goplay.be/programmas/play-7"
            self.__channel_brand = "play7"
            self.__channel_slug = "zeven"

        else:
            self.noImage = "vierimage.png"
            self.mainListUri = "https://www.goplay.be/programmas/play-4"
            self.__channel_brand = "play4"
            self.__channel_slug = "vier"

        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=NextJsParser(r"{\"brand\":\".+?\",\"results\":(.+),\"categories\":"),
                              parser=[],
                              creator=self.create_typed_nextjs_item)

        self._add_data_parser("https://www.goplay.be/", json=True, name="Main show parser",
                              preprocessor=NextJsParser(r"{\"playlists\":(.+)}\]}\]\]$"),
                              parser=[],
                              creator=self.create_season_item)

        self._add_data_parser("https://api.goplay.be/web/v1/videos/long-form/",
                              updater=self.update_video_item_with_id)
        self._add_data_parser("https://www.goplay.be/",
                              updater=self.update_video_item)

        # ==========================================================================================
        # Channel specific stuff
        self.__idToken = None
        self.__tz = pytz.timezone("Europe/Brussels")

        # ==========================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here ===================
        return

    def create_typed_nextjs_item(self, result_set: dict) -> MediaItemResult:
        item_type = result_set["type"]
        item_sub_type = result_set["subtype"]

        if item_type == "program":
            return self.create_program_typed_item(result_set)
        else:
            Logger.warning(f"Unknown type: {item_type}:{item_sub_type}")
        return None

    def create_program_typed_item(self, result_set: dict) -> MediaItemResult:
        item_sub_type = result_set["subtype"]
        data = result_set.get("data")

        if not data:
            return None

        brand = data["brandName"].lower()
        if brand != self.__channel_brand:
            return None

        title = data["title"]
        path = data["path"]
        url = f"{self.baseUrl}{path}"

        if item_sub_type == "movie":
            item = MediaItem(title, url, media_type=mediatype.MOVIE)
            # item.metaData["retrospect:parser"] = "movie"
        else:
            item = FolderItem(title, url, content_type=contenttype.EPISODES)

        if "brandName" in data:
            item.metaData["brand"] = data["brandName"]
        if "categoryName" in data:
            item.metaData["category"] = data["categoryName"]
        if "parentalRating" in data:
            item.metaData["parental"] = data["parentalRating"]

        self.__extract_artwork(item, data.get("images"))
        return item

    def create_season_item(self, result_set):
        videos = []
        season = result_set.get("season", 0)

        video_info: dict
        for video_info in result_set.get("videos", []):
            title = video_info["title"]
            url = f"{self.baseUrl}{video_info['path']}"
            video_date = video_info["dateCreated"]
            description = video_info["description"]
            # video_id = video_info["uuid"]
            episode = video_info.get("episodeNumber", 0)

            item = MediaItem(title, url, media_type=mediatype.EPISODE)
            item.description = description

            self.__extract_artwork(item, video_info.get("images"), set_fanart=False)

            if episode and season:
                item.set_season_info(season, episode)

            date_stamp = DateHelper.get_date_from_posix(int(video_date), tz=self.__tz)
            item.set_date(date_stamp.year, date_stamp.month, date_stamp.day, date_stamp.hour,
                          date_stamp.minute, date_stamp.second)

            stream_collection = video_info.get("streamCollection", {})
            if stream_collection:
                drm_key = stream_collection["drmKey"]
                streams = stream_collection["streams"]
                duration = stream_collection["duration"]
                if duration:
                    item.set_info_label(MediaItem.LabelDuration, duration)
                for stream in streams:
                    proto = stream["protocol"]
                    stream_url = stream["url"]
                    if proto == "dash":
                        stream = item.add_stream(stream_url, 1501)
                        Mpd.set_input_stream_addon_input(stream)
                    elif proto == "hls":
                        stream = item.add_stream(stream_url, 1500)
                        M3u8.set_input_stream_addon_input(stream)

                    if "/geo" in stream_url:
                        item.isGeoLocked = True

            # flags = video_info.get("flags", {})
            # item.isGeoLocked = flags["isProtected"]

            item.complete = item.has_streams()
            videos.append(item)

        return videos

    def update_video_item(self, item: MediaItem) -> MediaItem:
        data = UriHandler.open(item.url, additional_headers=self.httpHeaders)
        list_id = Regexer.do_regex(r"listId\":\"([^\"]+)\"", data)[0]
        item.url = f"https://api.goplay.be/web/v1/videos/long-form/{list_id}"
        return self.update_video_item_with_id(item)

    def log_on(self):
        """ Logs on to a website, using an url.

        First checks if the channel requires log on. If so and it's not already
        logged on, it should handle the log on. That part should be implemented
        by the specific channel.

        More arguments can be passed on, but must be handled by custom code.

        After a successful log on the self.loggedOn property is set to True and
        True is returned.

        :return: indication if the login was successful.
        :rtype: bool

        """

        if self.__idToken:
            return True

        # check if there is a refresh token
        refresh_token = AddonSettings.get_setting("viervijfzes_refresh_token")
        client = AwsIdp("eu-west-1_dViSsKM5Y", "6s1h851s8uplco5h6mqh1jac8m",
                        logger=Logger.instance())
        if refresh_token:
            id_token = client.renew_token(refresh_token)
            if id_token:
                self.__idToken = id_token
                return True
            else:
                Logger.info("Extending token for VierVijfZes failed.")

        username = AddonSettings.get_setting("viervijfzes_username")
        v = Vault()
        password = v.get_setting("viervijfzes_password")
        if not username or not password:
            XbmcWrapper.show_dialog(
                title=None,
                message=LanguageHelper.get_localized_string(LanguageHelper.MissingCredentials),
            )
            return False

        id_token, refresh_token = client.authenticate(username, password)
        if not id_token or not refresh_token:
            Logger.error("Error getting a new token. Wrong password?")
            return False

        self.__idToken = id_token
        AddonSettings.set_setting("viervijfzes_refresh_token", refresh_token)
        return True

    # def add_recent_items(self, data):
    #     """ Performs pre-process actions for data processing.
    #
    #     Accepts an data from the process_folder_list method, BEFORE the items are
    #     processed. Allows setting of parameters (like title etc) for the channel.
    #     Inside this method the <data> could be changed and additional items can
    #     be created.
    #
    #     The return values should always be instantiated in at least ("", []).
    #
    #     :param str data: The retrieve data that was loaded for the current item and URL.
    #
    #     :return: A tuple of the data and a list of MediaItems that were generated.
    #     :rtype: tuple[str|JsonHelper,list[MediaItem]]
    #
    #     """
    #
    #     items = []
    #     today = datetime.datetime.now()
    #     days = LanguageHelper.get_days_list()
    #     for d in range(0, 7, 1):
    #         air_date = today - datetime.timedelta(d)
    #         Logger.trace("Adding item for: %s", air_date)
    #
    #         # Determine a nice display date
    #         day = days[air_date.weekday()]
    #         if d == 0:
    #             day = LanguageHelper.get_localized_string(LanguageHelper.Today)
    #         elif d == 1:
    #             day = LanguageHelper.get_localized_string(LanguageHelper.Yesterday)
    #
    #         title = "%04d-%02d-%02d - %s" % (air_date.year, air_date.month, air_date.day, day)
    #         url = "https://www.goplay.be/api/epg/{}/{:04d}-{:02d}-{:02d}".\
    #             format(self.__channel_slug, air_date.year, air_date.month, air_date.day)
    #
    #         extra = MediaItem(title, url)
    #         extra.complete = True
    #         extra.dontGroup = True
    #         extra.set_date(air_date.year, air_date.month, air_date.day, text="")
    #         extra.content_type = contenttype.VIDEOS
    #         items.append(extra)
    #
    #     return data, items
    #
    # def add_specials(self, data):
    #     """ Performs pre-process actions for data processing.
    #
    #     Accepts an data from the process_folder_list method, BEFORE the items are
    #     processed. Allows setting of parameters (like title etc) for the channel.
    #     Inside this method the <data> could be changed and additional items can
    #     be created.
    #
    #     The return values should always be instantiated in at least ("", []).
    #
    #     :param str data: The retrieve data that was loaded for the current item and URL.
    #
    #     :return: A tuple of the data and a list of MediaItems that were generated.
    #     :rtype: tuple[str|JsonHelper,list[MediaItem]]
    #
    #     """
    #
    #     items = []
    #
    #     specials = {
    #         "https://www.goplay.be/api/programs/popular/{}".format(self.__channel_slug): (
    #             LanguageHelper.get_localized_string(LanguageHelper.Popular),
    #             contenttype.TVSHOWS
    #         ),
    #         "#tvguide": (
    #             LanguageHelper.get_localized_string(LanguageHelper.Recent),
    #             contenttype.FILES
    #         )
    #     }
    #
    #     for url, (title, content) in specials.items():
    #         item = MediaItem("\a.: {} :.".format(title), url)
    #         item.content_type = content
    #         items.append(item)
    #
    #     return data, items

    def update_video_item_with_id(self, item: MediaItem) -> MediaItem:
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

        # We need to log in
        if not self.loggedOn:
            self.log_on()

        # add authorization header
        authentication_header = {
            "authorization": "Bearer {}".format(self.__idToken),
            "content-type": "application/json"
        }

        data = UriHandler.open(item.url, additional_headers=authentication_header)
        json_data = JsonHelper(data)
        m3u8_url = json_data.get_value("manifestUrls", "hls")

        # If there's no m3u8 URL, try to use a SSAI stream instead
        if m3u8_url is None and json_data.get_value("ssai") is not None:
            return self.__get_ssai_streams(item, json_data)

        elif m3u8_url is None and json_data.get_value('message') is not None:
            error_message = json_data.get_value('message')
            if error_message == "Locked":
                # set it for the error statistics
                item.isGeoLocked = True
            Logger.info("No stream manifest found: {}".format(error_message))
            item.complete = False
            return item

        # Geo Locked?
        if "/geo/" in m3u8_url.lower():
            # set it for the error statistics
            item.isGeoLocked = True

        item.complete = M3u8.update_part_with_m3u8_streams(
            item, m3u8_url, channel=self, encrypted=False)

    def __extract_artwork(self, item: MediaItem, images: dict, set_fanart: bool = True):
        if not images:
            return

        if "poster" in images:
            item.poster = images["poster"]
        if "default" in images:
            item.thumb = images["default"]
            if set_fanart:
                item.fanart = images["default"]
        elif "posterLandscape" in images:
            item.thumb = images["posterLandscape"]
            if set_fanart:
                item.fanart = images["posterLandscape"]

    def __get_ssai_streams(self, item, json_data):
        Logger.info("No stream data found, trying SSAI data")
        content_source_id = json_data.get_value("ssai", "contentSourceID")
        video_id = json_data.get_value("ssai", "videoID")

        streams_url = 'https://dai.google.com/ondemand/dash/content/{}/vid/{}/streams'.format(
            content_source_id, video_id)
        streams_input_data = {
            "api-key": "null"
        }
        streams_headers = {
            "content-type": "application/json"
        }
        data = UriHandler.open(streams_url, data=streams_input_data, additional_headers=streams_headers)
        json_data = JsonHelper(data)
        mpd_url = json_data.get_value("stream_manifest")

        stream = item.add_stream(mpd_url, 0)
        Mpd.set_input_stream_addon_input(stream)
        item.complete = True
        return item
