import mediaitem
import contextmenu
import chn_class

from streams.smil import Smil
from regexer import Regexer
from logger import Logger
from streams.youtube import YouTube
from urihandler import UriHandler
from streams.brightcove import BrightCove


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
        self.noImage = "extremeimage.png"

        # set context menu items
        self.contextMenuItems.append(contextmenu.ContextMenuItem("Download item", "CtMnDownloadItem", itemTypes="video"))

        # setup the urls
        self.mainListUri = "http://extreme.com/"
        self.baseUrl = "http://extreme.com"

        # setup the main parsing data
        self.episodeItemRegex = '<li><a href="([^"]+)" title=[^>]*>([^<]+)</a></li>'
        self.videoItemRegex = '<img src="(?P<thumburl>[^"]+)"[^>]*alt="([^"]+)" /></a>[\w\W]{0,200}<a href="(?P<url>[^"]+)"[^>]*>(?P<title>[^"]+)</a></p><p class="description">(?P<description>[^"]+)</p>'
        self.mediaUrlRegex = 'fo.addVariable\("id", "([^"]+)"\)'
        self.pageNavigationRegex = '<a[^>]*href="(/[^"]+page=)(\d+)">\d+</a>'
        self.pageNavigationRegexIndex = 1

        # ====================================== Actual channel setup STOPS here =======================================
        return
      
    def CtMnDownloadItem(self, item):
        item = self.DownloadVideoItem(item)
        return item
    
    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item. 
        """
        #item = mediaitem.MediaItem(resultSet[0], "http://www.freecaster.com/helpers/videolist_helper.php?apID=%s&i=0&q=&sortby=date&sort=DESC&event_id=" % resultSet[1])
        item = mediaitem.MediaItem(resultSet[1], "%s%s?page=1" % (self.baseUrl, resultSet[0]))
        item.icon = self.icon
        item.complete = True
        return item

    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL 
        and the Thumb! It should return a completed item. 
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)
        
        # get additional info
        data = UriHandler.Open(item.url, proxy=self.proxy)
        guid = Regexer.DoRegex('<meta property="og:video" content="http://player.extreme.com/FCPlayer.swf\?id=([^&]+)&amp[^"]+" />', data)

        #<param name="flashvars" value="id=dj0xMDEzNzQyJmM9MTAwMDAwNA&amp;tags=source%253Dfreecaster&amp;autoplay=1" />
        # http://freecaster.tv/player/smil/dj0xMDEzNzQyJmM9MTAwMDAwNA -> playlist with bitrate
        # http://freecaster.tv/player/smil/dj0xMDEzNzQyJmM9MTAwMDAwNA -> info (not needed, get description from main page.

        if len(guid) > 0:
            url = '%s/player/smil/%s' % (self.baseUrl, guid[0],) 
            data = UriHandler.Open(url)

            smiller = Smil(data)
            baseUrl = smiller.GetBaseUrl()
            urls = smiller.GetVideosAndBitrates()

            part = item.CreateNewEmptyMediaPart()
            for url in urls:
                if "youtube" in url[0]:
                    for s, b in YouTube.GetStreamsFromYouTube(url[0], self.proxy):
                        item.complete = True
                        part.AppendMediaStream(s, b)
                else:
                    part.AppendMediaStream("%s%s" % (baseUrl, url[0]), bitrate=int(int(url[1]) / 1000))
                item.complete = True

            Logger.Trace("UpdateVideoItem complete: %s", item)
            return item

        # Try the brightcove
        brightCoveRegex = '<object id="myExperience[\w\W]+?videoPlayer" value="(\d+)"[\w\W]{0,1000}?playerKey" value="([^"]+)'
        brightCoveData = Regexer.DoRegex(brightCoveRegex, data)
        Logger.Trace(brightCoveData)
        if len(brightCoveData) > 0:
            seed = "c5f9ae8729f7054d43187989ef3421531ee8678d"
            objectData = brightCoveData[0]
            # from proxyinfo import ProxyInfo
            playerKey = str(objectData[1])
            videoId = int(objectData[0])

            part = item.CreateNewEmptyMediaPart()
            # But we need the IOS streams!
            amfHelper = BrightCove(Logger.Instance(), playerKey, videoId, str(item.url), seed, proxy=self.proxy)
            for stream, bitrate in amfHelper.GetStreamInfo(renditions="IOSRenditions"):
                part.AppendMediaStream(stream, bitrate)

        # Logger.Error("Cannot find GUID in url: %s", item.url)
        return item
