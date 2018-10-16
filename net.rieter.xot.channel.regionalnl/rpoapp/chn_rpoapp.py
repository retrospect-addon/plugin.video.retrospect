import urlparse

import contextmenu
import mediaitem
import chn_class
from addonsettings import AddonSettings
from helpers.datehelper import DateHelper
from helpers.encodinghelper import EncodingHelper
from helpers.languagehelper import LanguageHelper
from parserdata import ParserData
from logger import Logger
from helpers.jsonhelper import JsonHelper
from helpers.htmlhelper import HtmlHelper
from regexer import Regexer
from streams.m3u8 import M3u8
from urihandler import UriHandler


class Channel(chn_class.Channel):
    """
    THIS CHANNEL IS BASED ON THE PEPERZAKEN APPS FOR ANDROID
    """

    def __init__(self, channelInfo):
        """Initialisation of the class.

        Arguments:
        channelInfo: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        self.liveUrl = None        # : the live url if present

        if self.channelCode == "omroepzeeland":
            self.noImage = "omroepzeelandimage.png"
            self.mainListUri = "https://www.omroepzeeland.nl/tvgemist"
            self.baseUrl = "https://www.omroepzeeland.nl"
            self.liveUrl = "https://zeeland.rpoapp.nl/v01/livestreams/AndroidTablet.json"

        elif self.channelCode == "rtvutrecht":
            self.noImage = "rtvutrechtimage.png"
            self.mainListUri = ""
            self.baseUrl = "http://app.rtvutrecht.nl"
            # Uses NPO stream with smshield cookie
            self.liveUrl = "https://utrecht.rpoapp.nl/v02/livestreams/AndroidTablet.json"

        else:
            raise NotImplementedError("Channelcode '%s' not implemented" % (self.channelCode, ))

        # setup the main parsing data
        self._AddDataParser(self.mainListUri, preprocessor=self.AddLiveChannelAndExtractData,
                            matchType=ParserData.MatchExact,
                            parser=(), creator=self.CreateEpisodeItem,
                            json=True)

        self._AddDataParser("https://www.omroepzeeland.nl/RadioTv/Results?",
                            name="Video item parsers", json=True,
                            parser=("searchResults", ), creator=self.CreateVideoItem)

        self._AddDataParser(self.liveUrl, name="Live Stream Creator",
                            creator=self.CreateLiveItem, parser=(), json=True)

        self._AddDataParser(".+/live/.+", matchType=ParserData.MatchRegex,
                            updater=self.UpdateLiveItem)

        self._AddDataParser("*", updater=self.UpdateVideoItem)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:
        #   Omroep Zeeland: M3u8 playist

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddLiveChannelAndExtractData(self, data):
        Logger.Info("Performing Pre-Processing")
        items = []

        title = LanguageHelper.GetLocalizedString(LanguageHelper.LiveStreamTitleId)
        item = mediaitem.MediaItem("\a.: {} :.".format(title), self.liveUrl)
        item.type = "folder"
        items.append(item)

        if not data:
            return "[]", items

        data = Regexer.DoRegex("setupBroadcastArchive\('Tv',\s*([^;]+)\);", data)
        if not isinstance(data, (tuple, list)):
            Logger.Error("Cannot extract JSON data from HTML.")
            return "[]", items

        Logger.Debug("Pre-Processing finished")
        return data[0], items

    def CreateLiveItem(self, result):
        url = result["stream"]["highQualityUrl"]
        title = result["title"] or result["id"].title()
        item = mediaitem.MediaItem(title, url)
        item.type = "video"
        item.isLive = True

        if item.url.endswith(".mp3"):
            item.AppendSingleStream(item.url)
            item.complete = True
            return item

        return item

    def CreateEpisodeItem(self, result):
        Logger.Trace(result)
        url = "{}/RadioTv/Results?medium=Tv&query=&category={}&from=&to=&page=1".format(self.baseUrl, result["seriesId"])
        title = result["title"]
        item = mediaitem.MediaItem(title, url)
        item.type = "folder"
        item.complete = False
        return item

    def CreateVideoItem(self, result):
        Logger.Trace(result)
        url = result["url"]
        if not url.startswith("http"):
            url = "{}{}".format(self.baseUrl, url)

        title = result["title"]
        item = mediaitem.MediaItem(title, url)
        item.description = result.get("synopsis", None)
        item.thumb = result.get("photo", self.noImage)
        item.type = "video"

        if "publicationTimeString" in result:
            try:
                # publicationTimeString=7 jun 2018 17:20 uur
                dateParts = result["publicationTimeString"].split(" ")
                day = int(dateParts[0])
                month = DateHelper.GetMonthFromName(dateParts[1], language="nl", short=True)
                year = int(dateParts[2])
                hours, minutes = dateParts[3].split(":")
                hours = int(hours)
                minutes = int(minutes)
                item.SetDate(year, month, day, hours, minutes, 0)
            except:
                Logger.Warning("Error parsing date %s", result["publicationTimeString"], exc_info=True)

        item.complete = False
        return item

    def UpdateLiveItem(self, item):
        part = item.CreateNewEmptyMediaPart()
        if AddonSettings.UseAdaptiveStreamAddOn():
            stream = part.AppendMediaStream(item.url, 0)
            M3u8.SetInputStreamAddonInput(stream, self.proxy)
            item.complete = True
        else:
            for s, b in M3u8.GetStreamsFromM3u8(item.url, self.proxy):
                item.complete = True
                part.AppendMediaStream(s, b)
        return item

    def UpdateVideoItem(self, item):

        urlParts = item.url.rsplit("/", 3)
        if urlParts[-3] == "aflevering":
            videoId = urlParts[-2]
        else:
            videoId = urlParts[-1]
        Logger.Debug("Found videoId '%s' for '%s'", videoId, item.url)

        url = "https://omroepzeeland.bbvms.com/p/regiogrid/q/sourceid_string:{}*.js".format(videoId)
        data = UriHandler.Open(url, proxy=self.proxy)

        jsonData = Regexer.DoRegex('var opts\s*=\s*({.+});\W*//window', data)
        Logger.Debug("Found jsondata with size: %s", len(jsonData[0]))
        jsonData = JsonHelper(jsonData[0])
        clipData = jsonData.GetValue("clipData", "assets")
        server = jsonData.GetValue("publicationData", "defaultMediaAssetPath")
        part = item.CreateNewEmptyMediaPart()
        for clip in clipData:
            part.AppendMediaStream("{}{}".format(server, clip["src"]), int(clip["bandwidth"]))
            item.complete = True

        return item
