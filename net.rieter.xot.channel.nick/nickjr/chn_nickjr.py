# coding=utf-8
import chn_class
import mediaitem

from regexer import Regexer
from parserdata import ParserData
from logger import Logger
from helpers.jsonhelper import JsonHelper
from helpers.datehelper import DateHelper
from helpers.languagehelper import LanguageHelper
from urihandler import UriHandler
# from streams.m3u8 import M3u8


class Channel(chn_class.Channel):
    """
    main class from which all channels inherit
    """

    def __init__(self, channelInfo):
        """Initialisation of the class.

        Arguments:
        channelInfo: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        # setup the main parsing data
        self.noImage = "nickjrimage.jpg"
        self.__mgid = "arc:video:nickjr.tv"

        if self.channelCode == 'nickjrnl':
            self.mainListUri = "http://www.nickjr.nl/"
            self.baseUrl = "http://www.nickjr.nl"
            self.__apiKey = "nl_global_Nickjr_web"

        elif self.channelCode == 'nickjrintl':
            self.mainListUri = "http://www.nickjr.tv/"
            self.baseUrl = "http://www.nickjr.tv"
            self.__apiKey = "global_Nickjr_web"

        elif self.channelCode == "nickse":
            self.noImage = "nickelodeonimage.png"
            self.mainListUri = "http://www.nickelodeon.se/"
            self.baseUrl = "http://www.nickelodeon.se"
            self.__apiKey = "sv_SE_Nick_Web"
            self.__mgid = "arc:video:nick.intl"

        else:
            raise NotImplementedError("Unknown channel code")

        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.ExtractJson,
                              parser=[], creator=self.create_episode_item)

        self._add_data_parser("*", json=True,
                              parser=["stream", ],
                              creator=self.CreateVideoItems,
                              updater=self.update_video_item)

        self._add_data_parser("*", json=True,
                              parser=["pagination", ],
                              creator=self.create_page_item)

        self.mediaUrlRegex = '<param name="src" value="([^"]+)" />'    # used for the update_video_item
        self.swfUrl = "http://origin-player.mtvnn.com/g2/g2player_2.1.7.swf"

        #===============================================================================================================
        # Test cases:
        #  NO: Avator -> Other items
        #  SE: Hotel 13 -> Other items
        #  NL: Sam & Cat -> Other items

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def ExtractJson(self, data):
        """Performs pre-process actions for data processing/

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """

        Logger.info("Performing Pre-Processing")
        items = []

        jsonData = Regexer.do_regex('type="application/json">([^<]+)<', data)
        if not jsonData:
            Logger.warning("No JSON data found.")
            return data, items

        json = JsonHelper(jsonData[0])
        result = []
        for key, value in json.json.iteritems():
            result.append(value)
            value["title"] = key

        # set new json and return JsonHelper object
        json.json = result
        return json, items

    def create_episode_item(self, resultSet):
        Logger.trace(resultSet)
        title = resultSet["title"].replace("-", " ").title()

        # http://www.nickjr.nl/data/propertyStreamPage.json?&urlKey=dora&apiKey=nl_global_Nickjr_web&page=1
        url = "%s/data/propertyStreamPage.json?&urlKey=%s&apiKey=%s&page=1" % (self.baseUrl, resultSet["seriesKey"], self.__apiKey)
        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.complete = True
        item.fanart = self.fanart
        item.HttpHeaders = self.httpHeaders
        return item

    def create_page_item(self, resultSet):
        """Creates a MediaItem of type 'page' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(string) - the resultSet of the self.pageNavigationRegex

        Returns:
        A new MediaItem of type 'page'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.trace(resultSet)
        nextPage = resultSet["next"]
        if not nextPage:
            Logger.debug("No more items available")
            return None

        more = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
        url = "%s=%s" % (self.parentItem.url.rsplit("=", 1)[0], nextPage)
        item = mediaitem.MediaItem(more, url)
        item.thumb = self.parentItem.thumb
        item.icon = self.icon
        item.fanart = self.parentItem.fanart
        item.complete = True
        return item

    def CreateVideoItems(self, resultSets):
        items = []
        for resultSet in resultSets.get("items", []):
            if "data" in resultSet and resultSet["data"]:
                item = self.create_video_item(resultSet["data"])
                if item:
                    items.append(item)

        return items

    def create_video_item(self, resultSet):
        """Creates a MediaItem of type 'video' using the resultSet from the regex.

        Arguments:
        resultSet : tuple (string) - the resultSet of the self.videoItemRegex

        Returns:
        A new MediaItem of type 'video' or 'audio' (despite the method's name)

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        """

        Logger.trace(resultSet)

        isSerieTitle = resultSet["seriesTitle"]
        if not isSerieTitle:
            return None

        if resultSet["mediaType"] == "game":
            return None
        elif resultSet["mediaType"] == "episode":
            title = "%(title)s (Episode)" % resultSet
        else:
            title = resultSet["title"]

        videoId = resultSet["id"]
        url = "http://media.mtvnservices.com/pmt/e1/access/index.html?uri=mgid:%s:%s&configtype=edge" \
              % (self.__mgid, videoId, )

        item = mediaitem.MediaItem(title, url)
        item.description = resultSet.get("description", None)
        item.type = "video"
        item.icon = self.icon
        item.fanart = self.fanart
        item.HttpHeaders = self.httpHeaders
        item.complete = False

        if "datePosted" in resultSet:
            date = DateHelper.get_date_from_posix(float(resultSet["datePosted"]["unixOffset"]) / 1000)
            item.set_date(date.year, date.month, date.day, date.hour, date.minute, date.second)

        if "images" in resultSet:
            images = resultSet.get("images", {})
            thumbs = images.get("thumbnail", {})
            item.thumb = thumbs.get("r16-9", self.noImage)

        return item

    def update_video_item(self, item):
        """Updates an existing MediaItem with more data.

        Arguments:
        item : MediaItem - the MediaItem that needs to be updated

        Returns:
        The original item with more data added to it's properties.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        metaData = UriHandler.open(item.url, proxy=self.proxy, referer=self.baseUrl)
        meta = JsonHelper(metaData)
        streamParts = meta.get_value("feed", "items")
        for streamPart in streamParts:
            streamUrl = streamPart["group"]["content"]
            # streamUrl = streamUrl.replace("{device}", "ipad")
            streamUrl = streamUrl.replace("{device}", "html5")
            streamUrl = "%s&format=json" % (streamUrl, )
            streamData = UriHandler.open(streamUrl, proxy=self.proxy)
            stream = JsonHelper(streamData)

            # subUrls = stream.get_value("package", "video", "item", 0, "transcript", 0, "typographic")
            part = item.create_new_empty_media_part()

            # m3u8Url = stream.get_value("package", "video", "item", 0, "rendition", 0, "src")
            # for s, b in M3u8.get_streams_from_m3u8(m3u8Url, self.proxy):
            #     item.complete = True
            #     part.append_media_stream(s, b)

            rtmpDatas = stream.get_value("package", "video", "item", 0, "rendition")
            for rtmpData in rtmpDatas:
                rtmpUrl = rtmpData["src"]
                rtmpUrl = rtmpUrl.replace("rtmpe://", "rtmp://")
                bitrate = rtmpData["bitrate"]
                part.append_media_stream(rtmpUrl, bitrate)

        item.complete = True
        Logger.trace("Media url: %s", item)
        return item
