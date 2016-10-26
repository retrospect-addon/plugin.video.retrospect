# coding:Cp1252

import mediaitem
import chn_class

from regexer import Regexer
from logger import Logger
from parserdata import ParserData
from streams.m3u8 import M3u8
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper
from helpers.datehelper import DateHelper


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
        if self.channelCode == "sporza":
            self.noImage = "sporzaimage.png"
            self.mainListUri = "http://sporza.be/cm/sporza/videozone"
            self.baseUrl = "http://sporza.be"
        else:
            raise IndexError("Invalid Channel Code")

        # elif self.channelCode == "ketnet":
        #     self.noImage = "ketnetimage.png"
        #     self.mainListUri = "http://video.ketnet.be/cm/ketnet/ketnet-mediaplayer"
        #     self.baseUrl = "http://video.ketnet.be"
        #
        # elif self.channelCode == "cobra":
        #     self.noImage = "cobraimage.png"
        #     self.mainListUri = "http://www.cobra.be/cm/cobra/cobra-mediaplayer"
        #     self.baseUrl = "http://www.cobra.be"

        # setup the urls
        self.swfUrl = "%s/html/flash/common/player.5.10.swf" % (self.baseUrl,)

        # setup the main parsing data
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            preprocessor=self.AddLiveChannel,
                            parser='<li[^>]*>\W*<a href="(/cm/[^"]+/videozone/programmas/[^"]+)" title="([^"]+)"\W*>',
                            creator=self.CreateEpisodeItem)

        # extract the right section, although it is hard to determine the actual one
        self._AddDataParser("*", preprocessor=self.ExtractVideoSection)

        # the main video of the page
        regex = Regexer.FromExpresso('<img[^>]+src="(?<thumburl>[^"]+)"[^>]*>[\w\W]{0,700}<p>(?<description>[^<]+)</p>[\w\W]{0,500}?<a href="(?<url>/cm/[^/]+/videozone/[^?"]+)" >(?<title>[^<]+)</a>')
        self._AddDataParser("*", parser=regex, creator=self.CreateVideoItem)
        # other videos in the side bar
        regex = Regexer.FromExpresso('<a[^>]*href="(?<url>[^"]+)"[^>]*class="videolink"[^>]*>\W*<span[^>]*>(?<title>[^"]+)</span>\W*(?:<span[^>]*>(?<desciption>[^"]+)</span>\W*)?<span[^>]*>\W*<img[^>]*src="(?<thumburl>[^"]+)"')
        self._AddDataParser("*", parser=regex, creator=self.CreateVideoItem,
                            updater=self.UpdateVideoItem)

        # live streams
        self._AddDataParser("http://sporza.be/cm/sporza/matchcenter/mc_livestream",
                            creator=self.CreateLiveChannel,
                            parser='data-video-title="([^"]+)"\W+data-video-iphone-server="([^"]+)"\W+[\w\W]{0,1000}data-video-sitestat-pubdate="(\d+)"[\w\W]{0,2000}data-video-geoblocking="(\w+)"[^>]+>\W*<img[^>]*src="([^"]+)"')
        self._AddDataParser("http://live.stream.vrt.be", updater=self.UpdateLiveItem)

        self.mediaUrlRegex = 'data-video-((?:src|rtmp|iphone|mobile)[^=]*)="([^"]+)"\W+(?:data-video-[^"]+path="([^"]+)){0,1}'

        # self.pageNavigationRegex = '<a href="([^"]+\?page=\d+)"[^>]+>(\d+)'
        # self.pageNavigationRegexIndex = 1

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddLiveChannel(self, data):
        # Only get the first bit
        items = []

        item = mediaitem.MediaItem("\a.: Live :.", "http://sporza.be/cm/sporza/matchcenter/mc_livestream")
        item.type = "folder"
        item.dontGroup = True
        item.complete = False
        items.append(item)
        return data, items

    def CreateLiveChannel(self, resultSet):
        Logger.Trace(resultSet)

        item = mediaitem.MediaItem(resultSet[0], resultSet[1])
        item.type = "video"
        item.isGeoLocked = resultSet[3].lower() == "true"

        dateTime = DateHelper.GetDateFromPosix(int(resultSet[2]) * 1 / 1000)
        item.SetDate(dateTime.year, dateTime.month, dateTime.day, dateTime.hour, dateTime.minute,
                     dateTime.second)

        thumb = resultSet[4]
        if not thumb.startswith("http"):
            thumb = "%s%s" % (self.baseUrl, thumb)
        item.thumb = thumb

        return item

    def CreateEpisodeItem(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        url = "%s%s" % (self.baseUrl, resultSet[0])
        name = resultSet[1]

        item = mediaitem.MediaItem(name.capitalize(), url)
        item.icon = self.icon
        item.type = "folder"
        item.complete = True
        return item

    def ExtractVideoSection(self, data):
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
        data = data[0:data.find('<div class="splitter split24">')]
        # data = data[0:data.find('<ul class="videoarticle-socialsharing">')]
        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateVideoItem(self, resultSet):
        """Creates a MediaItem of type 'video' using the resultSet from the regex.

        Arguments:
        resultSet : tuple (string) - the resultSet of the self.videoItemRegex

        Returns:
        A new MediaItem of type 'video' or 'audio' (despite the method's name)

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.UpdateVideoItem method is called if the item is focused or selected
        for playback.

        """

        Logger.Trace(resultSet)

        url = "%s%s" % (self.baseUrl, resultSet["url"])
        if self.parentItem.url not in url:
            return None

        name = resultSet["title"]
        desc = resultSet.get("description", "")
        thumb = resultSet["thumburl"]

        if thumb and not thumb.startswith("http://"):
            thumb = "%s%s" % (self.baseUrl, thumb)

        item = mediaitem.MediaItem(name, url)
        item.thumb = thumb
        item.description = desc
        item.icon = self.icon
        item.type = 'video'
        item.complete = False

        try:
            nameParts = name.rsplit("/", 3)
            # possibleDateParts = thumb.split("/")
            if len(nameParts) == 3:
                Logger.Debug("Found possible date in name: %s", nameParts)
                year = nameParts[2]
                if len(year) == 2:
                    year = 2000 + int(year)
                month = nameParts[1]
                day = nameParts[0].rsplit(" ", 1)[1]
                Logger.Trace("%s - %s - %s", year, month, day)
                item.SetDate(year, month, day)

            # elif len(possibleDateParts[3]) == 4 and len(possibleDateParts[4]) == 2:
            #     Logger.Debug("Found possible date in name: %s - %s - %s",
            #                  possibleDateParts[3], possibleDateParts[4], possibleDateParts[5])
            #
            #     year = int(possibleDateParts[3])
            #     month = int(possibleDateParts[4])
            #     if len(possibleDateParts[5]) == 2:
            #         day = int(possibleDateParts[5])
            #     else:
            #         day = 1
            #     Logger.Trace("%s - %s - %s", year, month, day)
            #     item.SetDate(year, month, day)
        except:
            Logger.Warning("Apparently it was not a date :)")
        return item

    def UpdateLiveItem(self, item):
        # http://services.vrt.be/videoplayer/r/live.json?_1466364209811=
        channelData = UriHandler.Open("http://services.vrt.be/videoplayer/r/live.json", proxy=self.proxy)
        channelData = JsonHelper(channelData)
        url = None
        for channelId in channelData.json:
            if channelId not in item.url:
                continue
            else:
                url = channelData.json[channelId].get("hls")

        if url is None:
            Logger.Error("Could not find stream for live channel: %s", item.url)
            return item

        Logger.Debug("Found stream url for %s: %s", item, url)
        part = item.CreateNewEmptyMediaPart()
        for s, b in M3u8.GetStreamsFromM3u8(url, self.proxy):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)
        return item

    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        # noinspection PyStatementEffect
        """
        data-video-id="1613274"
        data-video-type="video"
        data-video-src="http://media.vrtnieuws.net/2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-title="Het journaal 1 - 25/04/13"
        data-video-rtmp-server="rtmp://vrt.flash.streampower.be/vrtnieuws"
        data-video-rtmp-path="2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-rtmpt-server="rtmpt://vrt.flash.streampower.be/vrtnieuws"
        data-video-rtmpt-path="2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-iphone-server="http://iphone.streampower.be/vrtnieuws_nogeo/_definst_"
        data-video-iphone-path="2013/04/135132051ONL1304255866693.urlMP4_H.264.m4v"
        data-video-mobile-server="rtsp://mp4.streampower.be/vrt/vrt_mobile/vrtnieuws_nogeo"
        data-video-mobile-path="2013/04/135132051ONL1304255866693.url3GP_MPEG4.3gp"
        data-video-sitestat-program="het_journaal_1_-_250413_id_1-1613274"
        """

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.Open(item.url, proxy=self.proxy)

        # descriptions = Regexer.DoRegex('<div class="longdesc"><p>([^<]+)</', data)
        # Logger.Trace(descriptions)
        # for desc in descriptions:
        #     item.description = desc

        data = data.replace("\\/", "/")
        urls = Regexer.DoRegex(self.mediaUrlRegex, data)
        part = item.CreateNewEmptyMediaPart()
        for url in urls:
            Logger.Trace(url)
            if url[0] == "src":
                flv = url[1]
                bitrate = 750
            else:
                flvServer = url[1]
                flvPath = url[2]

                if url[0] == "rtmp-server":
                    flv = "%s//%s" % (flvServer, flvPath)
                    bitrate = 750

                elif url[0] == "rtmpt-server":
                    continue
                    #flv = "%s//%s" % (flvServer, flvPath)
                    #flv = self.GetVerifiableVideoUrl(flv)
                    #bitrate = 1500

                elif url[0] == "iphone-server":
                    flv = "%s/%s" % (flvServer, flvPath)
                    if not flv.endswith("playlist.m3u8"):
                        flv = "%s/playlist.m3u8" % (flv,)

                    for s, b in M3u8.GetStreamsFromM3u8(flv, self.proxy):
                        item.complete = True
                        part.AppendMediaStream(s, b)
                    # no need to continue adding the streams
                    continue

                elif url[0] == "mobile-server":
                    flv = "%s/%s" % (flvServer, flvPath)
                    bitrate = 250

                else:
                    flv = "%s/%s" % (flvServer, flvPath)
                    bitrate = 0

            part.AppendMediaStream(flv, bitrate)

        item.complete = True
        return item
