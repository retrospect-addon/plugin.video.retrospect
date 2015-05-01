import mediaitem
import chn_class
from helpers import datehelper
from logger import Logger
from urihandler import UriHandler
from regexer import Regexer
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
        self.noImage = "l1image.png"

        # setup the urls
        self.mainListUri = "http://www.l1.nl/programmas"
        self.baseUrl = "http://www.l1.nl"

        # setup the main parsing data
        self.episodeItemRegex = '<a href="(http://www.l1.nl/programma/[^"]+)">([^<]+)'  # used for the ParseMainList
        self.videoItemRegex = '(:?<a href="/video/[^"]+"[^>]+><img src="([^"]+)"[^>]+>[\w\W]{0,200}){0,1}<a href="(/video/[^"]+-(\d{1,2})-(\w{3})-(\d{4})[^"]*|/video/[^"]+)"[^>]*>([^>]+)</a>'

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """

        item = mediaitem.MediaItem(resultSet[1], resultSet[0])
        item.icon = self.icon
        item.thumb = self.noImage
        item.complete = True
        return item

    def PreProcessFolderList(self, data):
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

        Logger.Info("Performing Pre-Processing")
        items = []

        firstItemRegex = '<a href="(/video/[^"]+-(\d{1,2})-(\w{3})-(\d{4})[^"]*|/video/[^"]+)"[^>]*><img src="([^"]+)"[^>]+/></a>'
        firstItems = Regexer.DoRegex(firstItemRegex, data)
        if firstItems:
            Logger.Debug("Found first item of list")
            item = firstItems[0]
            url = item[0]
            if not "http:" in url:
                url = "%s%s" % (self.baseUrl, url)
            thumbUrl = item[4]
            mediaItem = mediaitem.MediaItem("Laatste uitzending", url)
            mediaItem.thumb = thumbUrl
            mediaItem.complete = False
            mediaItem.type = 'video'
            if item[1]:
                day = item[1]
                month = item[2]
                month = datehelper.DateHelper.GetMonthFromName(month, "nl", True)
                year = item[3]
                mediaItem.SetDate(year, month, day)
            items.append(mediaItem)

        Logger.Debug("Pre-Processing finished")
        return data, items

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

        Logger.Trace(resultSet)

        thumbUrl = resultSet[1]
        url = "%s%s" % (self.baseUrl, resultSet[2])
        title = resultSet[6]

        item = mediaitem.MediaItem(title, url)
        item.thumb = self.noImage
        if thumbUrl:
            item.thumb = thumbUrl
        item.icon = self.icon
        item.type = 'video'

        if resultSet[3]:
            # set date
            day = resultSet[3]
            month = resultSet[4]
            year = resultSet[5]
            Logger.Trace("%s-%s-%s", year, month, day)
            month = datehelper.DateHelper.GetMonthFromName(month, "nl", True)
            item.SetDate(year, month, day)

        item.complete = False
        return item

    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        data = UriHandler.Open(item.url, proxy=self.proxy)
        javascriptUrls = Regexer.DoRegex('<script type="text/javascript" src="(http://l1.bbvms.com/p/standaard/c/\d+.js)">', data)
        dataUrl = None
        for javascriptUrl in javascriptUrls:
            dataUrl = javascriptUrl

        if not dataUrl:
            return item

        data = UriHandler.Open(dataUrl, proxy=self.proxy)
        jsonData = Regexer.DoRegex('clipData\W*:([\w\W]{0,10000}?\}),"playerWidth', data)
        Logger.Trace(jsonData)
        json = JsonHelper(jsonData[0], logger=Logger.Instance())
        Logger.Trace(json)

        streams = json.GetValue("assets")
        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()
        for stream in streams:
            url = stream.get("src", None)
            if not "://" in url:
                url = "http://static.l1.nl/bbw%s" % (url, )
            bitrate = stream.get("bandwidth", None)
            if url:
                part.AppendMediaStream(url, bitrate)

        if not item.thumb and json.GetValue("thumbnails"):
            url = json.GetValue("thumbnails")[0].get("src", None)
            if url and not "http:/" in url:
                url = "%s%s" % (self.baseUrl, url)
            item.thumb = url
        item.complete = True
        return item

    def CtMnDownloadItem(self, item):
        item = self.DownloadVideoItem(item)
        return item
