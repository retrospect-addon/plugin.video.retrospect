import mediaitem
import chn_class

from regexer import Regexer
from logger import Logger
from urihandler import UriHandler
from helpers.datehelper import DateHelper
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
        self.noImage = ""

        # setup the urls
        if self.channelCode == '538':
            self.noImage = "radio538image.png"
            self.mainListUri = "http://www.538gemist.nl/"
            self.baseUrl = "http://www.538.nl"
            self.swfUrl = "http://www.538.nl/jwplayer/player.swf"

        # setup the main parsing data
        self.episodeItemRegex = '<option value="(\d+)">([^<]+)</option>'
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            preprocessor=self.AddLiveStreams,
                            parser=self.episodeItemRegex, creator=self.CreateEpisodeItem)

        # proces video
        self.videoItemRegex = '<figure style="background-image:url\(([^"]+)\);">[\w\W]{0,200}?<h1>' \
                              '<a[^>]+href="(/gemist/(\d+)/[^"]+)"[^>]*title="([^"]+)"[^>]*>[^>]*></h1>' \
                              '<p>([^<]+)</p><time datetime="\W*(\d+) (\w+) (\d+)\W+(\d+):(\d+)\W+uur">'
        self._AddDataParser("*", parser=self.videoItemRegex, creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        # proces pages
        self.pageNavigationRegex = '<a href="(/gemist/filter/pagina/)(\d+)[\w\W]{0,200}?<span>Volgende</span></a>'
        self.pageNavigationRegexIndex = 1
        self._AddDataParser("*", parser=self.pageNavigationRegex, creator=self.CreatePageItem)

        # updater for live streams
        self._AddDataParsers(("^http://538-?hls.lswcdn.triple-it.nl/content.+", "^http://hls2.slamfm.nl/content.+"),
                             matchType=ParserData.MatchRegex, updater=self.UpdateLiveStream)

        self.mediaUrlRegex = '<media:content url="([^"]+)"'

        #===============================================================================================================
        # non standard items
        self.EndOfProgramsFound = True  # should be done in the pre-processor

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

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.Trace(resultSet)

        # the URL
        programId = resultSet[0]
        url = "http://www.538.nl/gemist/filter/pagina/1/type/video,audiofragmenten,uitzending-gemist" \
              "/programma/%s/sortering/date" % (programId, )

        if programId == "0":
            # first set of <option> elements, we should use them
            self.EndOfProgramsFound = False
            return None

        if self.EndOfProgramsFound:
            return None

        # the title
        title = resultSet[1]

        item = mediaitem.MediaItem(title, url)
        # item.thumb = resultSet.get("thumburl", None)
        # item.description = resultSet.get("description", "")
        item.icon = self.icon
        item.complete = True
        item.fanart = self.fanart
        return item

    def AddLiveStreams(self, data):
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

        # add live stuff
        live = mediaitem.MediaItem("\bLive streams", "")
        live.icon = self.icon
        live.thumb = self.noImage
        live.complete = True

        tv538 = mediaitem.MediaItem("TV 538", "http://538hls.lswcdn.triple-it.nl/content/538tv/538tv.m3u8")
        tv538.icon = self.icon
        tv538.thumb = self.noImage
        tv538.type = "video"
        tv538.complete = False
        tv538.isLive = True
        live.items.append(tv538)

        cam538 = mediaitem.MediaItem("538 Webcam", "http://538hls.lswcdn.triple-it.nl/content/538webcam/538webcam.m3u8")
        cam538.icon = self.icon
        cam538.thumb = self.noImage
        cam538.type = "video"
        cam538.isLive = True
        live.items.append(cam538)

        radio538 = mediaitem.MediaItem("Radio 538", "http://vip-icecast.538.lw.triple-it.nl/RADIO538_MP3")
        radio538.icon = self.icon
        radio538.thumb = self.noImage
        radio538.type = "audio"
        radio538.isLive = True
        radio538.complete = True
        radio538.AppendSingleStream(radio538.url)
        live.items.append(radio538)

        slam = mediaitem.MediaItem("Slam! FM Webcam", "http://538hls.lswcdn.triple-it.nl/content/slamwebcam/slamwebcam.m3u8")
        slam.icon = self.icon
        slam.thumb = self.noImage
        slam.type = "video"
        slam.isLive = True
        live.items.append(slam)

        slam = mediaitem.MediaItem("Slam! TV", "http://hls2.slamfm.nl/content/slamtv/slamtv.m3u8")
        slam.icon = self.icon
        slam.thumb = self.noImage
        slam.type = "video"
        slam.isLive = True
        live.items.append(slam)

        slamFm = mediaitem.MediaItem("Slam! FM", "http://edge2-icecast.538.lw.triple-it.nl/SLAMFM_MP3")
        slamFm.icon = self.icon
        slamFm.thumb = self.noImage
        slamFm.type = "audio"
        slamFm.isLive = True
        slamFm.AppendSingleStream(slamFm.url)
        slamFm.complete = True
        live.items.append(slamFm)

        items = [live]

        # now = datetime.datetime.now()
        # fromDate = now - datetime.timedelta(365)
        # Logger.Debug("Showing dates starting from %02d%02d%02d to %02d%02d%02d", fromDate.year, fromDate.month, fromDate.day, now.year, now.month, now.day)
        # current = fromDate
        # while current <= now:
        #     url = "http://www.538.nl/ajax/VdaGemistBundle/Gemist/ajaxGemistFilter/date/%02d%02d%02d" % (current.year, current.month, current.day)
        #     title = "Afleveringen van %02d-%02d-%02d" % (current.year, current.month, current.day)
        #     dateItem = mediaitem.MediaItem(title, url)
        #     dateItem.icon = self.icon
        #     dateItem.thumb = self.noImage
        #     dateItem.complete = True
        #     dateItem.httpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        #     items.append(dateItem)
        #     current = current + datetime.timedelta(1)

        data = data[0:data.find('data-filter-type="sortering"')]
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

        thumbUrl = resultSet[0]
        episodeUrl = resultSet[1]
        if not episodeUrl.startswith("http"):
            episodeUrl = "%s%s" % (self.baseUrl, episodeUrl)
        episodeId = resultSet[2]
        programTitle = resultSet[3]
        episodeTitle = resultSet[4]
        day = resultSet[5]
        month = resultSet[6]
        month = DateHelper.GetMonthFromName(month, language="nl")
        year = resultSet[7]
        hour = resultSet[8]
        minute = resultSet[9]

        title = episodeTitle
        if programTitle:
            title = "%s - %s" % (programTitle, episodeTitle)

        url = "http://www.538.nl/static/VdaGemistBundle/Feed/xml/idGemist/%s|%s" % (episodeId, episodeUrl)

        item = mediaitem.MediaItem(title, url)
        item.type = 'video'

        item.SetDate(year, month, day, hour, minute, 0)
        item.description = episodeTitle
        item.thumb = thumbUrl
        item.icon = self.icon
        item.complete = False
        return item

    def CreatePageItem(self, resultSet):
        page = chn_class.Channel.CreatePageItem(self, resultSet)
        Logger.Trace(page.url)
        filterValue = self.parentItem.url.replace("http://www.538.nl/gemist/filter/pagina/", "")
        filterValue = filterValue[filterValue.index("/"):]
        page.url = "%s%s" % (page.url, filterValue)
        Logger.Trace(page.url)
        return page

    def UpdateLiveStream(self, item):
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

        part = item.CreateNewEmptyMediaPart()
        for s, b in M3u8.GetStreamsFromM3u8(item.url, self.proxy):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)

        item.complete = True
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

        rssUrl, htmlUrl = item.url.split("|", 1)

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.Open(rssUrl, proxy=self.proxy)
        item.MediaItemParts = []
        i = 1
        found = False
        for part in Regexer.DoRegex(self.mediaUrlRegex, data):
            found = True
            name = "%s - Deel %s" % (item.name, i)
            mediaPart = mediaitem.MediaItemPart(name, part, 128)
            item.MediaItemParts.append(mediaPart)
            i += 1

        if not found:
            data = UriHandler.Open(htmlUrl, proxy=self.proxy)
            for mediaUrl in Regexer.DoRegex('<meta property="og:video"[^>]+content="([^"]+)" />', data):
                item.AppendSingleStream(mediaUrl, 128)

        item.complete = True
        return item
