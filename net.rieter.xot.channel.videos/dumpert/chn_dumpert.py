#===============================================================================
# Import the default modules
#===============================================================================
import string
#===============================================================================
# Make global object available
#===============================================================================
import mediaitem
import contextmenu
import chn_class

from helpers import datehelper
from regexer import Regexer
from logger import Logger
from urihandler import UriHandler
from xbmcwrapper import XbmcWrapper
from helpers.encodinghelper import EncodingHelper
from helpers.jsonhelper import JsonHelper
from streams.youtube import YouTube


class Channel(chn_class.Channel):

    def __init__(self, channelInfo):
        """Initialisation of the class.

        Arguments:
        channelInfo: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "dumpertimage.png"

        # set context menu items
        self.contextMenuItems.append(contextmenu.ContextMenuItem("Download Item", "CtMnDownloadItem", itemTypes="video"))

        # setup the urls
        self.baseUrl = "http://www.dumpert.nl/mediabase/flv/%s_YTDL_1.flv.flv"

        # setup the main parsing data
        self.mainListUri = "#mainlist"
        self._AddDataParser(self.mainListUri, preprocessor=self.GetMainListItems)
        self.videoItemRegex = '<a[^>]+href="([^"]+)"[^>]*>\W+<img src="([^"]+)[\W\w]{0,400}<h\d>([^<]+)</h\d>\W+<[^>]' \
                              '*date"{0,1}>(\d+) (\w+) (\d+) (\d+):(\d+)'
        self._AddDataParser("*",
                            parser=self.videoItemRegex, creator=self.CreateVideoItem,
                            updater=self.UpdateVideoItem)

        self.mediaUrlRegex = '<div class="videoplayer" id="video1" data-files="([^"]+)"'

        # ====================================== Actual channel setup STOPS here =======================================
        self.__IgnoreCookieLaw()
        return

    def GetMainListItems(self, data):
        """ 
        accepts an url and returns an list with items of type CListItem
        Items have a name and url. This is used for the filling of the progwindow
        """

        items = []
        urlPattern = "http://www.dumpert.nl/%s/%s/"

        for page in range(1, 3):
            item = mediaitem.MediaItem("Toppertjes - Pagina %s" % (page, ), urlPattern % ('toppers', page))
            item.icon = self.icon
            items.append(item)

        for page in range(1, 11):
            item = mediaitem.MediaItem("Filmpjes - Pagina %s" % (page, ), urlPattern % ('filmpjes', page))
            item.icon = self.icon
            items.append(item)

        item = mediaitem.MediaItem("Zoeken", "searchSite")
        item.icon = self.icon
        items.append(item)

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

        #                         0              1             2                             3
        #<a class="item" href="([^"]+)"[^=]+="([^"]+)" alt="([^"]+)[^:]+<div class="date">([^<]+)

        #Logger.Trace(resultSet)

        item = mediaitem.MediaItem(resultSet[2], resultSet[0], type='video')
        item.icon = self.icon
        item.description = resultSet[2]
        item.thumb = resultSet[1]

        try:
            month = datehelper.DateHelper.GetMonthFromName(resultSet[4], "nl")
            item.SetDate(resultSet[5], month, resultSet[3], resultSet[6], resultSet[7], 0)
        except:
            Logger.Error("Error matching month: %s", resultSet[4].lower(), exc_info=True)

        item.complete = False
        item.downloadable = True
        return item

    def UpdateVideoItem(self, item):
        """
        Updates the item
        """

        data = UriHandler.Open(item.url, proxy=self.proxy)

        baseEncode = Regexer.DoRegex(self.mediaUrlRegex, data)[-1]
        jsonData = EncodingHelper.DecodeBase64(baseEncode)
        json = JsonHelper(jsonData, logger=Logger.Instance())
        Logger.Trace(json)

        # "flv": "http://media.dumpert.nl/flv/e2a926ff_10307954_804223649588516_151552487_n.mp4.flv",
        # "tablet": "http://media.dumpert.nl/tablet/e2a926ff_10307954_804223649588516_151552487_n.mp4.mp4",
        # "mobile": "http://media.dumpert.nl/mobile/e2a926ff_10307954_804223649588516_151552487_n.mp4.mp4",

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()
        streams = json.GetValue()
        for key in streams:
            if key == "flv":
                part.AppendMediaStream(streams[key], 1000)
            elif key == "tablet":
                part.AppendMediaStream(streams[key], 800)
            elif key == "mobile":
                part.AppendMediaStream(streams[key], 450)
            elif key == "embed" and streams[key].startswith("youtube"):
                embedType, youtubeId = streams[key].split(":")
                url = "https://www.youtube.com/watch?v=%s" % (youtubeId, )
                for s, b in YouTube.GetStreamsFromYouTube(url, self.proxy):
                    item.complete = True
                    part.AppendMediaStream(s, b)
            else:
                Logger.Debug("Key '%s' was not used", key)

        item.complete = True
        Logger.Trace("VideoItem updated: %s", item)
        return item

    def SearchSite(self, url=None):
        """
        Creates an list of items by searching the site
        """
        items = []

        needle = XbmcWrapper.ShowKeyBoard()
        if needle:
            #convert to HTML
            needle = string.replace(needle, " ", "%20")
            searchUrl = "http://www.dumpert.nl/search/V/%s/ " % (needle, )
            temp = mediaitem.MediaItem("Search", searchUrl)
            return self.ProcessFolderList(temp)

        return items

    #==============================================================================
    # ContextMenu functions
    #==============================================================================
    def CtMnDownloadItem(self, item):
        item = self.DownloadVideoItem(item)
        return item

    def __IgnoreCookieLaw(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.Info("Setting the Cookie-Consent cookie for www.dumpert.nl")

        # Set-Cookie: cpc=10; path=/; domain=www.dumpert.nl; expires=Thu, 11-Jun-2020 18:49:38 GMT
        UriHandler.SetCookie(name='cpc', value='10', domain='.www.dumpert.nl')
        return
