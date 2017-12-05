# coding:UTF-8
import mediaitem
import chn_class

from parserdata import ParserData
from regexer import Regexer
from helpers import subtitlehelper
from logger import Logger
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper


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
        self.noImage = "urplayimage.png"

        # setup the urls
        self.mainListUri = "http://urplay.se/sok?product_type=series&rows=1000&start=0"
        self.baseUrl = "http://urplay.se"
        self.swfUrl = "http://urplay.se/assets/jwplayer-6.12-17973009ab259c1dea1258b04bde6e53.swf"

        # programs
        programReg = 'href="/(?<url>[^/]+/(?<id>\d+)[^"]+)"[^>]*>[^<]+</a>\W+<figure>[\W\w]' \
                     '{0,3000}?<h2[^>]*>(?<title>[^<]+)</h2>\W+<p[^>]+>(?<description>[^<]+)' \
                     '<span class="usp">(?<description2>[^<]+)'
        programReg = Regexer.FromExpresso(programReg)
        self._AddDataParser(self.mainListUri,
                            name="Show parser with categories",
                            matchType=ParserData.MatchExact,
                            preprocessor=self.AddCategories,
                            parser=programReg, creator=self.CreateEpisodeItem)

        self._AddDataParser("http://urplay.se/bladdra/",
                            name="Category show parser",
                            matchType=ParserData.MatchStart,
                            parser=programReg,
                            creator=self.CreateEpisodeItem)

        # Categories
        catReg = '<a[^>]+href="(?<url>[^"]+)">\W*<img[^>]+data-src="(?<thumburl>[^"]+)' \
                 '"[^>]*>\W*<span>(?<title>[^<]+)<'
        catReg = Regexer.FromExpresso(catReg)
        self._AddDataParser("http://urplay.se/", name="Category parser",
                            matchType=ParserData.MatchExact,
                            parser=catReg,
                            creator=self.CreateCategory)

        # videos
        # videoItemRegex = 'href="/(?<url>\w+/(?<id>\d+)[^"]+)[^>]*>[^<]+</a>\W*<div[^>]*>\W*' \
        #                  '<figure[^>]*>\W+<span[^<]+[^>]*>\W+<img[^>]+data-src="(?<thumb>[^"]+)"' \
        #                  '\W+<span[^>]*class="(?<type>[^"]+)"[^>]*>[\w\W]{0,500}?<h3>' \
        #                  '(?<title>[^<]+)</h3>\W+<p[^>]*>(?<serie>[^<]+)</p>\W*<p[^>]+>' \
        #                  '(?<description>[^<]+)'
        # videoItemRegex = Regexer.FromExpresso(videoItemRegex)
        singleVideoRegex = '<meta \w+="name" content="(?:[^:]+: )?(?<title>[^"]+)' \
                           '"[^>]*>\W*<meta \w+="description" content="(?<description>[^"]+)"' \
                           '[^>]*>\W*<meta \w+="url" content="(?:[^"]+/(?<url>\w+/' \
                           '(?<id>\d+)[^"]+))"[^>]*>\W*<meta \w+="thumbnailURL[^"]+" ' \
                           'content="(?<thumbnail>[^"]+)"[^>]*>\W+<meta \w+="uploadDate" ' \
                           'content="(?<date>[^"]+)"'
        singleVideoRegex = Regexer.FromExpresso(singleVideoRegex)
        self._AddDataParser("http://urplay.se/sok?product_type=program",
                            parser=programReg, preprocessor=self.GetVideoSection,
                            creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        self._AddDataParser("*", parser=programReg, preprocessor=self.GetVideoSection,
                            creator=self.CreateVideoItem, updater=self.UpdateVideoItem)
        self._AddDataParser("*", parser=singleVideoRegex, preprocessor=self.GetVideoSection,
                            creator=self.CreateSingleVideoItem, updater=self.UpdateVideoItem)

        self.mediaUrlRegex = "urPlayer.init\(([^<]+)\);"

        #===============================================================================================================
        # non standard items
        self.__videoItemFound = False

        #===============================================================================================================
        # Test cases:
        #   Anaconda Auf Deutch : RTMP, Subtitles

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateCategory(self, resultSet):
        if not resultSet['thumburl'].startswith("http"):
            resultSet['thumburl'] = "%s/%s" % (self.baseUrl, resultSet["thumburl"])

        resultSet["url"] = "%s?rows=1000&start=0" % (resultSet["url"],)
        return self.CreateFolderItem(resultSet)

    def AddCategories(self, data):
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
        maxItems = 200
        categories = {
            # "\a.: Mest spelade :.": "http://urplay.se/Mest-spelade",
            "\a.: Mest delade :.": "http://urplay.se/sok?product_type=program&query=&view=most_viewed&rows=%s&start=0" % (maxItems, ),
            "\a.: Senaste :.": "http://urplay.se/sok?product_type=program&query=&view=latest&rows=%s&start=0" % (maxItems, ),
            "\a.: Sista chansen :.": "http://urplay.se/sok?product_type=program&query=&view=default&rows=%s&start=0" % (maxItems, ),
            "\a.: Kategorier :.": "http://urplay.se/"
        }

        for cat in categories:
            item = mediaitem.MediaItem(cat, categories[cat])
            item.thumb = self.noImage
            item.complete = True
            item.icon = self.icon
            item.dontGroup = True
            items.append(item)

        Logger.Debug("Pre-Processing finished")
        return data, items

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

        title = "%(title)s" % resultSet
        url = "%s/%s" % (self.baseUrl, resultSet["url"])
        fanart = "http://assets.ur.se/id/%(id)s/images/1_hd.jpg" % resultSet
        thumb = "http://assets.ur.se/id/%(id)s/images/1_l.jpg" % resultSet
        item = mediaitem.MediaItem(title, url)
        item.thumb = thumb
        item.description = "%(description)s\n%(description2)s" % resultSet
        item.fanart = fanart
        item.icon = self.icon
        return item

    def GetVideoSection(self, data):
        """Performs pre-process actions for data processing

                Arguments:
                data : string - the retrieve data that was loaded for the current item and URL.

                Returns:
                A tuple of the data and a list of MediaItems that were generated.
        """

        Logger.Info("Performing Pre-Processing")
        items = []

        data = data[:data.find('<h2>Relaterade</h2>')]
        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateVideoItemWithSerie(self, resultSet):
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
        item = self.CreateVideoItem(resultSet)
        if item is None:
            return item

        if resultSet["serie"]:
            item.name = "%s - %s" % (resultSet["serie"], item.name)
        return item

    def CreateSingleVideoItem(self, resultSet):
        """ If no items were found, we should find the main item on the page. """

        if self.__videoItemFound:
            return None
        return self.CreateVideoItem(resultSet)

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

        # Logger.Trace(resultSet)

        title = resultSet["title"]
        url = "%s/%s" % (self.baseUrl, resultSet["url"])
        thumb = "http://assets.ur.se/id/%(id)s/images/1_l.jpg" % resultSet
        item = mediaitem.MediaItem(title, url)
        item.type = "video"
        item.thumb = thumb
        item.description = resultSet["description"]
        item.fanart = self.parentItem.fanart
        item.icon = self.icon
        item.complete = False

        self.__videoItemFound = True
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

        # noinspection PyStatementEffect
        """
        <script type="text/javascript">/* <![CDATA[ */ var movieFlashVars = "
        image=http://assets.ur.se/id/147834/images/1_l.jpg
        file=/147000-147999/147834-20.mp4
        plugins=http://urplay.se/jwplayer/plugins/gapro-1.swf,http://urplay.se/jwplayer/plugins/sharing-2.swf,http://urplay.se/jwplayer/plugins/captions/captions.swf
        sharing.link=http://urplay.se/147834
        gapro.accountid=UA-12814852-8
        captions.margin=40
        captions.fontsize=11
        captions.back=false
        captions.file=http://undertexter.ur.se/147000-147999/147834-19.tt
        streamer=rtmp://streaming.ur.se/ondemand
        autostart=False"; var htmlVideoElementSource = "http://streaming.ur.se/ondemand/mp4:147834-23.mp4/playlist.m3u8?location=SE"; /* //]]> */ </script>

        """

        data = UriHandler.Open(item.url, proxy=self.proxy)
        # Extract stream JSON data from HTML
        streams = Regexer.DoRegex(self.mediaUrlRegex, data)
        jsonData = streams[0]
        json = JsonHelper(jsonData, logger=Logger.Instance())
        Logger.Trace(json.json)

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()

        streams = {
            # No longer used I think
            "file_flash": 900,
            "file_mobile": 750,
            "file_hd": 2000,
            "file_html5": 850,
            "file_html5_hd": 2400,

            'file_rtmp': 900,
            'file_rtmp_hd': 2400,
            'file_http_sub': 750,
            'file_http': 900,
            'file_http_sub_hd': 2400,
            'file_http_hd': 2500
        }

        # u'file_rtmp_hd': u'urplay/mp4: 178000-178999/178963-7.mp4',
        # u'file_rtmp': u'urplay/mp4: 178000-178999/178963-11.mp4',
        #
        # u'file_http': u'urplay/_definst_/mp4: 178000-178999/178963-11.mp4/',
        # u'file_http_sub_hd': u'urplay/_definst_/mp4: 178000-178999/178963-25.mp4/',
        # u'file_http_sub': u'urplay/_definst_/mp4: 178000-178999/178963-28.mp4/',
        # u'file_http_hd': u'urplay/_definst_/mp4: 178000-178999/178963-7.mp4/',

        # generic server information
        proxy = json.GetValue("streaming_config", "streamer", "redirect")
        if proxy is None:
            proxyData = UriHandler.Open("http://streaming-loadbalancer.ur.se/loadbalancer.json", proxy=self.proxy, noCache=True)
            proxyJson = JsonHelper(proxyData)
            proxy = proxyJson.GetValue("redirect")
        Logger.Trace("Found RTMP Proxy: %s", proxy)

        rtmpApplication = json.GetValue("streaming_config", "rtmp", "application")
        Logger.Trace("Found RTMP Application: %s", rtmpApplication)

        # find all streams
        for streamType in streams:
            if streamType not in json.json:
                Logger.Debug("%s was not found as stream.", streamType)
                continue

            bitrate = streams[streamType]
            streamUrl = json.GetValue(streamType)
            Logger.Trace(streamUrl)
            if not streamUrl:
                Logger.Debug("%s was found but was empty as stream.", streamType)
                continue

            #onlySweden = False
            if streamUrl.startswith("se/") or ":se/" in streamUrl:  # or json.GetValue("only_in_sweden"): -> will be in the future
                onlySweden = True
                Logger.Warning("Streams are only available in Sweden: onlySweden=%s", onlySweden)
                # No need to replace the se/ part. Just log.
                # streamUrl = streamUrl.replace("se/", "", 1)

            # although all urls can be handled via RTMP, let's not do that and make the HTTP ones HTTP
            alwaysRtmp = False
            if alwaysRtmp or "_rtmp" in streamType:
                url = "rtmp://%s/%s/?slist=mp4:%s" % (proxy, rtmpApplication, streamUrl)
                url = self.GetVerifiableVideoUrl(url)
            elif "_http" in streamType:
                url = "http://%s/%smaster.m3u8" % (proxy, streamUrl)
            else:
                Logger.Warning("Unsupported Stream Type: %s", streamType)
                continue
            part.AppendMediaStream(url.strip("/"), bitrate)

        # get the subtitles
        captions = json.GetValue("subtitles")
        subtitle = None
        for caption in captions:
            language = caption["label"]
            default = caption["default"]
            url = caption["file"]
            if url.startswith("//"):
                url = "http:%s" % (url, )
            Logger.Debug("Found subtitle language: %s [Default=%s]", language, default)
            if "Svenska" in language:
                Logger.Debug("Selected subtitle language: %s", language)
                fileName = caption["file"]
                fileName = fileName[fileName.rindex("/") + 1:] + ".srt"
                if url.endswith("vtt"):
                    subtitle = subtitlehelper.SubtitleHelper.DownloadSubtitle(url, fileName, "webvtt", proxy=self.proxy)
                else:
                    subtitle = subtitlehelper.SubtitleHelper.DownloadSubtitle(url, fileName, "ttml", proxy=self.proxy)
                break
        part.Subtitle = subtitle

        item.complete = True
        return item
