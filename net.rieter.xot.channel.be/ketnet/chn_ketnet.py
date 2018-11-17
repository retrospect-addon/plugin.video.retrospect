# coding:Cp1252
import chn_class
import mediaitem

from helpers.languagehelper import LanguageHelper
from regexer import Regexer
from logger import Logger
from urihandler import UriHandler
from parserdata import ParserData
from helpers.jsonhelper import JsonHelper
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

        if self.channelCode == "ketnet":
            self.noImage = "ketnetimage.jpg"
            self.mainListUri = "https://www.ketnet.be/kijken"
            self.baseUrl = "https://www.ketnet.be"
            self.mediaUrlRegex = 'playerConfig\W*=\W*(\{[\w\W]{0,2000}?);.vamp'

        elif self.channelCode == "cobra":
            self.noImage = "cobraimage.png"
            self.mainListUri = "http://www.cobra.be/cm/cobra/cobra-mediaplayer"
            self.baseUrl = "http://www.cobra.be"

        self.swfUrl = "%s/html/flash/common/player.swf" % (self.baseUrl,)

        episodeRegex = '<a[^>]+href="(?<url>/kijken[^"]+)"[^>]*>\W*<img[^>]+src="(?<thumburl>[^"]+)"[^>]+alt="(?<title>[^"]+)"'
        episodeRegex = Regexer.FromExpresso(episodeRegex)
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            parser=episodeRegex, creator=self.CreateEpisodeItem)

        self._AddDataParser("*", preprocessor=self.SelectVideoSection)

        videoRegex = Regexer.FromExpresso('<a title="(?<title>[^"]+)" href="(?<url>[^"]+)"[^>]*>'
                                          '\W+<img src="(?<thumburl>[^"]+)"[^<]+<span[^<]+[^<]+'
                                          '[^>]+></span>\W+(?<description>[^<]+)')
        self._AddDataParser("*", parser=videoRegex, creator=self.CreateVideoItem,
                            updater=self.UpdateVideoItem)

        folderRegex = Regexer.FromExpresso('<span class="more-of-program" rel="/(?<url>[^"]+)">')
        self._AddDataParser("*", parser=folderRegex, creator=self.CreateFolderItem)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def SelectVideoSection(self, data):
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

        Logger.info("Performing Pre-Processing")
        items = []

        endOfSection = data.rfind('<div class="grid-4">')
        if endOfSection > 0:
            data = data[:endOfSection]

        # find the first main video
        jsonData = Regexer.DoRegex(self.mediaUrlRegex, data)
        if not jsonData:
            Logger.debug("No show data found as JSON")
            return data, items

        Logger.trace(jsonData[0])
        json = JsonHelper(jsonData[0])
        title = json.get_value("title")
        url = json.get_value("source", "hls")
        item = mediaitem.MediaItem(title, url)
        item.type = 'video'
        item.description = json.get_value("description", fallback=None)
        item.thumb = json.get_value("image", fallback=self.noImage)
        item.fanart = self.parentItem.fanart
        item.complete = False
        items.append(item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def CreateFolderItem(self, resultSet):
        """Creates a MediaItem of type 'folder' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(strig) - the resultSet of the self.folderItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.trace(resultSet)

        resultSet["title"] = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
        return chn_class.Channel.CreateFolderItem(self, resultSet)

    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        if not item.url.endswith("m3u8"):
            data = UriHandler.Open(item.url, proxy=self.proxy)
            jsonData = Regexer.DoRegex(self.mediaUrlRegex, data)
            if not jsonData:
                Logger.error("Cannot find JSON stream info.")
                return item

            json = JsonHelper(jsonData[0])
            Logger.trace(json.json)
            stream = json.get_value("source", "hls")
            if stream is None:
                stream = json.get_value("mzsource", "hls")
            Logger.debug("Found HLS: %s", stream)
        else:
            stream = item.url

        part = item.create_new_empty_media_part()
        for s, b in M3u8.get_streams_from_m3u8(stream, self.proxy):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.append_media_stream(s, b)

        # var playerConfig = {"id":"mediaplayer","width":"100%","height":"100%","autostart":"false","image":"http:\/\/www.ketnet.be\/sites\/default\/files\/thumb_5667ea22632bc.jpg","brand":"ketnet","source":{"hls":"http:\/\/vod.stream.vrt.be\/ketnet\/_definst_\/mp4:ketnet\/2015\/12\/Ben_ik_familie_van_R001_A0023_20151208_143112_864.mp4\/playlist.m3u8"},"analytics":{"type_stream":"vod","playlist":"Ben ik familie van?","program":"Ben ik familie van?","episode":"Ben ik familie van?: Warre - Aflevering 3","parts":"1","whatson":"270157835527"},"title":"Ben ik familie van?: Warre - Aflevering 3","description":"Ben ik familie van?: Warre - Aflevering 3"}
        return item    
