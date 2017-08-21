# coding:UTF-8
import datetime
import sys

# import contextmenu
import chn_class
import mediaitem
from parserdata import ParserData
from helpers.datehelper import DateHelper
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.subtitlehelper import SubtitleHelper
from streams.m3u8 import M3u8
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper
from regexer import Regexer
from logger import Logger


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
        self.useAtom = False  # : The atom feeds just do not give all videos
        self.noImage = "nrknoimage.png"

        # setup the urls
        self.mainListUri = "#mainlist"
        self.baseUrl = "https://tvapi.nrk.no/v1"
        self.httpHeaders["app-version-android"] = "999"

        #self.swfUrl = "%s/public/swf/video/svtplayer-2013.23.swf" % (self.baseUrl,)

        self._AddDataParser(self.mainListUri, preprocessor=self.CreateMainList)
        self._AddDataParser("https://tvapi.nrk.no/v1/categories/",
                            matchType=ParserData.MatchExact, json=True,
                            parser=(), creator=self.CreateCategory)

        self._AddDataParser("https://tvapi.nrk.no/v1/categories/.+",
                            matchType=ParserData.MatchRegex, json=True,
                            parser=(), creator=self.CreateProgramFolder)
        self._AddDataParser("https://tvapi.nrk.no/v1/categories/.+",
                            matchType=ParserData.MatchRegex, json=True,
                            parser=(), creator=self.CreateCategoryVideo)

        self._AddDataParser("https://tvapi.nrk.no/v1/channels", json=True,
                            parser=(),
                            creator=self.CreateLiveChannel)
        self._AddDataParser("https://tvapi.nrk.no/v1/programs/", json=True, matchType=ParserData.MatchExact,
                            parser=(),
                            creator=self.CreateProgramFolder)

        self._AddDataParser("https://tvapi.nrk.no/v1/series/[^/]+", json=True, matchType=ParserData.MatchRegex,
                            name="Default Series parser",
                            parser=("programs", ),
                            creator=self.CreateCategoryVideo)

        self._AddDataParser("https://tvapi.nrk.no/v1/categories/all-programs/", json=True,
                            parser=(),
                            creator=self.CreateCategoryVideo)

        self._AddDataParser("https://tvapi.nrk.no/v1/search/indexelements", json=True,
                            name="Main Searchable Index items",
                            parser=(),
                            creator=self.CreateIndexedItem)

        self._AddDataParser("*", updater=self.UpdateVideoItem)

        # ==============================================================================================================
        # non standard items
        self.__metaDataIndexCategory = "category_id"

        # ==============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateMainList(self, data):
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

        links = {
            "Live streams": "https://tvapi.nrk.no/v1/channels",
            "Recommended": "https://tvapi.nrk.no/v1/categories/all-programs/recommendedprograms",
            "Popular": "https://tvapi.nrk.no/v1/categories/all-programs/popularprograms",
            "Recent": "https://tvapi.nrk.no/v1/categories/all-programs/recentlysentprograms",
            "Categories": "https://tvapi.nrk.no/v1/categories/",
            # The other Programs url stopped working. This the next best thing.
            # "Programs": "http://m.nrk.no/tvapi/v1/series/",
            "Programs": "https://tvapi.nrk.no/v1/programs/",
            "A - Å": "https://tvapi.nrk.no/v1/search/indexelements"
        }
        for name, url in links.iteritems():
            item = mediaitem.MediaItem(name, url)
            item.icon = self.icon
            item.thumb = self.noImage
            item.complete = True
            item.HttpHeaders = self.httpHeaders
            items.append(item)

        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateLiveChannel(self, resultSet):
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

        channelId = resultSet["channelId"]
        title = resultSet["title"]
        if "mediaUrl" not in resultSet:
            Logger.Warning("Found channel without media url: %s", title)
            return None

        # url = resultSet["mediaUrl"]
        url = "https://psapi-ne.nrk.no/mediaelement/%s" % (channelId, )
        item = mediaitem.MediaItem(title, url)
        item.type = 'video'
        item.isLive = True
        item.HttpHeaders = self.httpHeaders

        thumbId = resultSet.get("imageId", None)
        if thumbId is not None:
            item.thumb = "http://m.nrk.no/img?kaleidoId=%s&width=720" % (thumbId, )
        item.icon = self.icon
        item.complete = False
        return item

    def CreateCategory(self, resultSet):
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

        title = resultSet["displayValue"]
        # url = "%s/categories/%s/programs" % (self.baseUrl, resultSet["categoryId"], )
        url = "https://tvapi.nrk.no/v1/search/indexelements"
        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.type = 'folder'
        item.fanart = self.fanart
        item.HttpHeaders = self.httpHeaders
        item.metaData[self.__metaDataIndexCategory] = resultSet["categoryId"]

        item.thumb = self.noImage
        item.fanart = self.fanart
        return item

    def CreateIndexedItem(self, resultSet):
        if "seriesId" in resultSet:
            return self.CreateProgramFolder(resultSet)

        # elif "programId" in resultSet:
        #     item = mediaitem.MediaItem(resultSet["title"], "https://tvapi.nrk.no/v1/programs/%s/" % (resultSet["programId"]))
        #     item.type = "video"
        #     imageId = resultSet.get("imageId")
        #     if imageId:
        #         item.thumb = "http://m.nrk.no/img?kaleidoId=%s&width=720" % (imageId,)
        #         item.fanart = "http://m.nrk.no/img?kaleidoId=%s&width=1280" % (imageId,)
        #     item.complete = False
        #     item.HttpHeaders = self.httpHeaders
        #     return item
        return None

    def CreateProgramFolder(self, resultSet):
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
        title = resultSet["title"]
        seriesId = resultSet.get("seriesId")
        if seriesId is None:
            return None

        categoryId = resultSet.get("categoryId", None)
        parentCategoryId = self.parentItem.metaData.get(self.__metaDataIndexCategory, None)
        if parentCategoryId is not None and parentCategoryId != categoryId:
            return None

        item = mediaitem.MediaItem(title, "%s/series/%s" % (self.baseUrl, seriesId))
        item.icon = self.icon
        item.type = 'folder'
        item.fanart = self.fanart
        item.description = resultSet.get("description", "")
        item.HttpHeaders = self.httpHeaders

        imageId = resultSet.get("seriesImageId", None)
        if imageId is not None:
            item.thumb = "http://m.nrk.no/img?kaleidoId=%s&width=720" % (imageId, )
            item.fanart = "http://m.nrk.no/img?kaleidoId=%s&width=1280" % (imageId, )

        if "usageRights" in resultSet:
            item.isGeoLocked = resultSet["usageRights"].get("geoblocked", False)
            if "availableFrom" in resultSet["usageRights"]:
                timeStamp = int(resultSet["usageRights"]["availableFrom"]) / 1000
                if 0 < timeStamp < sys.maxint:
                    date = DateHelper.GetDateFromPosix(timeStamp)
                    item.SetDate(date.year, date.month, date.day, date.hour, date.minute, date.second)
        return item

    def CreateCategoryVideo(self, resultSet):
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

        title = resultSet["title"]

        if not resultSet['isAvailable']:
            Logger.Trace("Found unavailable video: %s", title)
            return None

        episodeData = resultSet.get("episodeNumberOrDate", None)
        season = None
        episode = None
        if episodeData is not None and ":" in episodeData:
            episodeData = episodeData.split(":", 1)
            season = int(episodeData[0])
            episode = int(episodeData[1])
            title = "%s - %02d:%02d" % (title, season, episode)

        url = resultSet.get("mediaUrl", None)
        if url is None:
            url = resultSet.get("programId", None)
            if url is None:
                return None
            url = "%s/programs/%s" % (self.baseUrl, url)

        item = mediaitem.MediaItem(title, url)
        item.description = resultSet.get("description", "")
        item.icon = self.icon
        item.type = 'video'
        item.fanart = self.parentItem.fanart
        item.HttpHeaders = self.httpHeaders

        if season is not None and episode is not None:
            item.SetSeasonInfo(season, episode)

        imageId = resultSet.get("imageId", None)
        if imageId is not None:
            item.thumb = "http://m.nrk.no/img?kaleidoId=%s&width=720" % (imageId, )

        fanartId = resultSet.get("seriesImageId", None)
        if fanartId is not None:
            item.fanart = "http://m.nrk.no/img?kaleidoId=%s&width=1280" % (fanartId, )

        dateSet = False
        if episodeData is not None and ". " in episodeData:
            episodeData = episodeData.split(" ", 2)
            day = episodeData[0].strip(".")
            monthName = episodeData[1]
            month = DateHelper.GetMonthFromName(monthName, "no", short=False)
            year = episodeData[2]
            item.SetDate(year, month, day)
            dateSet = True

        if "usageRights" in resultSet:
            item.isGeoLocked = resultSet["usageRights"].get("geoblocked", False)
            if not dateSet and "availableFrom" in resultSet["usageRights"]:
                timeStamp = int(resultSet["usageRights"]["availableFrom"]) / 1000
                if 0 < timeStamp < sys.maxint:
                    date = DateHelper.GetDateFromPosix(timeStamp)
                    item.SetDate(date.year, date.month, date.day, date.hour, date.minute, date.second)

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
        url = item.url

        if self.localIP:
            item.HttpHeaders.update(self.localIP)

        if ".m3u8" not in item.url:
            data = UriHandler.Open(url, proxy=self.proxy, additionalHeaders=item.HttpHeaders)
            json = JsonHelper(data)
            url = json.GetValue("mediaUrl")
            if url is None:
                Logger.Warning("Could not find mediaUrl in %s", item.url)
                return
            f4mNeedle = "/manifest.f4m"
            if f4mNeedle in url:
                Logger.Info("Found F4m stream. Converting to M3u8.")
                url = url[:url.index(f4mNeedle)].replace("/z/", "/i/").replace("http:", "https:")
                url = "%s/master.m3u8" % (url, )

        # are there subs? They are added as URL parameter

        part = item.CreateNewEmptyMediaPart()
        subMatches = Regexer.DoRegex('https*%3a%2f%2.+master.m3u8', url)
        if subMatches:
            subUrl = HtmlEntityHelper.UrlDecode(subMatches[0])
            Logger.Info("Item has subtitles: %s", subUrl)
            subTitle = SubtitleHelper.DownloadSubtitle(subUrl, format="m3u8srt", proxy=self.proxy)
            if subTitle:
                part.Subtitle = subTitle

        for s, b in M3u8.GetStreamsFromM3u8(url, self.proxy, headers=item.HttpHeaders):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)
            if self.localIP:
                part.HttpHeaders.update(self.localIP)

        return item

    def __GetDate(self, first, second, third):
        """ Tries to parse formats for dates like "Today 9:00" or "mon 9 jun" or "Tonight 9.00"

        @param first: First part
        @param second: Second part
        @param third: Third part

        @return:  a tuple containing: year, month, day, hour, minutes
        """

        Logger.Trace("Determining date for: ('%s', '%s', '%s')", first, second, third)
        hour = minutes = 0

        year = DateHelper.ThisYear()
        if first.lower() == "idag" or first.lower() == "ikv&auml;ll":  # Today or Tonight
            date = datetime.datetime.now()
            month = date.month
            day = date.day
            hour = second
            minutes = third

        elif first.lower() == "ig&aring;r":  # Yesterday
            date = datetime.datetime.now() - datetime.timedelta(1)
            month = date.month
            day = date.day
            hour = second
            minutes = third

        elif second.isdigit():
            day = int(second)
            month = DateHelper.GetMonthFromName(third, "se")
            year = DateHelper.ThisYear()

            # if the date was in the future, it must have been last year.
            result = datetime.datetime(year, month, day)
            if result > datetime.datetime.now() + datetime.timedelta(1):
                Logger.Trace("Found future date, setting it to one year earlier.")
                year -= 1

        elif first.isdigit() and third.isdigit() and not second.isdigit():
            day = int(first)
            month = DateHelper.GetMonthFromName(second, "se")
            year = int(third)

        else:
            Logger.Warning("Unknonw date format: ('%s', '%s', '%s')", first, second, third)
            year = month = day = hour = minutes = 0

        return year, month, day, hour, minutes

#     @GET("/system/isAddressNorwegian?withIp=true")
#     <T> IpCheck checkMyIp();
#
#     @GET("/search/autocomplete/{query}")
#     <T> void getAutoComplete(@Path("query") String str, @Query("viewerAgeLimit") int i, Callback<T> callback);
#
#     @GET("/categories")
#     <T> void getCategories(Callback<T> callback);
#
#     @GET("/channels")
#     <T> List<Channel> getChannels();
#
#     @GET("/channels")
#     <T> void getChannels(Callback<T> callback);
#
#     @GET("/series/{seriesId}/currentprogram")
#     <T> void getCurrentProgramForSeries(@Path("seriesId") String str, @Query("viewerAgeLimit") int i, Callback<T> callback);
#
#     @GET("/series/{seriesId}/currentprogram")
#     <T> void getCurrentProgramForSeries(@Path("seriesId") String str, Callback<T> callback);
#
#     @GET("/channels/epg")
#     <T> void getEpg(@Query("date") String str, Callback<T> callback);
#
#     @GET("/search/{query}")
#     <T> void getForSearchPrograms(@Path("query") String str, Callback<T> callback);
#
#     @GET("/search/indexelements")
#     <T> List<ProgramTeaser> getIndexElements();
#
#     @POST("/series/newepisodes")
#     <T> void getNewEpisodesForSeries(@Body SeriesLastSeen[] seriesLastSeenArr, Callback<T> callback);
#
#     @GET("/programs/{programId}/nextepisode")
#     <T> void getNextEpisode(@Path("programId") String str, @Query("viewerAgeLimit") int i, Callback<T> callback);
#
#     @GET("/programs/{programId}")
#     <T> void getProgram(@Path("programId") String str, @Query("viewerAgeLimit") int i, Callback<Program> callback);
#
#     @GET("/programs/{programId}")
#     <T> void getProgram(@Path("programId") String str, Callback<Program> callback);
#
#     @GET("/categories/{categoryId}/programs")
#     <T> void getProgramByCategoryFeed(@Path("categoryId") String str, Callback<T> callback);
#
#     @GET("/categories/{categoryId}/popularprograms")
#     <T> void getProgramByCategoryPopular(@Path("categoryId") String str, Callback<T> callback);
#
#     @GET("/categories/{categoryId}/recentlysentprograms")
#     <T> void getProgramByCategoryRecent(@Path("categoryId") String str, Callback<T> callback);
#
#     @GET("/categories/{categoryId}/recommendedprograms")
#     <T> void getProgramByCategoryRecommended(@Path("categoryId") String str, Callback<T> callback);
#
#     @GET("/programs")
#     <T> List<ProgramTeaser> getProgramFeed();
#
#     @GET("/programs")
#     <T> void getProgramFeed(Callback<T> callback);
#
#     @GET("/programs/{programId}")
#     <T> ProgramTeaser getProgramTeaser(@Path("programId") String str);
#
#     @POST("/programs")
#     <T> List<ProgramTeaser> getProgramTeaserByIdList(@Body String[] strArr);
#
#     @POST("/programs")
#     <T> void getProgramTeaserByIdList(@Body String[] strArr, Callback<T> callback);
#
#     @POST("/programs")
#     List<ProgramTeaser> getProgramTeaserByIdListSynchronous(@Body String[] strArr);
#
#     @GET("/categories/barn/programs")
#     <T> void getSuperFeed(Callback<T> callback);
