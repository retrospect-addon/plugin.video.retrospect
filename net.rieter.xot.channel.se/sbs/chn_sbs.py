# coding:UTF-8
import datetime

#===============================================================================
# Make global object available
#===============================================================================
from helpers.jsonhelper import JsonHelper
import mediaitem
#import contextmenu
import chn_class

from regexer import Regexer
from parserdata import ParserData
from helpers import subtitlehelper
from helpers.datehelper import DateHelper
# from addonsettings import AddonSettings


from logger import Logger
from urihandler import UriHandler


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
        # setup the urls
        #  See: http://www.kanal5play.se/api
        # self.mainListApi = "/getMobileFindProgramsContent"
        self.mainListApi = "/listPrograms"

        if self.channelCode == "tv5json":
            self.baseUrl = "http://www.kanal5play.se"
            # self.mainListUri = "http://www.kanal5play.se/api/listPrograms?format=ALL_MOBILE&channel=KANAL5"
            # self.mainListUri = "http://kanal5swe.appspot.com/api/getMobileFindProgramsContent?format=ALL_MOBILE&channel=KANAL5"
            self.mainListUri = "http://kanal5swe.appspot.com/api%s?format=ALL_MOBILE&channel=KANAL5" % (self.mainListApi,)
            self.noImage = "tv5seimage.png"
            self.swfUrl = "http://www.kanal5play.se/flash/K5StandardPlayer.swf"

        elif self.channelCode == "tv9json":
            self.baseUrl = "http://www.kanal9play.se"
            # self.mainListUri = "http://www.kanal9play.se/api/listPrograms?format=ALL_MOBILE&channel=KANAL9"
            # self.mainListUri = "http://kanal5swe.appspot.com/api/getMobileFindProgramsContent?format=ALL_MOBILE&channel=KANAL9"
            self.mainListUri = "http://kanal5swe.appspot.com/api%s?format=ALL_MOBILE&channel=KANAL9" % (self.mainListApi,)
            self.noImage = "tv9seimage.png"
            self.swfUrl = "http://www.kanal9play.se/flash/K9StandardPlayer.swf"

        elif self.channelCode == "tv11json":
            self.baseUrl = "http://www.kanal11play.se"
            # self.mainListUri = "http://www.kanal11play.se/api/listPrograms?format=ALL_MOBILE&channel=KANAL11"
            # self.mainListUri = "http://kanal5swe.appspot.com/api/getMobileFindProgramsContent?format=ALL_MOBILE&channel=KANAL11"
            self.mainListUri = "http://kanal5swe.appspot.com/api%s?format=ALL_MOBILE&channel=KANAL11" % (self.mainListApi,)
            self.noImage = "tv11seimage.jpg"
            self.swfUrl = "http://www.kanal11play.se/flash/K11StandardPlayer.swf"

        else:
            raise NotImplementedError("ChannelCode %s is not implemented" % (self.channelCode, ))

        # setup the main parsing data
        # we are going to use the new Json interface here
        # self.episodeItemJson = ('programsWithTemperatures',)
        self.episodeItemJson = ()
        self._AddDataParser(self.mainListUri, json=True, matchType=ParserData.MatchExact,
                            preprocessor=self.AddRecent,
                            parser=self.episodeItemJson, creator=self.CreateEpisodeItem)

        self.videoItemJson = ('episodes',)
        self._AddDataParser("*", json=True,
                            parser=self.videoItemJson, creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        # self._AddDataParser("api/listVideos", matchType=ParserData.MatchContains, json=True,
        #                     parser=(), creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        self.newVideoItemJson = ('newEpisodeVideos',)
        self._AddDataParser("api/getMobileStartContent", matchType=ParserData.MatchContains, json=True,
                            parser=self.newVideoItemJson, creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        self._AddDataParser("/rss?type=", matchType=ParserData.MatchContains,
                            parser=Regexer.FromExpresso("<title>(?<title>[^<]+)</title>\W+<link>[^<]+/(?<url>\d+)</link>\W+<description>(?<description>[^<]+)</description>\W+<pubDate>\w+, (?<day>\d+) (?<month>\w+) (?<year>\d+) (?<hours>\d+):(?<minutes>\d+):(?<seconds>\d+)[^<]+</pubDate>"),
                            creator=self.CreateRssItem)

        #===============================================================================================================
        # non standard items
        self.program = None
        self.avsnitt = None

        #===============================================================================================================
        # Test cases:
        #  Arga snickaren : Has clips

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateEpisodeItem(self, resultSet):
        """Creates a MediaItem of type 'page' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(string) - the resultSet of the self.pageNavigationRegex

        Returns:
        A new MediaItem of type 'page'

        This method creates a new MediaItem from the Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        # the resultSet already was in the Json format.
        if "program" in resultSet:
            data = resultSet["program"]
        else:
            data = resultSet
        Logger.Trace(data)

        description = data.get("description", "")
        thumbUrl = data.get("photoWithLogoUrl", "")  # .get("key", default)
        name = data["name"]
        premium = data["premium"]
        programId = data["id"]
        availableAbroad = data.get("availableAbroad", True)

        url = "http://kanal5swe.appspot.com/api/getMobileProgramContent?format=ALL_MOBILE&programId=%s" % (programId,)

        # do not show premium only content
        if premium:
            #name = "%s [Premium-innehåll]" % (name,)
            return None

        item = mediaitem.MediaItem(name, url)
        item.thumb = thumbUrl
        item.type = "folder"
        item.complete = True
        item.description = description
        item.fanart = self.fanart
        item.isGeoLocked = not availableAbroad

        # see if we can find seasons
        if "seasonNumbersWithContent" not in data:
            return None

        for season in data['seasonNumbersWithContent']:
            title = "%s - Säsong %s" % (name, season,)
            seasonUrl = "http://kanal5swe.appspot.com/api/getMobileSeasonContent?format=ALL_MOBILE&programId=%s&seasonNumber=%s" % (programId, season)
            season = mediaitem.MediaItem(title, seasonUrl)
            season.thumb = thumbUrl
            season.fanart = self.fanart
            season.complete = True
            season.isGeoLocked = not availableAbroad
            item.items.append(season)

        return item

    def AddRecent(self, data):
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

        items = []

        # http://kanal5swe.appspot.com/api/getMobileStartContent?format=ALL_MOBILE&channel=KANAL9
        extras = {
            # "\a.: Senaste avsnitten via RSS :.": "%s/rss?type=PROGRAM" % (self.baseUrl, ),
            # "\a.: Senaste clip via RSS :.": "%s/rss?type=CLIP" % (self.baseUrl, ),
            # "\a.: Senaste avsnitten :.": "http://kanal5swe.appspot.com/api/getMobileStartContent?format=ALL_MOBILE&channel=KANAL5",
            "\a.: Senaste avsnitten :.": self.mainListUri.replace(self.mainListApi, "/getMobileStartContent"),
            # "\a.: Senaste avsnitten (All Video) :.": self.mainListUri.replace(self.mainListApi, "/listVideos"),
        }
        for (k, v) in extras.iteritems():
            item = mediaitem.MediaItem(k, v)
            item.thumb = self.noImage
            item.complete = True
            item.icon = self.icon
            item.dontGroup = True
            if "/getMobileStartContent" in item.url:
                item.isGeoLocked = True
            items.append(item)

        return data, items

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

        if self.channelCode == "tv5" or self.channelCode == "tv9":
            # get the title of the program in season
            results = Regexer.DoRegex('<h1[^>]*>([^<]+)</h1>', data)
            for result in results:
                self.program = result

        Logger.Debug("Pre-Processing finished")
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

        Logger.Trace(resultSet)

        if resultSet[0] == 0:
            # first regex match
            url = "%s/content/%s" % (self.baseUrl, resultSet[2])
            name = resultSet[1]
        else:
            # second regex match
            url = "%s/content/%s" % (self.baseUrl, resultSet[1])
            name = resultSet[2]

        item = mediaitem.MediaItem("%s - %s" % (name, self.program), url)
        item.thumb = self.noImage
        item.type = "folder"
        item.complete = True
        item.fanart = self.fanart
        return item

    def CreatePageItem(self, resultSet):
        """Creates a MediaItem of type 'page' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(string) - the resultSet of the self.pageNavigationRegex

        Returns:
        A new MediaItem of type 'page'

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        total = ''

        for result in resultSet:
            total = "%s%s" % (total, result)

        #total = htmlentityhelper.HtmlEntityHelper.StripAmp(total)

        item = mediaitem.MediaItem(resultSet[1], "%s/content%s%s" % (self.baseUrl, resultSet[0], resultSet[1]))

        item.type = "page"
        Logger.Trace("Created '%s' for url %s", item.name, item.url)
        return item

    def CreateRssItem(self, resultSet):
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

        item = chn_class.Channel.CreateVideoItem(self, resultSet)
        month = DateHelper.GetMonthFromName(resultSet["month"], language="en")
        item.SetDate(resultSet["year"], month, resultSet["day"],
                     resultSet["hours"], resultSet["minutes"], resultSet["seconds"])
        item.url = "http://kanal5swe.appspot.com/api/getVideo?videoId=%(url)s&format=ALL_MOBILE" % resultSet

        # http://kanal5swe.appspot.com/api/getVideo?videoId=342011&format=ALL_MOBILE
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

        # data = "%s%s" % (resultSet[0], resultSet[1])
        data = resultSet

        # basic info
        name = data["episodeText"]
        videoId = data["id"]
        thumbUrl = data["posterUrl"]
        description = data["description"]
        premium = data["premium"]
        program = data["program"]["name"]
        isGeoLocked = not data["program"]["availableAbroad"]
        requiresWideVine = data.get("widevineRequired", False)

        if premium:
            # Premium was set and True
            Logger.Debug("Premium item '%s' found", name)
            return None

        # url = "http://www.kanal5play.se/api/getVideo?format=FLASH&videoId=%s" % (videoId, )
        url = "http://www.kanal9play.se/api/getVideo?format=FLASH&videoId=%s" % (videoId,)

        item = mediaitem.MediaItem("%s - %s" % (program, name), url)
        item.description = description
        item.thumb = thumbUrl
        item.type = "video"
        item.complete = False
        item.icon = self.icon
        item.fanart = self.fanart
        item.isDrmProtected = requiresWideVine
        item.isGeoLocked = isGeoLocked

        if "shownOnTvDateTimestamp" in data:
            timeStamp = data["shownOnTvDateTimestamp"]  # milli seconds since epoch
            timeStamp = int(timeStamp) / 1000
            date = datetime.datetime.fromtimestamp(timeStamp)
            item.SetDate(date.year, date.month, date.day, date.hour, date.minute, date.second)

        part = item.CreateNewEmptyMediaPart()
        self.__FindStreamData(data, videoId, part)

        if len(part.MediaStreams) == 0:
            item.MediaItemParts = []
            item.complete = False
            #item.name = "%s [No streams]" % (item.name,)
        else:
            # we need to fetch subtitles
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

        # http://www.kanal5play.se/api/subtitles/298903
        if len(item.MediaItemParts) == 0:
            Logger.Debug("No media info found, trying to determine it based on video ID")
            data = UriHandler.Open(item.url, proxy=self.proxy)
            data = JsonHelper(data)
            data = data.GetValue()

            part = item.CreateNewEmptyMediaPart()
            videoId = data["id"]

            self.__FindStreamData(data, videoId, part)

        if len(item.MediaItemParts) > 0:
            part = item.MediaItemParts[0]
            Logger.Trace("Fetching subtitle from %s", part.Subtitle)
            if part.Subtitle.startswith(self.baseUrl):
                part.Subtitle = subtitlehelper.SubtitleHelper.DownloadSubtitle(part.Subtitle, format="json", proxy=self.proxy)

        item.complete = True
        return item

    def __FindStreamData(self, data, videoId, part):
        """ Retrieves stream data from the JSON objects and updates the MediaItemPart with the stream data. It also
        determines the subtitle url and sets it.

        @param data:        Json data object
        @param videoId:     The VideoID for this video
        @param part:        The MediaItemPart to update
        @return:            Nothing, the MediaItemPart is updated by reference.

        """

        part.Subtitle = "%s/api/subtitles/%s" % (self.baseUrl, videoId)

        baseUrl = data.get("streamBaseUrl", None)
        for stream in data.get("streams", []):
            drm = stream['drmProtected']
            if drm:
                # skip drm
                continue

            if 'bitrate' in stream:
                bitrate = int(stream['bitrate']) / 1000
            else:
                # audio only in XBMC
                continue

            url = stream['source']
            if "rtsp:" in url:
                # audio only in XBMC
                continue
            elif "://" not in url:
                if baseUrl is None:
                    # some cases the BaseUrl is missing for RTMP, we can't do anything then
                    continue
                url = "%s?slist=/%s.%s" % (baseUrl, url[4:], url[0:3])
                url = self.GetVerifiableVideoUrl(url)
                # if url.startswith("rtmp"):
                #     # SBS changed something and the live=1 might be required.
                #     url = "%s live=1" % (url, )
                #     # part.AddProperty("IsLive", "true")

            part.AppendMediaStream(url, bitrate)
            # Logger.Trace(stream)
        return
