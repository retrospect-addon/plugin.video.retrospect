import mediaitem
import chn_class

from regexer import Regexer
from logger import Logger
from urihandler import UriHandler
from helpers.htmlentityhelper import HtmlEntityHelper


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

        # setup the urls
        self.swfUrl = "http://media.mtvnservices.com/player/prime/mediaplayerprime.1.12.5.swf"
        if self.channelCode == "southpark.se":
            self.noImage = "southparkimage.png"
            self.mainListUri = "http://www.southparkstudios.se/full-episodes/"
            self.baseUrl = "http://www.southparkstudios.se"
            # self.proxy = proxyinfo.ProxyInfo("94.254.2.120", 80, "http")
            self.promotionId = None
        else:
            self.noImage = "southparkimage.png"
            self.mainListUri = "http://www.southpark.nl/episodes/"
            self.baseUrl = "http://www.southpark.nl"

        # setup the main parsing data
        self.episodeItemRegex = '(?:data-promoId="([^"]+)"|<li[^>]*>\W*<a[^>]+href="([^"]+episodes/season[^"]+)">(\d+)</a>)'  # used for the ParseMainList
        self.videoItemRegex = '(\{[^}]+)'

        # ====================================== Actual channel setup STOPS here =======================================
        return

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

        if not resultSet[0] == "":
            self.promotionId = resultSet[0]
            Logger.Debug("Setting PromotionId to: %s", resultSet[0])
            return None

        # <li><a href="(/guide/season/[^"]+)">(\d+)</a></li>
        # if (self.channelCode == "southpark"):
        #    url = "%s/ajax/seasonepisode/%s" % (self.baseUrl, resultSet[2])
        #    url = http://www.southpark.nl/feeds/full-episode/carousel/14/424b7b57-e459-4c9c-83ca-9b924350e94d
        # else:
        url = "%s/feeds/full-episode/carousel/%s/%s" % (self.baseUrl, resultSet[2], self.promotionId)

        item = mediaitem.MediaItem("Season %02d" % int(resultSet[2]), url)
        item.icon = self.icon
        item.complete = True
        return item

    def CreateVideoItem(self, resultSet):
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
        self.UpdateVideoItem method is called if the item is focussed or selected
        for playback.

        """

        # Logger.Debug(resultSet)

        # data = resultSet.replace('" : "', '":"').replace("\\'", "'")
        # helper = jsonhelper.JsonHelper(data)
        #
        # episodeNumber = helper.GetNamedValue("episodenumber")
        # episodeId = helper.GetNamedValue("id")
        #
        # # http://www.southpark.nl/feeds/video-player/mrss/mgid%3Aarc%3Aepisode%3Asouthpark.nl%3Abcc6a626-c98d-4390-9d7c-1d1233d4df1f?lang={lang}
        # interPart = "feeds/video-player/mrss/mgid%3Aarc%3Aepisode%3Asouthpark.nl%3A"
        # url = "%s/%s%s?lang={lang}" % (self.baseUrl, interPart, episodeId)
        #
        # title = "%s (%s)" % (helper.GetNamedValue("title"), episodeNumber)
        #
        # item = mediaitem.MediaItem(title, url)
        # item.thumb = helper.GetNamedValue("thumbnail_190")
        # item.icon = self.icon
        # item.description = helper.GetNamedValue("description")
        # item.type = 'video'
        # item.complete = False
        #
        # date = helper.GetNamedValue("airdate")
        # Logger.Trace(date)
        # year = int(date[6:8])
        # if year > 80:
        #     year = "19%s" % (year,)
        # else:
        #     year = "20%s" % (year,)
        # day = date[0:2]
        # month = date[3:5]
        # item.SetDate(year, month, day)
        #
        # return item

        # json that comes here, sucks!
        return None

    def UpdateVideoItem(self, item):
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

        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        # 1 - get the overal config file
        guidRegex = 'http://[^:]+/mgid:[^"]+:([0-9a-f-]+)"'
        rtmpRegex = 'type="video/([^"]+)" bitrate="(\d+)">\W+<src>([^<]+)</src>'

        data = UriHandler.Open(item.url, proxy=self.proxy)
        guids = Regexer.DoRegex(guidRegex, data)

        item.MediaItemParts = []
        for guid in guids:
            # get the info for this part
            Logger.Debug("Processing part with GUID: %s", guid)

            # reset stuff
            part = None

            # http://www.southpark.nl/feeds/video-player/mediagen?uri=mgid%3Aarc%3Aepisode%3Acomedycentral.com%3Aeb2a53f7-e370-4049-a6a9-57c195367a92&suppressRegisterBeacon=true
            guid = HtmlEntityHelper.UrlEncode("mgid:arc:episode:comedycentral.com:%s" % (guid,))
            infoUrl = "%s/feeds/video-player/mediagen?uri=%s&suppressRegisterBeacon=true" % (self.baseUrl, guid)

            # 2- Get the GUIDS for the different ACTS
            infoData = UriHandler.Open(infoUrl, proxy=self.proxy)
            rtmpStreams = Regexer.DoRegex(rtmpRegex, infoData)

            for rtmpStream in rtmpStreams:
                # if this is the first stream for the part, create an new part
                if part is None:
                    part = item.CreateNewEmptyMediaPart()

                part.AppendMediaStream(self.GetVerifiableVideoUrl(rtmpStream[2]), rtmpStream[1])

        item.complete = True
        Logger.Trace("Media item updated: %s", item)
        return item
