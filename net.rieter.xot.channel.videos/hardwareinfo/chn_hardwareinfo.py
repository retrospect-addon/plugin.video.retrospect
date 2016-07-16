import mediaitem
import chn_class
import contextmenu

from helpers import xmlhelper
from streams.youtube import YouTube
from urihandler import UriHandler
from helpers.datehelper import DateHelper
from logger import Logger


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
        self.noImage = "hardwareinfoimage.png"

        # set context menu items
        self.contextMenuItems.append(contextmenu.ContextMenuItem("Download Item", "CtMnDownload", itemTypes="video"))

        # setup the urls
        # self.mainListUri = "https://www.youtube.com/feeds/videos.xml?user=hardwareinfovideo"
        self.mainListUri = "http://nl.hardware.info/tv/rss-private/streaming"
        self.baseUrl = "http://www.youtube.com"

        # setup the main parsing data
        # self.episodeItemRegex = '<name>([^-]+) - (\d+)-(\d+)-(\d+)[^<]*</name>'
        # self._AddDataParser(self.mainListUri, preprocessor=self.AddEpisodePaging,
        #                     parser=self.episodeItemRegex, creator=self.CreateEpisodeItem)

        self.videoItemRegex = '<(?:entry|item)>([\w\W]+?)</(?:entry|item)>'
        self._AddDataParser("http://nl.hardware.info/tv/rss-private/streaming",
                            parser=self.videoItemRegex, creator=self.CreateVideoItemHwInfo,
                            updater=self.UpdateVideoItem)
        self._AddDataParser("*", parser=self.videoItemRegex, creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        self.pageNavigationIndicationRegex = '<page>(\d+)</page>'
        self.pageNavigationRegex = '<page>(\d+)</page>'
        self.pageNavigationRegexIndex = 0
        self._AddDataParser("*", parser=self.pageNavigationRegex, creator=self.CreatePageItem)

        #===============================================================================================================
        # non standard items

        # ====================================== Actual channel setup STOPS here =======================================
        return

    # noinspection PyUnusedLocal
    def AddEpisodePaging(self, data):
        """Performs pre-process actions for data processing/

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

        items = []

        # we need to create page items. So let's just spoof the paging. Youtube has
        # a 50 max results per query limit.
        itemsPerPage = 50
        data = UriHandler.Open(self.mainListUri, proxy=self.proxy)
        xml = xmlhelper.XmlHelper(data)
        nrItems = xml.GetSingleNodeContent("openSearch:totalResults")

        for index in range(1, int(nrItems), itemsPerPage):
            items.append(self.CreateEpisodeItem([index, itemsPerPage]))
            pass
        # Continue working normal!

        return data, items

    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """

        url = "http://gdata.youtube.com/feeds/api/users/hardwareinfovideo/uploads?max-results=%s&start-index=%s" % (
            resultSet[1], resultSet[0])
        title = "Hardware Info TV %04d-%04d" % (resultSet[0], resultSet[0] + resultSet[1])
        item = mediaitem.MediaItem(title, url)
        item.complete = True
        item.icon = self.icon
        item.thumb = self.noImage
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

        xmlData = xmlhelper.XmlHelper(resultSet)

        title = xmlData.GetSingleNodeContent("title")

        # Retrieve an ID and create an URL like: http://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=OHqu64Qnz9M
        videoId = xmlData.GetSingleNodeContent("id")
        lastSlash = videoId.rfind(":") + 1
        videoId = videoId[lastSlash:]
        # url = "http://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=%s" % (videoId,)
        url = "http://www.youtube.com/watch?v=%s" % (videoId, )

        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.type = 'video'

        # date stuff
        date = xmlData.GetSingleNodeContent("published")
        year = date[0:4]
        month = date[5:7]
        day = date[8:10]
        hour = date[11:13]
        minute = date[14:16]
        # Logger.Trace("%s-%s-%s %s:%s", year, month, day, hour, minute)
        item.SetDate(year, month, day, hour, minute, 0)

        # description stuff
        description = xmlData.GetSingleNodeContent("media:description")
        item.description = description

        # thumbnail stuff
        thumbUrl = xmlData.GetTagAttribute("media:thumbnail", {'url': None}, {'height': '360'})
        # <media:thumbnail url="http://i.ytimg.com/vi/5sTMRR0_Wo8/0.jpg" height="360" width="480" time="00:09:52.500" xmlns:media="http://search.yahoo.com/mrss/" />
        if thumbUrl != "":
            item.thumb = thumbUrl
        else:
            item.thumb = self.noImage

        # finish up
        item.complete = False
        return item

    def CreateVideoItemHwInfo(self, resultSet):
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

        xmlData = xmlhelper.XmlHelper(resultSet)

        title = xmlData.GetSingleNodeContent("title")

        # Retrieve an ID and create an URL like: http://www.youtube.com/get_video_info?hl=en_GB&asv=3&video_id=OHqu64Qnz9M
        url = xmlData.GetTagAttribute("enclosure", {'url': None}, {'type': 'video/youtube'})
        Logger.Trace(url)

        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.type = 'video'

        # date stuff
        date = xmlData.GetSingleNodeContent("pubDate")
        dayname, day, month, year, time, zone = date.split(' ', 6)
        month = DateHelper.GetMonthFromName(month, language="en")
        hour, minute, seconds = time.split(":")
        Logger.Trace("%s-%s-%s %s:%s", year, month, day, hour, minute)
        item.SetDate(year, month, day, hour, minute, 0)

        # # description stuff
        description = xmlData.GetSingleNodeContent("description")
        item.description = description

        # # thumbnail stuff
        item.thumb = self.noImage
        thumbUrls = xmlData.GetTagAttribute("enclosure", {'url': None}, {'type': 'image/jpg'}, firstOnly=False)
        for thumbUrl in thumbUrls:
            if thumbUrl != "" and "thumb" not in thumbUrl:
                item.thumb = thumbUrl

        # finish up
        item.complete = False
        return item

    def UpdateVideoItem(self, item):
        """
        Accepts an arraylist of results. It returns an item.
        """

        part = item.CreateNewEmptyMediaPart()
        for s, b in YouTube.GetStreamsFromYouTube(item.url, self.proxy):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)

        item.complete = True
        return item

    def CtMnDownload(self, item):
        """ downloads a video item and returns the updated one
        """
        item = self.DownloadVideoItem(item)
        return item
