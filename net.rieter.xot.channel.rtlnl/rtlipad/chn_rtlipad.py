import mediaitem
import chn_class

from helpers import xmlhelper
from logger import Logger
from streams.m3u8 import M3u8


class Channel(chn_class.Channel):

    def __init__(self, channelInfo):
        """Initialisation of the class.

        channelInfo: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "rtlimage.png"

        # setup the urls
        self.mainListUri = "http://www.rtl.nl/system/s4m/ipadfd/d=ipad/fmt=adaptive/"
        self.baseUrl = "http://www.rtl.nl/service/gemist/device/ipad/feed/index.xml"

        # setup the main parsing data
        self.episodeItemRegex = "<serieitem><itemsperserie_url>([^<]+)</itemsperserie_url><serienaam>([^<]+)" \
                                "</serienaam><seriescoverurl>([^<]+)</seriescoverurl><serieskey>([^<]+)</serieskey>"
        self.videoItemRegex = '(<item>([\w\W]+?)</item>)'

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

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
        # Logger.Trace("iRTL :: %s", resultSet)

        item = mediaitem.MediaItem(resultSet[1], resultSet[0])
        item.thumb = resultSet[2]
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

        xml = resultSet[0]
        xmlData = xmlhelper.XmlHelper(xml)

        title = xmlData.GetSingleNodeContent("title")
        eTitle = xmlData.GetSingleNodeContent("episodetitel")
        if not eTitle == title:
            title = "%s - %s" % (title, eTitle)
        thumb = xmlData.GetSingleNodeContent("thumbnail")
        url = xmlData.GetSingleNodeContent("movie")
        date = xmlData.GetSingleNodeContent("broadcastdatetime")
        desc = xmlData.GetSingleNodeContent("samenvattinglang") or title

        item = mediaitem.MediaItem(title, url)
        item.description = desc
        item.icon = self.icon
        item.thumb = thumb
        item.type = 'video'

        item.SetDate(date[0:4], date[5:7], date[8:10], date[11:13], date[14:16], date[17:20])
        item.complete = False
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

        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        # load the details.
        part = item.CreateNewEmptyMediaPart()
        # prevent the "418 I'm a teapot" error
        part.HttpHeaders["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0"

        for s, b in M3u8.GetStreamsFromM3u8(item.url, self.proxy):
            part.AppendMediaStream(s, b)

        item.complete = True
        return item
