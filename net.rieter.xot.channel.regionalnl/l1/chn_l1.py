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
        self.mainListUri = "https://l1.nl/gemist/"
        self.baseUrl = "https://l1.nl"

        # setup the main parsing data
        episodeRegex = '<li>\W*<a[^>]*href="(?<url>/[^"]+)"[^>]*>(?<title>[^<]+)</a>\W*</li>'
        episodeRegex = Regexer.FromExpresso(episodeRegex)
        self._AddDataParser(self.mainListUri, preprocessor=self.PreProcessFolderList,
                            parser=episodeRegex, creator=self.CreateEpisodeItem)

        videoRegex = '<a[^>]*class="mediaItem"[^>]*href="(?<url>[^"]+)"[^>]*title="(?<title>' \
                     '[^"]+)"[^>]*>[\w\W]{0,500}?<img[^>]+src="/(?<thumburl>[^"]+)'
        videoRegex = Regexer.FromExpresso(videoRegex)
        self._AddDataParser("*", parser=videoRegex, creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        pageRegex = '<a[^>]+href="https?://l1.nl/([^"]+?pagina=)(\d+)"'
        pageRegex = Regexer.FromExpresso(pageRegex)
        self.pageNavigationRegexIndex = 1
        self._AddDataParser("*", parser=pageRegex, creator=self.CreatePageItem)
        # self.episodeItemRegex = '<a href="(http://www.l1.nl/programma/[^"]+)">([^<]+)'  # used for the ParseMainList
        # self.videoItemRegex = '(:?<a href="/video/[^"]+"[^>]+><img src="([^"]+)"[^>]+>[\w\W]{0,200}){0,1}<a href="(/video/[^"]+-(\d{1,2})-(\w{3})-(\d{4})[^"]*|/video/[^"]+)"[^>]*>([^>]+)</a>'

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

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

        if '>Populair<' in data:
            data = data[data.index('>Populair<'):]
        if '>L1-kanalen<' in data:
            data = data[:data.index('>L1-kanalen<')]

        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateEpisodeItem(self, resultSet):
        """ We need to exclude L1 Gemist """

        item = chn_class.Channel.CreateEpisodeItem(self, resultSet)
        if "L1 Gemist" in item.name:
            return None
        return item

    def CreateVideoItem(self, resultSet):
        item = chn_class.Channel.CreateVideoItem(self, resultSet)
        if not item.thumb.startswith("http"):
            item.thumb = "%s/%s" % (self.baseUrl, item.thumb)
        return item

    def CreateVideoItem_old(self, resultSet):
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
        javascriptUrls = Regexer.DoRegex('<script type="text/javascript" src="(//l1.bbvms.com/p/\w+/c/\d+.js)"', data)
        dataUrl = None
        for javascriptUrl in javascriptUrls:
            dataUrl = javascriptUrl
            if not dataUrl.startswith("http"):
                dataUrl = "https:%s" % (dataUrl, )

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
            if "://" not in url:
                url = "http://static.l1.nl/bbw%s" % (url, )
            bitrate = stream.get("bandwidth", None)
            if url:
                part.AppendMediaStream(url, bitrate)

        if not item.thumb and json.GetValue("thumbnails"):
            url = json.GetValue("thumbnails")[0].get("src", None)
            if url and "http:/" not in url:
                url = "%s%s" % (self.baseUrl, url)
            item.thumb = url
        item.complete = True
        return item

    def CtMnDownloadItem(self, item):
        item = self.DownloadVideoItem(item)
        return item
