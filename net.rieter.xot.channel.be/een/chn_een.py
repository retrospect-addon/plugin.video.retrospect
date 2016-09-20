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

        # url's pointing to stream info
        videoParser = 'data-image="(?<thumburl>[^"]+(?<year>\d{4})/(?<month>\d{2})/(?<day>\d{2})/' \
                      '[^"]+)"\W+data-anal[\w\W]{0,500}?data-video="(?<url>[^"]+)"[\w\W+]' \
                      '{0,2000}?<div[^>]*>(?<title>[^>]*)</div>\W*<h3[^>]*>(?<subtitle>[^<]+)' \
                      '</h3>\W+<div[^>]*>\W+<span[^>]*>[^<]*</span>(?<description>[^<]+)'
        videoParser = Regexer.FromExpresso(videoParser)
        self._AddDataParser("*", parser=videoParser, creator=self.CreateVideoItem,
                            updater=self.UpdateVideoItem)

        # urls pointing to HTML with a single video
        folderParser = '<a class="card-teaser"[^>][^>]*href="(?<url>[^"]+)"[^>]*>\W+<div[^>]+' \
                       'style="background-image: url\(\'(?<thumburl>[^\']+/(?<year>\d{4})/' \
                       '(?<month>\d{2})/(?<day>\d{2})/[^\']+)[\w\W+]{0,2000}?<div[^>]*>' \
                       '(?<title>[^>]*)</div>\W*<h3[^>]*>(?<subtitle>[^<]+)</h3>\W+<div[^>]*>' \
                       '\W+(?:<span[^>]*>[^<]*</span>)?(?<description>[^<]+)'
        folderParser = Regexer.FromExpresso(folderParser)
        self._AddDataParser("https://www.een.be/deze-week",
                            parser=videoParser, creator=self.CreateVideoItem)
        self._AddDataParser("https://www.een.be/deze-week",
                            parser=folderParser, creator=self.CreateFolderItem)

        # single video parsers in case a page only contains a single video
        singleVideoParser = '>(?<title>[^<]+)</h1>[\w\W]{0,2000}?(?:<h2>?<description>[^<]+)?' \
                            '[\w\W]{0,1000}?data-video="(?<url>[^"]+)"[\w\W]{0,500}data-analytics' \
                            '=\'{&quot;date&quot;:&quot;(?<year>\d+)-(?<month>\d+)-(?<day>\d+)'
        singleVideoParser = Regexer.FromExpresso(singleVideoParser)
        self._AddDataParser("*", parser=singleVideoParser, creator=self.CreateVideoItem)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:
        #   Laura: year is first 2 digits
        #   Koppen: year is first 2 and last 2

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

    def CreateVideoItem(self, resultSet):
        if not resultSet["url"].startswith("http"):
            resultSet["url"] = "https://mediazone.vrt.be/api/v1/een/assets/%(url)s" % resultSet
        item = chn_class.Channel.CreateVideoItem(self, resultSet)
        item.fanart = self.parentItem.fanart
        if "year" in resultSet and resultSet["year"]:
            item.SetDate(resultSet["year"], resultSet["month"], resultSet["day"])
        return item

    # def PreProcessFolderList(self, data):
    #     """Performs pre-process actions for data processing/
    #
    #     Arguments:
    #     data : string - the retrieve data that was loaded for the current item and URL.
    #
    #     Returns:
    #     A tuple of the data and a list of MediaItems that were generated.
    #
    #
    #     Accepts an data from the ProcessFolderList method, BEFORE the items are
    #     processed. Allows setting of parameters (like title etc) for the channel.
    #     Inside this method the <data> could be changed and additional items can
    #     be created.
    #
    #     The return values should always be instantiated in at least ("", []).
    #
    #     """
    #     return data.replace("&apos", "'"), []

    def CreateShowItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item. 
        """

        Logger.Trace(resultSet)
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

    # def CreatePageItem(self, resultSet):
    #     """Creates a MediaItem of type 'page' using the resultSet from the regex.
    #
    #     Arguments:
    #     resultSet : tuple(string) - the resultSet of the self.pageNavigationRegex
    #
    #     Returns:
    #     A new MediaItem of type 'page'
    #
    #     This method creates a new MediaItem from the Regular Expression
    #     results <resultSet>. The method should be implemented by derived classes
    #     and are specific to the channel.
    #
    #     """
    #
    #     # we need to overwrite the page number, as the Een.be pages are zero-based.
    #     item = chn_class.Channel.CreatePageItem(self, (resultSet[0], ''))
    #     item.name = resultSet[1]
    #
    #     Logger.Trace("Created '%s' for url %s", item.name, item.url)
    #     return item
    #
    # def CreateVideoItemHtml(self, resultSet):
    #     """Creates a MediaItem of type 'video' using the resultSet from the regex.
    #
    #     Arguments:
    #     resultSet : tuple (string) - the resultSet of the self.videoItemRegex
    #
    #     Returns:
    #     A new MediaItem of type 'video' or 'audio' (despite the method's name)
    #
    #     This method creates a new MediaItem from the Regular Expression
    #     results <resultSet>. The method should be implemented by derived classes
    #     and are specific to the channel.
    #
    #     If the item is completely processed an no further data needs to be fetched
    #     the self.complete property should be set to True. If not set to True, the
    #     self.UpdateVideoItem method is called if the item is focused or selected
    #     for playback.
    #
    #     """
    #
    #     #http://www.een.be/mediatheek/ajax/video/531837
    #     url = "%sajax/video/%s" % (resultSet[0], resultSet[1])
    #     item = mediaitem.MediaItem(resultSet[3], urlparse.urljoin(self.baseUrl, url))
    #     item.thumb = resultSet[2]
    #     item.icon = self.icon
    #
    #     dateRegex = Regexer.DoRegex("/(?:20(\d{2})_[^/]+|[^\/]+)/[^/]*_(\d{2})(\d{2})(\d{2})[_.]", item.thumb)
    #     if len(dateRegex) == 1:
    #         dateRegex = dateRegex[0]
    #
    #         # figure out if the year is the first part
    #         year = dateRegex[0]
    #         if dateRegex[1] == year or year == "":
    #             # The year was in the path, so use that one. OR the year was not in the
    #             # path and we assume that the first part is the year
    #             item.SetDate(2000 + int(dateRegex[1]), dateRegex[2], dateRegex[3])
    #         else:
    #             # the year was in the path and tells us the first part is the day.
    #             item.SetDate(2000 + int(dateRegex[3]), dateRegex[2], dateRegex[1])
    #     item.type = 'video'
    #     item.complete = False
    #     return item

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
        if "mediazone.vrt.be" not in item.url:
            # Extract actual media data
            videoId = Regexer.DoRegex('data-video=[\'"]([^"\']+)[\'"]', data)
            url = "https://mediazone.vrt.be/api/v1/een/assets/%s" % (videoId[0], )
            data = UriHandler.Open(url, proxy=self.proxy)

        json = JsonHelper(data)
        urls = json.GetValue("targetUrls")
        part = item.CreateNewEmptyMediaPart()
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
