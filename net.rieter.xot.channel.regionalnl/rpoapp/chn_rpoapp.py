import mediaitem
import chn_class
from addonsettings import AddonSettings
from helpers.datehelper import DateHelper
from helpers.languagehelper import LanguageHelper
from parserdata import ParserData
from logger import Logger
from helpers.jsonhelper import JsonHelper
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
        self.jsonParsing = False

        if self.channelCode == "omroepzeeland":
            self.noImage = "omroepzeelandimage.png"
            self.mainListUri = "https://www.omroepzeeland.nl/tvgemist"
            self.baseUrl = "https://www.omroepzeeland.nl"
            self.liveUrl = "https://zeeland.rpoapp.nl/v01/livestreams/AndroidTablet.json"

        elif self.channelCode == "rtvutrecht":
            self.noImage = "rtvutrechtimage.png"
            self.mainListUri = "https://www.rtvutrecht.nl/gemist/rtvutrecht/"
            self.baseUrl = "https://www.rtvutrecht.nl"
            # Uses NPO stream with smshield cookie
            self.liveUrl = "https://utrecht.rpoapp.nl/v02/livestreams/AndroidTablet.json"

        else:
            raise NotImplementedError("Channelcode '%s' not implemented" % (self.channelCode, ))

        # JSON Based Main lists
        self._add_data_parser("https://www.omroepzeeland.nl/tvgemist",
                              preprocessor=self.AddLiveChannelAndExtractData,
                              match_type=ParserData.MatchExact,
                              parser=[], creator=self.CreateJsonEpisodeItem,
                              json=True)

        # HTML Based Main lists
        htmlEpisodeRegex = '<option\s+value="(?<url>/gemist/uitzending/[^"]+)">(?<title>[^<]*)'
        htmlEpisodeRegex = Regexer.from_expresso(htmlEpisodeRegex)
        self._add_data_parser("https://www.rtvutrecht.nl/gemist/rtvutrecht/",
                              preprocessor=self.AddLiveChannelAndExtractData,
                              match_type=ParserData.MatchExact,
                              parser=htmlEpisodeRegex, creator=self.create_episode_item,
                              json=False)

        videoItemRegex = '<img src="(?<thumburl>[^"]+)"[^>]+alt="(?<title>[^"]+)"[^>]*/>\W*</a>\W*<figcaption(?:[^>]+>\W*){2}<time[^>]+datetime="(?<date>[^"]+)[^>]*>(?:[^>]+>\W*){3}<a[^>]+href="(?<url>[^"]+)"[^>]*>\W*(?:[^>]+>\W*){3}<a[^>]+>(?<description>.+?)</a>'
        videoItemRegex = Regexer.from_expresso(videoItemRegex)
        self._add_data_parser("https://www.rtvutrecht.nl/",
                              name="HTML Video parsers and updater for JWPlayer embedded JSON",
                              parser=videoItemRegex, creator=self.create_video_item,
                              updater=self.UpdateVideoItemJsonPlayer)

        # Json based stuff
        self._add_data_parser("https://www.omroepzeeland.nl/RadioTv/Results?",
                              name="Video item parser", json=True,
                              parser=["searchResults", ], creator=self.CreateJsonVideoItem)

        self._add_data_parser("https://www.omroepzeeland.nl/",
                              name="Updater for Javascript file based stream data",
                              updater=self.UpdateVideoItemJavascript)

        # Live Stuff
        self._add_data_parser(self.liveUrl, name="Live Stream Creator",
                              creator=self.CreateLiveItem, parser=[], json=True)

        self._add_data_parser(".+/live/.+", match_type=ParserData.MatchRegex,
                              updater=self.UpdateLiveItem)
        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:
        #   Omroep Zeeland: M3u8 playist

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddLiveChannelAndExtractData(self, data):
        Logger.info("Performing Pre-Processing")
        items = []

        title = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
        item = mediaitem.MediaItem("\a.: {} :.".format(title), self.liveUrl)
        item.type = "folder"
        items.append(item)

        if not data:
            return "[]", items

        jsonData = Regexer.do_regex("setupBroadcastArchive\('Tv',\s*([^;]+)\);", data)
        if isinstance(jsonData, (tuple, list)) and len(jsonData) > 0:
            Logger.debug("Pre-Processing finished")
            return jsonData[0], items

        Logger.info("Cannot extract JSON data from HTML.")
        return data, items

    def CreateLiveItem(self, result):
        url = result["stream"]["highQualityUrl"]
        title = result["title"] or result["id"].title()
        item = mediaitem.MediaItem(title, url)
        item.type = "video"
        item.isLive = True

        if item.url.endswith(".mp3"):
            item.append_single_stream(item.url)
            item.complete = True
            return item

        return item

    def CreateJsonEpisodeItem(self, result):
        Logger.trace(result)
        url = "{}/RadioTv/Results?medium=Tv&query=&category={}&from=&to=&page=1".format(self.baseUrl, result["seriesId"])
        title = result["title"]
        item = mediaitem.MediaItem(title, url)
        item.type = "folder"
        item.complete = False
        return item

    def create_video_item(self, resultSet):
        item = chn_class.Channel.create_video_item(self, resultSet)
        if item is None:
            return None

        # 2018-02-24 07:15:00
        timeStamp = DateHelper.get_date_from_string(resultSet['date'], date_format="%Y-%m-%d %H:%M:%S")
        item.set_date(*timeStamp[0:6])
        return item

    def CreateJsonVideoItem(self, result):
        Logger.trace(result)
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
                month = DateHelper.get_month_from_name(dateParts[1], language="nl", short=True)
                year = int(dateParts[2])
                hours, minutes = dateParts[3].split(":")
                hours = int(hours)
                minutes = int(minutes)
                item.set_date(year, month, day, hours, minutes, 0)
            except:
                Logger.warning("Error parsing date %s", result["publicationTimeString"], exc_info=True)

        item.complete = False
        return item

    def UpdateLiveItem(self, item):
        part = item.create_new_empty_media_part()
        if AddonSettings.use_adaptive_stream_add_on():
            stream = part.append_media_stream(item.url, 0)
            M3u8.set_input_stream_addon_input(stream, self.proxy)
            item.complete = True
        else:
            for s, b in M3u8.get_streams_from_m3u8(item.url, self.proxy):
                item.complete = True
                part.append_media_stream(s, b)
        return item

    def UpdateVideoItemJsonPlayer(self, item):
        data = UriHandler.open(item.url, proxy=self.proxy)
        streams = Regexer.do_regex('label:\s*"([^"]+)",\W*file:\s*"([^"]+)"', data)

        part = item.create_new_empty_media_part()
        bitrates = {"720p SD": 1200}
        for stream in streams:
            part.append_media_stream(stream[1], bitrates.get(stream[0], 0))
            item.complete = True

        return item

    def UpdateVideoItemJavascript(self, item):

        urlParts = item.url.rsplit("/", 3)
        if urlParts[-3] == "aflevering":
            videoId = urlParts[-2]
        else:
            videoId = urlParts[-1]
        Logger.debug("Found videoId '%s' for '%s'", videoId, item.url)

        url = "https://omroepzeeland.bbvms.com/p/regiogrid/q/sourceid_string:{}*.js".format(videoId)
        data = UriHandler.open(url, proxy=self.proxy)

        jsonData = Regexer.do_regex('var opts\s*=\s*({.+});\W*//window', data)
        Logger.debug("Found jsondata with size: %s", len(jsonData[0]))
        jsonData = JsonHelper(jsonData[0])
        clipData = jsonData.get_value("clipData", "assets")
        server = jsonData.get_value("publicationData", "defaultMediaAssetPath")
        part = item.create_new_empty_media_part()
        for clip in clipData:
            part.append_media_stream("{}{}".format(server, clip["src"]), int(clip["bandwidth"]))
            item.complete = True

        return item
