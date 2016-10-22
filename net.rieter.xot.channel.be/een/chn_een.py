# coding:UTF-8
#===============================================================================
# Import the default modules
#===============================================================================

#===============================================================================
# Make global object available
#===============================================================================
import mediaitem
import chn_class

from regexer import Regexer
from logger import Logger
from streams.m3u8 import M3u8
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper


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
        self.noImage = "eenimage.png"

        # setup the urls
        self.mainListUri = "https://www.een.be/programmas"
        self.baseUrl = "http://www.een.be"

        # setup the main parsing data
        self._AddDataParser(self.mainListUri, preprocessor=self.ExtractJson, json=True,
                            parser=("data", ), creator=self.CreateShowItem)

        videoParser = '<a class="card-teaser"[^>][^>]*href="(?<url>[^"]+)"[^>]*>\W+<div[^>]+' \
                      'style="background-image: url\(\'(?<thumburl>[^\']+/(?<year>\d{4})/' \
                      '(?<month>\d{2})/(?<day>\d{2})/[^\']+)\'[^>]*>\W+<div[^>]+_play[\w\W+]' \
                      '{0,2000}?<div[^>]*>(?<_title>[^>]*)</div>\W*<h3[^>]*>(?<title>[^<]+)' \
                      '</h3>\W+<div[^>]*>\W+(?:<span[^>]*>[^<]*</span>)?(?<description>[^<]+)'
        videoParser = Regexer.FromExpresso(videoParser)
        self._AddDataParser("*", name="Links to teasers of videos (Card teaser)",
                            # preprocessor=self.CropData,
                            parser=videoParser, creator=self.CreateVideoItem,
                            updater=self.UpdateVideoItem)

        videoParser = '<a[^>]*class="[^"]+-teaser"[^>]*background-image: url\(\'(?<thumburl>' \
                      '[^\']+/(?<year>\d{4})/(?<month>\d{2})/(?<day>\d{2})/[^\']+)\'[^>]*href="' \
                      '(?<url>[^"]+)"[^>]*>\W+<div[^>]+_play[\w\W+]{0,2000}?<div[^>]*>' \
                      '(?<_title>[^>]*)</div>\W*<h3[^>]*>(?<title>[^<]+)</h3>\W+<div[^>]*>\W+' \
                      '(?:<span[^>]*>[^<]*</span>)?(?<description>[^<]+)'
        videoParser = Regexer.FromExpresso(videoParser)
        self._AddDataParser("*", name="Links to teasers of videos (Image Teaser)",
                            # preprocessor=self.CropData,
                            parser=videoParser, creator=self.CreateVideoItem,
                            updater=self.UpdateVideoItem)

        singleVideoParser = '>(?<title>[^<]+)</h1>[\w\W]{0,2000}?(?:<h2>?<description>[^<]+)?' \
                            '[\w\W]{0,1000}?data-video="(?<url>[^"]+)"[\w\W]{0,500}data-analytics' \
                            '=\'{&quot;date&quot;:&quot;(?<year>\d+)-(?<month>\d+)-(?<day>\d+)'
        singleVideoParser = Regexer.FromExpresso(singleVideoParser)
        self._AddDataParser("*", name="Pages that contain only a single video",
                            parser=singleVideoParser, creator=self.CreateVideoItem)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def ExtractJson(self, data):
        """ Extracts JSON data from pages

        @param data: the HTML data
        @return: the JSON part only

        """

        items = []
        recent = mediaitem.MediaItem("\a .: Recent :.", "https://www.een.be/deze-week")
        recent.type = "folder"
        recent.complete = True
        recent.dontGroup = True
        items.append(recent)

        data = Regexer.DoRegex('epgAZ\W+({"data"[\w\W]+?);<', data)[0]
        return data, items

    def CropData(self, data):
        """ Removes unwanted HTML data

        @param data: the HTML data
        @return: the JSON part only

        """

        items = []
        data = data[0: data.find('<div class="section section--12">')]
        return data, items

    def CreateVideoItem(self, resultSet):
        if not resultSet["url"].startswith("http"):
            resultSet["url"] = "https://mediazone.vrt.be/api/v1/een/assets/%(url)s" % resultSet

        item = chn_class.Channel.CreateVideoItem(self, resultSet)
        item.fanart = self.parentItem.fanart
        if "year" in resultSet and resultSet["year"]:
            item.SetDate(resultSet["year"], resultSet["month"], resultSet["day"])
        return item

    def CreateShowItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item. 
        """

        Logger.Trace(resultSet)

        exclude = {
            11: "Dagelijkse Kost",
            388: "Het journaal",
            400: "Karakters",
            413: "Het weer"
        }
        if resultSet["id"] in exclude.keys():
            return None

        # # dummy class
        # url = "http://www.een.be/mediatheek/tag/%s"
        item = mediaitem.MediaItem(resultSet["title"], resultSet["url"])
        item.icon = self.icon
        item.type = "folder"
        item.complete = True

        if "image" in resultSet and "data" in resultSet["image"]:
            item.thumb = resultSet["image"]["data"]["url"]
            item.fanart = resultSet["image"]["data"]["url"]
        return item

    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL 
        and the Thumb! It should return a completed item. 
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        # rtmpt://vrt.flash.streampower.be/een//2011/07/1000_110723_getipt_neefs_wiels_Website_EEN.flv
        # http://www.een.be/sites/een.be/modules/custom/vrt_video/player/player_4.3.swf

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.Open(item.url, proxy=self.proxy)

        part = item.CreateNewEmptyMediaPart()
        if "mediazone.vrt.be" not in item.url:
            # Extract actual media data
            videoId = Regexer.DoRegex('data-video=[\'"]([^"\']+)[\'"]', data)[0]
            # if videoId.startswith("http"):
            #     Logger.Info("Found direct stream. Not processing any further.")
            #     part.AppendMediaStream(videoId, 0)
            #     item.complete = True
            #     return item

            url = "https://mediazone.vrt.be/api/v1/een/assets/%s" % (videoId, )
            data = UriHandler.Open(url, proxy=self.proxy)

        json = JsonHelper(data)
        urls = json.GetValue("targetUrls")
        for urlInfo in urls:
            Logger.Trace(urlInfo)
            if urlInfo["type"].lower() != "hls":
                continue

            hlsUrl = urlInfo["url"]
            for s, b in M3u8.GetStreamsFromM3u8(hlsUrl, self.proxy):
                part.AppendMediaStream(s, b)

        # urls = Regexer.DoRegex(self.mediaUrlRegex, data)
        # Logger.Trace(urls)
        # part = item.CreateNewEmptyMediaPart()
        # for url in urls:
        #     if not url[1] == "":
        #         mediaurl = "%s//%s" % (url[0], url[1])  # the extra slash in the url causes the application name in the RTMP stream to be "een" instead of "een/2011"
        #     else:
        #         mediaurl = url[0]
        #
        #     mediaurl = mediaurl.replace(" ", "%20")
        #
        #     if "rtmp" in mediaurl:
        #         mediaurl = self.GetVerifiableVideoUrl(mediaurl)
        #         # In some cases the RTMPT does not work. Let's just try the RTMP first and then add the original if the RTMP version fails.
        #         part.AppendMediaStream(mediaurl.replace("rtmpt://", "rtmp://"), 650)
        #     elif "rtsp" in mediaurl:
        #         part.AppendMediaStream(mediaurl, 600)
        #     elif mediaurl.startswith("http") and "m3u8" in mediaurl:
        #         # http://iphone.streampower.be/een_nogeo/_definst_/2013/08/1000_130830_placetobe_marjolein_Website_Een_M4V.m4v/playlist.m3u8
        #         mediaurl = mediaurl.rstrip()
        #         for s, b in M3u8.GetStreamsFromM3u8(mediaurl, self.proxy):
        #             part.AppendMediaStream(s, b)
        #     else:
        #         Logger.Warning("Media url was not recognised: %s", mediaurl)

        item.complete = True
        return item
