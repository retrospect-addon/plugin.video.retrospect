import chn_class
import mediaitem

from logger import Logger
from regexer import Regexer
from urihandler import UriHandler
from parserdata import ParserData
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.jsonhelper import JsonHelper
from helpers.datehelper import DateHelper
from streams.m3u8 import M3u8


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

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = "rtbfimage.png"

        # setup the urls
        self.mainListUri = "https://www.rtbf.be/auvio/emissions"
        self.baseUrl = "https://www.rtbf.be"
        # self.swfUrl = "http://www.canvas.be/sites/all/libraries/player/PolymediaShowFX16.swf"

        # setup the main parsing data
        episodeRegex = '<article[^>]+data-id="(?<id>(?<url>\d+))"[^>]*>\W+<figure[^>]+>\W+' \
                       '<figcaption[^>]+>(?<title>[^{][^<]+)</figcaption>\W*<div[^>]*>\W*' \
                       '<img[^>]*(?<thumburl>http[^"]+) \d+w"'
        episodeRegex = Regexer.FromExpresso(episodeRegex)
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            preprocessor=self.AddCategoryAndLiveItems,
                            parser=episodeRegex,
                            creator=self.CreateEpisodeItem)

        self._AddDataParser("http://www.rtbf.be/news/api/menu?site=media", json=True,
                            matchType=ParserData.MatchExact,
                            parser=("item", 3, "item"), creator=self.CreateCategory)

        liveRegex = '<img[^>]*(?<thumburl>http[^"]+) \d+w"[^>]*>[\w\W]{0,1000}Maintenant</span> (?:sur )?(?<channel>[^>]+)</div>\W*<h3[^>]*>\W*<a[^>]+href="(?<url>[^"]+=(?<liveId>\d+))"[^>]+title="(?<title>[^"]+)'
        liveRegex = Regexer.FromExpresso(liveRegex)
        self._AddDataParser("https://www.rtbf.be/auvio/direct/",
                            parser=liveRegex,
                            creator=self.CreateVideoItem)

        self._AddDataParser("https://www.rtbf.be/auvio/embed/direct",
                            updater=self.UpdateLiveItem)

        videoRegex = '<img[^>]*(?<thumburl>http[^"]+) \d+w"[^>]*>[\w\W]{0,1000}?<time[^>]+' \
                     'datetime="(?<date>[^"]+)"[\w\W]{0,500}?<h4[^>]+>\W+<a[^>]+href="' \
                     '(?<url>[^<"]+=(?<videoId>\d+))"[^>]*>(?<title>[^<]+)</a>\W+</h4>\W+' \
                     '<h5[^>]+>(?<description>[^<]*)'
        videoRegex = Regexer.FromExpresso(videoRegex)
        self._AddDataParser("*",
                            # preprocessor=self.ExtractVideoSection,
                            parser=videoRegex, creator=self.CreateVideoItem,
                            updater=self.UpdateVideoItem)

        self.pageNavigationRegexIndex = 1
        pageRegex = '<li class="[^a][^"]+">\W+<a class="rtbf-pagination__link" href="([^"]+&p=)(\d+)"'
        self._AddDataParser("*",
                            # preprocessor=self.ExtractVideoSection,
                            parser=pageRegex, creator=self.CreatePageItem)

        self.swfUrl = "http://www.static.rtbf.be/rtbf/embed/js/vendor/jwplayer/jwplayer.flash.swf"
        # ==========================================================================================
        # Test cases:
        # 5@7

        # ====================================== Actual channel setup STOPS here ===================
        return

    def AddCategoryAndLiveItems(self, data):
        """Performs pre-process actions for data processing

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        Accepts an data from the ProcessFolderList method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """

        Logger.Info("Performing Pre-Processing")
        items = []

        subItems = {
            "\a.: Direct :.": "%s/auvio/direct/" % (self.baseUrl, ),
            "\a.: Cat&eacute;gories :.": "http://www.rtbf.be/news/api/menu?site=media"
        }

        for k, v in subItems.iteritems():
            item = mediaitem.MediaItem(k, v)
            item.complete = True
            item.dontGroup = True
            items.append(item)
            item.isLive = v.endswith('/direct/')

        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateEpisodeItem(self, resultSet):
        item = chn_class.Channel.CreateEpisodeItem(self, resultSet)
        if item is None:
            return item

        item.url = "%s/auvio/archives?pid=%s&contentType=complete" % (self.baseUrl, resultSet["id"])
        return item

    def CreateCategory(self, resultSet):
        resultSet = resultSet["@attributes"]
        Logger.Trace(resultSet)
        # http://www.rtbf.be/auvio/archives?caid=29&contentType=complete,extract,bonus
        # {
        # u'url': u'http://www.rtbf.be/auvio/categorie/sport/football?id=11',
        # u'expandorder': u'6', u'aliases': u'football', u'id': u'category-11',
        # u'name': u'Football'
        # }
        cid = resultSet["id"].split("-")[-1]
        url = "%s/auvio/archives?caid=%s&contentType=complete,extract,bonus" % (self.baseUrl, cid)
        item = mediaitem.MediaItem(resultSet["name"], url)
        item.complete = True
        return item
    #
    # def CreateLiveChannelItem(self, resultSet):
    #     item = chn_class.Channel.CreateEpisodeItem(self, resultSet)
    #     if item is None:
    #         return item
    #
    #     item.url = "%s/auvio/archives?pid=%s&contentType=complete" % (self.baseUrl, resultSet["id"])
    #     return item

    def CreatePageItem(self, resultSet):
        item = chn_class.Channel.CreatePageItem(self, resultSet)
        url = "%s/auvio/archives%s%s" % (self.baseUrl, HtmlEntityHelper.UrlDecode(resultSet[0]), resultSet[1])
        item.url = url
        return item

    def CreateVideoItem(self, resultSet):
        item = chn_class.Channel.CreateVideoItem(self, resultSet)
        if item is None:
            return item

        # http://www.rtbf.be/auvio/embed/media?id=2101078&autoplay=1
        if "videoId" in resultSet:
            item.url = "%s/auvio/embed/media?id=%s" % (self.baseUrl, resultSet["videoId"])
        elif "liveId" in resultSet:
            item.name = "%s - %s" % (resultSet["channel"].strip(), item.name)
            item.url = "%s/auvio/embed/direct?id=%s" % (self.baseUrl, resultSet["liveId"])
            item.isLive = True

        if "date" in resultSet:
            # 2016-05-14T20:00:00+02:00 -> strip the hours
            timeStamp = DateHelper.GetDateFromString(resultSet["date"].rsplit("+")[0], "%Y-%m-%dT%H:%M:%S")
            item.SetDate(*timeStamp[0:6])

        return item

    def UpdateVideoItem(self, item):
        data = UriHandler.Open(item.url, proxy=self.proxy, additionalHeaders=item.HttpHeaders)
        mediaRegex = 'data-media="([^"]+)"'
        mediaInfo = Regexer.DoRegex(mediaRegex, data)[0]
        mediaInfo = HtmlEntityHelper.ConvertHTMLEntities(mediaInfo)
        mediaInfo = JsonHelper(mediaInfo)
        Logger.Trace(mediaInfo)

        # sources
        part = item.CreateNewEmptyMediaPart()
        # high, web, mobile, url
        mediaSources = mediaInfo.json.get("sources", {})
        for quality in mediaSources:
            url = mediaSources[quality]
            if quality == "high":
                bitrate = 2000
            elif quality == "web":
                bitrate = 800
            elif quality == "mobile":
                bitrate = 400
            else:
                bitrate = 0
            part.AppendMediaStream(url, bitrate)

        # geoLocRestriction
        item.isGeoLocked = not mediaInfo.GetValue("geoLocRestriction", fallback="world") == "world"
        item.complete = True
        return item

    def UpdateLiveItem(self, item):
        data = UriHandler.Open(item.url, proxy=self.proxy, additionalHeaders=item.HttpHeaders)
        mediaRegex = 'data-media="([^"]+)"'
        mediaInfo = Regexer.DoRegex(mediaRegex, data)[0]
        mediaInfo = HtmlEntityHelper.ConvertHTMLEntities(mediaInfo)
        mediaInfo = JsonHelper(mediaInfo)
        Logger.Trace(mediaInfo)
        part = item.CreateNewEmptyMediaPart()

        hlsUrl = mediaInfo.GetValue("streamUrl")
        if hlsUrl is not None and "m3u8" in hlsUrl:
            Logger.Debug("Found HLS url for %s: %s", mediaInfo.json["streamName"], hlsUrl)
            # from debug.router import Router
            # data = Router.GetVia("be", hlsUrl, proxy=self.proxy)
            for s, b in M3u8.GetStreamsFromM3u8(hlsUrl, self.proxy):
                part.AppendMediaStream(s, b)
                item.complete = True
        else:
            Logger.Debug("No HLS url found for %s. Fetching RTMP Token.", mediaInfo.json["streamName"])
            # fetch the token:
            tokenUrl = "%s/api/media/streaming?streamname=%s" % (self.baseUrl, mediaInfo.json["streamName"])
            tokenData = UriHandler.Open(tokenUrl, proxy=self.proxy, additionalHeaders=item.HttpHeaders, noCache=True)
            tokenData = JsonHelper(tokenData)
            token = tokenData.GetValue("token")
            Logger.Debug("Found token '%s' for '%s'", token, mediaInfo.json["streamName"])

            rtmpUrl = "rtmp://rtmp.rtbf.be/livecast/%s?%s pageUrl=%s tcUrl=rtmp://rtmp.rtbf.be/livecast" % (mediaInfo.json["streamName"], token, self.baseUrl)
            rtmpUrl = self.GetVerifiableVideoUrl(rtmpUrl)
            part.AppendMediaStream(rtmpUrl, 0)
            item.complete = True

        item.isGeoLocked = not mediaInfo.GetValue("geoLocRestriction", fallback="world") == "world"
        return item
