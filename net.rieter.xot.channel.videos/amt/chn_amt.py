#===============================================================================
# Make global object available
#===============================================================================
import mediaitem
import contextmenu
import chn_class
from helpers import datehelper
from helpers import htmlhelper
from regexer import Regexer

from logger import Logger
from urihandler import UriHandler


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
        self.noImage = "amtimage.png"

        # set context menu items
        self.contextMenuItems.append(contextmenu.ContextMenuItem("Download Item", "CtMnDownloadItem", itemTypes="video"))

        # setup the urls
        self.baseUrl = "http://trailers.apple.com"
        self.mainListUri = "http://trailers.apple.com/trailers/home/feeds/just_added.json"

        # setup the main parsing data
        self.episodeItemJson = ''
        self.videoItemRegex = "(\Wtrailer[^']+'>[\w\W]{200,2000}?\W</li>\W+(?:<li class|</ul>))"
        self.mediaUrlRegex = '<a class="movieLink" href="([^"]+_)'

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """

        Logger.Trace(resultSet)
        title = resultSet["title"]
        date = resultSet["trailers"][0]["postdate"]
        url = resultSet["trailers"][0]["url"]
        thumbUrl = resultSet["poster"]
        if not "http:" in thumbUrl:
            thumbUrl = "%s%s" % (self.baseUrl, thumbUrl)
        fanart = thumbUrl.replace("poster.jpg", "background.jpg")

        # get the url that shows all trailers/clips. Because the json
        # only shows the most recent one.
        url = "%s%sincludes/playlists/web.inc" % (self.baseUrl, url)

        # Logger.Trace(date)
        dates = date.split(" ")
        # Logger.Trace(dates)
        day = dates[1]
        month = datehelper.DateHelper.GetMonthFromName(dates[2], "en")
        year = dates[3]

        # dummy class
        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.thumb = thumbUrl.replace("poster.jpg", "poster-xlarge.jpg")
        item.fanart = fanart
        item.SetDate(year, month, day)
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

        html = htmlhelper.HtmlHelper(resultSet)

        # create the item
        itemName = html.GetTagContent("h3")
        Logger.Trace(itemName)
        title = "%s - %s" % (self.parentItem.name, itemName)

        # get the URL using the name and
        location = self.parentItem.url[:self.parentItem.url.rfind("/includes/")]
        itemName = itemName.replace(' ', '').replace('-', '').lower()

        # take the large to make sure we always have a html file
        url = "%s/includes/%s/large.html" % (location, itemName)

        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.description = self.parentItem.description
        item.type = 'video'
        item.fanart = "%s/images/background.jpg" % (location,)
        Logger.Trace(item.fanart)

        # get the thumburl
        item.thumb = html.GetTagAttribute("img", {"src": None})
        urls = html.GetTagAttribute("a", {"href": None}, {"cls": "OverlayPanel[^\"]+"}, firstOnly=False)
        Logger.Trace(urls)

        if len(urls) == 0:
            # could be that there are no URL, then skip
            return None

        # get the date
        dateResult = Regexer.DoRegex('<p>Posted: (\d+)/(\d+)/(\d+)', html.data)
        for dates in dateResult:
            year = "20%s" % (dates[2],)
            day = dates[1]
            month = dates[0]
            item.SetDate(year, month, day)

        item.downloadable = True
        item.complete = False
        return item

    #noinspection PyUnusedLocal
    def CtMnDownloadItem(self, item):
        """ downloads a video item and returns the updated one
        """
        item = self.DownloadVideoItem(item)
        return item

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

        # get the description
        data = UriHandler.Open(item.url)
        videoUrl = Regexer.DoRegex(self.mediaUrlRegex, data)[0]
        Logger.Trace(videoUrl)

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()

        # actual bitrates
        #  720p -> 5300
        #  1080p -> 8300
        #  408p -> 2200
        #  640w -> 1200
        #  480 -> 800
        #  320 -> 250
        for (res, bitrate) in (('h480p', 2000), ('h720p', 4000), ('h1080p', 8000), ("h640w", 1200), ("h480", 800), ("h320", 250)):
            part.AppendMediaStream("%s%s.mov" % (videoUrl, res), bitrate)

        part.HttpHeaders["User-Agent"] = "QuickTime/7.6 (qtver=7.6;os=Windows NT 6.0Service Pack 2)"
        item.complete = True
        return item
