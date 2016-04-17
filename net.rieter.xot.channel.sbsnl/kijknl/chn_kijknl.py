import mediaitem
import chn_class

from regexer import Regexer
from streams.brightcove import BrightCove
from streams.m3u8 import M3u8

from parserdata import ParserData
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
        # setup the urls
        self.baseUrl = "http://www.kijk.nl"
        # Just retrieve a single page with 200 items (should be all)
        self.mainListUri = "http://www.kijk.nl/ajax/section/overview/programs-abc-ABCDEFGHIJKLMNOPQRSTUVWXYZ/1/200"

        channelId = None
        if self.channelCode == 'veronica':
            self.noImage = "veronicaimage.png"
            channelId = "veronicatv"

        elif self.channelCode == 'sbs':
            self.noImage = "sbs6image.png"
            channelId = "sbs6"

        elif self.channelCode == 'sbs9':
            self.noImage = "sbs9image.png"

        elif self.channelCode == 'net5':
            self.noImage = "net5image.png"

        # setup the main parsing data
        self.episodeItemRegex = 'data-srchd="(?<thumburl>[^"]+)"[^>]*>\W*<noscript>\W*<img[^>]*>\W*</noscript>[\w\W]' \
                                '{0,750}?data-itemid="[^"]+\.%s"[^>]*data-title="(?<title>[^"]+)"></div>\W+</div>' \
                                '\W+</a>\W+<a href="(?<url>[^"]+)"[^>]+>\W+<div class="info[^>]*>\W+<h3[\w\W]{0,1500}' \
                                '?<p class="meta" itemprop="description">(?<description>[^<]+)'\
                                .replace("(?<", "(?P<") \
                                % (channelId or self.channelCode,)
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            parser=self.episodeItemRegex, creator=self.CreateEpisodeItem)

        # normal video items
        self.videoItemRegex = 'data-srchd="(?<thumburl>[^"]+)"[^>]* alt="(?<title>[^"]+)"[^>]*>[\w\W]{0,2000}?' \
                              'itemprop="datePublished" content="(?<date>[^"]+)[\w\W]{0,1000}itemprop="description">' \
                              '(?<description>[^<]+)<a href="(?<url>[^"]+)/[^"]+"'\
                              .replace("(?<", "(?P<")
        self._AddDataParser("*", parser=self.videoItemRegex, creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        # ajax video items
        self.ajaxItemRegex = '<img src="(?<thumburl>[^"]+)"[^>]* itemprop="thumbnailUrl"[^>]*>\W*</noscript>[\w\W]' \
                             '{0,1000}?data-title="(?<title>[^"]+)">\W*</div>\W*</div>\W*</a>\W*<a[^>]+href="' \
                             '(?<url>[^"]+)/[^"]+"[^>]+\W+<div[^>]+>\W+<(?:div class="desc[^>]+|h3[^>]*)>' \
                             '(?<description>[^<]+)[\W\w]{0,400}?<div class="airdate[^>]+?(?:content="' \
                             '(?<date>[^"]+)"|>)'.replace("(?<", "(?P<")
        self._AddDataParser("http://www.kijk.nl/ajax/section/series/",
                            parser=self.ajaxItemRegex, creator=self.CreateVideoItem)

        # folders
        self.folderItemRegex = ['(?<type>\w+)</h2>\W*<div[^>]+class="showcase sidescroll[^>]+'
                                'data-id="(?<url>[^"]+)" [^>]*data-hasmore="1"'
                                .replace("(?<", "(?P<"),
                                '<li[^>]+data-filter="(?<url>[^"]+)">(?<title>[^<]+)</li>'
                                .replace("(?<", "(?P<")]

        # we both need folders in the normal and ajax pages.
        self._AddDataParser("*", parser=self.folderItemRegex, creator=self.CreateFolderItem)
        self._AddDataParser("http://www.kijk.nl/ajax/section/series/",
                            parser=self.folderItemRegex, creator=self.CreateFolderItem)
        self.mediaUrlRegex = '<object id=@"myExperience[\w\W]+?playerKey@" value=@"([^@]+)[\w\W]{0,1000}?videoPlayer@" value=@"(\d+)@"'.replace("@", "\\\\")

        #===============================================================================================================
        # non standard items
        # The main page has 10 items per call, so we need to keep this the same to make sure that
        # we continue at the right number
        self.pageSize = 10

        #===============================================================================================================
        # Test cases:
        #  Piets Weer: no clips
        #  Achter gesloten deuren: seizoenen
        #  Wegmisbruikers: episodes and clips and both pages
        #  Utopia: no clips

        # ====================================== Actual channel setup STOPS here =======================================
        return

    # def PreProcessFolderList(self, data):
    #     """Performs pre-process actions for data processing/
    #
    #     Arguments:
    #     data : string - the retrieve data that was loaded for the current item and URL.
    #
    #     Returns:
    #     A tuple of the data and a list of MediaItems that were generated.
    #
    #
    #     Accepts an data from the ProcessFolderList method, BEFORE the items are
    #     processed. Allows setting of parameters (like title etc) for the channel.
    #     Inside this method the <data> could be changed and additional items can
    #     be created.
    #
    #     The return values should always be instantiated in at least ("", []).
    #
    #     """
    #
    #     Logger.Info("Performing Pre-Processing")
    #     items = []
    #
    #     dataStart = data.find('<h2 class="showcase-heading">')
    #     # end = data.find('_SerieSeasonSlider"')
    #     end = data.find('</li></ul></div><div')
    #     if end > 0:
    #         end += 20  # we want the </li> in case we found it
    #     resultData = data[dataStart:end]
    #
    #     # Add a Clips item
    #     # if "_Clips" in self.parentItem.url:
    #     #     # self.CreateVideoItem = self.CreateClipItem
    #     #     Logger.Trace("Switching to CLIPS regex")
    #     #     self.videoItemRegex = self.clipItemRegex
    #
    #     Logger.Debug("Pre-Processing finished")
    #     return resultData, items

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

        Logger.Trace(resultSet)
        matchedRegex = resultSet[0]
        resultSet = resultSet[1]

        if matchedRegex == 0:
            #  Main regex match for the More Clips/Episodes
            folderId = resultSet["url"]
            folderType = resultSet["type"]

            # http://www.kijk.nl/ajax/qw/moreepisodes?format=wegmisbruikers&page=1&season=0&station=sbs6
            if "ajax" in self.parentItem.url:
                # for ajax pages determine the next one and it's always a clip list or episode list
                folderNumber = int(self.parentItem.url.split("/")[-2])
                folderNumber += 1
                if "clip" in self.parentItem.url.lower():
                    title = "\bMeer clips"
                else:
                    title = "\bMeer afleveringen"

            elif "clip" in folderType.lower():
                # default clip start page = 1
                title = "\bClips"
                folderNumber = 1
            else:
                # default more episode page = 2
                title = "\bMeer afleveringen"
                folderNumber = 2

            url = "http://www.kijk.nl/ajax/section/series/%s/%s/%s" % (folderId, folderNumber, self.pageSize)

        elif matchedRegex == 1:
            # match for the Seasons on the main pages.
            if "ajax" in self.parentItem.url:
                # don't add then om Ajax call backs, only on main listing
                return None

            title = resultSet["title"]
            url = resultSet["url"]
            url = "http://www.kijk.nl/ajax/section/series/%s/1/%s" % (url, self.pageSize)
        else:
            Logger.Error("Unmatched multi regex match")
            return None

        item = mediaitem.MediaItem(title, url)
        item.thumb = self.noImage
        item.icon = self.icon
        item.type = 'folder'
        item.complete = True
        Logger.Trace(item)
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

        # {
        # 	'url': u'/sbs6/wegmisbruikers/videos/3dvYeP523cBh/aflevering-291',
        # 	'date': u'2014-09-28T20: 30: 00+02: 00',
        # 	'thumburl': u'http: //img.kijk.nl/media/cache/computer_retina_series_image/imgsrc01/data/image/50/sbs_media_image/2014.09/2715946859---20140928230130--0a58093311238a3cbbc49917bde98fab.jpg',
        # 	'description': u'Aflevering291',
        # 	'title': u'Aflevering291'
        # }

        url = resultSet['url']
        if "http://" not in url:
            url = "%s%s" % (self.baseUrl, url)
        Logger.Trace(url)

        item = mediaitem.MediaItem(resultSet['title'], url)
        item.type = 'video'
        if "description" in resultSet:
            item.description = resultSet['description']
        item.thumb = resultSet['thumburl']
        item.icon = self.icon

        date = resultSet["date"]
        if date:
            dateStamp = date.split("T")
            Logger.Trace(dateStamp)
            datePart = dateStamp[0]
            timePart = dateStamp[1].split("+")[0]
            (year, month, day) = datePart.split("-")
            (hour, minute, seconds) = timePart.split(":")
            Logger.Trace((year, month, day, hour, minute, seconds))
            item.SetDate(year, month, day, hour, minute, seconds)

        item.complete = False
        Logger.Trace(item)
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

        videoId = item.url[item.url.rfind("/") + 1:]

        url = "http://embed.kijk.nl/?width=868&height=491&video=%s" % (videoId,)
        referer = "http://www.kijk.nl/video/%s" % (videoId,)

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.Open(url, proxy=self.proxy, referer=referer)
        Logger.Trace(self.mediaUrlRegex)
        objectData = Regexer.DoRegex(self.mediaUrlRegex, data)[0]
        Logger.Trace(objectData)

        # seed = "61773bc7479ab4e69a5214f17fd4afd21fe1987a"
        # seed = "0a2b91ec0fdb48c5dd5239d3e796d6f543974c33"
        seed = "0b0234fa8e2435244cdb1603d224bb8a129de5c1"
        amfHelper = BrightCove(Logger.Instance(), str(objectData[0]), str(objectData[1]), url, seed)  # , proxy=ProxyInfo("localhost", 8888)
        item.description = amfHelper.GetDescription()

        part = item.CreateNewEmptyMediaPart()
        for stream, bitrate in amfHelper.GetStreamInfo():
            if "m3u8" in stream:
                for s, b in M3u8.GetStreamsFromM3u8(stream, self.proxy):
                    item.complete = True
                    # s = self.GetVerifiableVideoUrl(s)
                    part.AppendMediaStream(s, b)
            part.AppendMediaStream(stream.replace("&mp4:", ""), bitrate)

        item.complete = True
        return item
