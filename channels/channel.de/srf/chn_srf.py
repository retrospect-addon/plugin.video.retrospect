# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import chn_class, mediatype, contenttype

from resources.lib.mediaitem import MediaItem, FolderItem
from resources.lib.logger import Logger
from resources.lib.urihandler import UriHandler
from resources.lib.parserdata import ParserData
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.helpers.datehelper import DateHelper
from resources.lib.streams.m3u8 import M3u8


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.useAtom = False  # : The atom feeds just do not give all videos
        self.noImage = "srfimage.png"

        # setup the urls
        self.mainListUri = "https://www.srf.ch/play/v3/api/srf/production/shows?onlyActiveShows=true"
        self.baseUrl = "http://www.srf.ch"

        # setup the intial listing
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              parser=["data"], creator=self.create_episode_item)

        # self._add_data_parser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
        #                     preprocessor=self.get_live_items)

        # self._add_data_parser("http://il.srgssr.ch/integrationlayer/1.0/ue/srf/video/play",
        #                       updater=self.update_live_item)

        self._add_data_parser("https://www.srf.ch/play/v3/api/srf/production/videos-by-show-id?showId", json=True,
                              parser=['data', 'data'],
                              creator=self.create_video_item)

        # TODO: folders
        self._add_data_parser("https://il.srgssr.ch/integrationlayer/2.0/mediaComposition/byUrn", updater=self.update_video_item)

        # ===============================================================================================================
        # Test cases:
        #
        # ====================================== Actual channel setup STOPS here =======================================
        return

    def get_live_items(self, data):
        """ Adds live stream items.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Fetching episode items")
        items = []

        live_items = MediaItem("\a.: Live TV :.", "")
        items.append(live_items)

        live_base = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/video/play/%s.json"
        live_channels = {"SRF 1 live": ("c4927fcf-e1a0-0001-7edd-1ef01d441651", "srf1.png"),
                         "SRF zwei live": ("c49c1d64-9f60-0001-1c36-43c288c01a10", "srf2.png"),
                         "SRF info live": ("c49c1d73-2f70-0001-138a-15e0c4ccd3d0", "srfinfo.png")}
        for live_item in live_channels.keys():
            item = MediaItem(live_item, live_base % (live_channels[live_item][0],))
            item.thumb = self.get_image_location(live_channels[live_item][1])
            item.isGeoLocked = True
            item.media_type = mediatype.EPISODE
            live_items.items.append(item)

        return data, items

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        url = "https://www.srf.ch/play/v3/api/srf/production/videos-by-show-id?showId={}".format(result_set["id"])
        item = FolderItem(result_set["title"], url, content_type=contenttype.EPISODES)
        item.description = result_set.get("description", "")
        item.httpHeaders = self.httpHeaders
        item.poster = result_set.get("posterImageUrl")
        item.thumb = result_set.get("imageUrl")
        item.fanart = item.thumb
        item.complete = True
        return item

    def create_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param result_set: The result_set of the self.episodeItemRegex
        :type result_set: dict

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        video_urn = result_set["urn"]
        url = "https://il.srgssr.ch/integrationlayer/2.0/mediaComposition/byUrn/{}.json?onlyChapters=false&vector=portalplay".format(video_urn)
        item = MediaItem(result_set["title"], url)

        item.media_type = mediatype.EPISODE
        item.thumb = result_set.get("imageUrl")
        item.description = result_set.get("description")
        item.isGeoLocked = not result_set.get("playableAbroad", True)

        duration = result_set.get("duration")
        if duration:
            item.set_info_label("duration", int(duration)/1000)

        date_value = str(result_set["date"])
        date_value = date_value.split("+", 1)[0]
        # date=2021-07-01T12:34:50+02:00
        date_time = DateHelper.get_date_from_string(date_value, "%Y-%m-%dT%H:%M:%S")
        item.set_date(*date_time[0:6])
        item.httpHeaders = self.httpHeaders
        item.complete = False
        return item

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

        data = UriHandler.open(item.url, additional_headers=item.HttpHeaders)
        json = JsonHelper(data)
        video_infos = json.get_value("chapterList", 0, "resourceList")

        for video_info in video_infos:
            url = video_info["url"]
            video_type = video_info["protocol"].lower()
            quality = video_info["quality"].lower()
            if quality == "sd":
                bitrate = 1000
            else:
                bitrate = 2500

            if not video_type == "hls":
                Logger.warning("Cannot playback type '%s': %s", video_type, url)

            item.complete = M3u8.update_part_with_m3u8_streams(item, url, bitrate=bitrate, encrypted=False)

        return item
