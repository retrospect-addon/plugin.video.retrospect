import mediaitem
import chn_class

from helpers.jsonhelper import JsonHelper
from logger import Logger
from regexer import Regexer
from urihandler import UriHandler
from parserdata import ParserData
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

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "atvimage.png"

        # setup the urls
        self.mainListUri = "http://www.atv.sr/on-demand/"
        self.baseUrl = "http://www.atv.sr"
        self.swfUrl = "http://www.tikilive.com/public/player/player.flash.swf"

        # setup the intial listing
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, preprocessor=self.AddLive,
                            parser='<h3>([^>]+)</h3>[\w\W]+?<a[^>]+href\W+"([^"]+)"[^>]*>meer',
                            creator=self.CreateEpisodeItem)

        # videos on the main list
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            parser='<a title="(Suri[^"]+|Whaz[^"]+)" href="([^"]+)" rel="bookmark">\W+<img[^>]*src="([^"]+)',
                            creator=self.CreateVideoItem)

        self._AddDataParser("*",
                            parser='<a[^>]*title="([^"]+)"[^>]*href="([^"]+)"[^>]*>\W+<img[^>]*src="([^"]+)"',
                            creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        self._AddDataParser("http://cache.tikilive.com:8080/socket.io/",
                            updater=self.UpdateLiveItem)
        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddLive(self, data):
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

        item = mediaitem.MediaItem("\a.: Live TV :.", "http://cache.tikilive.com:8080/socket.io/"
                                                      "?c=34967&n=TIKISESSID&i=fo84il3e7qs68uet2ql2eav081&EIO=3"
                                                      "&transport=polling&t=1428225927102-0")
        item.type = 'video'
        item.dontGroup = True
        item.isLive = True
        items.append(item)

        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateEpisodeItem(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.Trace(resultSet)

        if resultSet[0]:
            title = resultSet[0]
            url = resultSet[1]
        else:
            title = resultSet[2]
            url = resultSet[3]

        item = mediaitem.MediaItem(title, url)
        item.thumb = self.noImage
        item.icon = self.icon
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

        Logger.Trace(resultSet)

        item = mediaitem.MediaItem(resultSet[0], resultSet[1])
        item.thumb = self.noImage
        item.icon = self.icon
        item.type = 'video'
        item.thumb = resultSet[2]
        item.complete = False
        return item

    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        data = UriHandler.Open(item.url, proxy=self.proxy)
        streams = Regexer.DoRegex('<(?:source|video)[^>]+src="([^"]+)"[^>]+>', data)
        part = item.CreateNewEmptyMediaPart()
        for s in streams:
            part.AppendMediaStream(s.replace(" ", "%20"), 0)

        item.complete = True
        return item

    def UpdateLiveItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        data = UriHandler.Open(item.url, proxy=self.proxy)
        data = data[data.index('{'):]
        json = JsonHelper(data)

        sid = json.GetValue("sid")
        # The i= is the same as the one from the RTMP stream at the page of ATV.sr:
        # http://edge1.tikilive.com:1935/rtmp_tikilive/34967/amlst:mainstream/jwplayer.smil?id=dIzAVAVL2dirCfJgAPEb&i=YXBwTmFtZT1QbGF5ZXImY0lEPTM0OTY3JmNOYW1lPUFUViUyME5ldHdvcmtzJm9JRD0xMzY1NTUmb05hbWU9YXR2bmV0d29ya3Mmc0lkPWJwaHR2bXR2OXI4M2N1Mm9sZ2Q5dWx1aWs2JnVJRD0wJnVOYW1lPUd1ZXN0OWFmYTE=

        # videoUrl = "http://edge2.tikilive.com:1935/html5_tikilive/34967/amlst:mainstream/playlist.m3u8" \
        #            "?i=8xbrQERMXS2dTUKuAPbW&i=YXBwTmFtZT1QbGF5ZXImY0lEPTM0OTY3JmNOYW1lPUFUViUyME5ldHdvcm" \
        #            "tzJm9JRD0xMzY1NTUmb05hbWU9YXR2bmV0d29ya3Mmc0lkPWJwaHR2bXR2OXI4M2N1Mm9sZ2Q5dWx1aWs2JnVJRD0wJnVOYW1lPUd1ZXN0YzExZmE=&id=%s" \
        #            % (sid,)
        videoUrl = "http://edge2.tikilive.com:1935/html5_tikilive/34967/amlst:mainstream/playlist.m3u8" \
                   "?i=YXBwTmFtZT1QbGF5ZXImY0lEPTM0OTY3JmNOYW1lPUFUViUyME5ldHdvcmtzJm9JRD0xMzY1NTUmb05hbW" \
                   "U9YXR2bmV0d29ya3Mmc0lkPWZvODRpbDNlN3FzNjh1ZXQycWwyZWF2MDgxJnVJRD0wJnVOYW1lPUd1ZXN0MTNiNjk=&id=%s" \
                   % (sid,)
        part = item.CreateNewEmptyMediaPart()
        for s, b in M3u8.GetStreamsFromM3u8(videoUrl, self.proxy):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)

        item.complete = True
        return item
