# coding:UTF-8
import datetime

#===============================================================================
# Make global object available
#===============================================================================
from helpers.jsonhelper import JsonHelper
import mediaitem
import chn_class

from helpers.languagehelper import LanguageHelper
from helpers import subtitlehelper
from urihandler import UriHandler
from streams.m3u8 import M3u8
from helpers.htmlentityhelper import HtmlEntityHelper
from parserdata import ParserData
from logger import Logger
from xbmcwrapper import XbmcWrapper


# noinspection PyIncorrectDocstring
class Channel(chn_class.Channel):

    def __init__(self, channelInfo):
        """Initialisation of the class.

        Arguments:
        channelInfo: ChannelInfo - The channel info object to base this channel on.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        """

        chn_class.Channel.__init__(self, channelInfo)

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.mainListUri = "#programs"
        self.programPageSize = 50
        self.videoPageSize = 25
        self.swfUrl = "http://player.dplay.se/4.0.6/swf/AkamaiAdvancedFlowplayerProvider_v3.8.swf"
        self.subtitleKey = "subtitles_se_srt"
        self.channelSlugs = ()
        self.liveUrl = None
        self.recentUrl = None

        if self.channelCode == "tv5json":
            self.noImage = "tv5seimage.png"
            self.baseUrl = "http://www.dplay.se/api/v2/ajax"
            # self.liveUrl = "https://secure.dplay.se/secure/api/v2/user/authorization/stream/132040"
            # self.fanart = "http://a1.res.cloudinary.com/dumrsasw1/image/upload/Kanal5-channel-large_kxf7fn.jpg"
            # Recent URL changes over time. See the 'website -> channel' page
            self.recentUrl = "%s/modules?page_id=132040&module_id=7556&items=%s&page=0"

            # - From the /program/ page (requires slugs for filtering)
            # self.mainListFormat = "%s/modules?page_id=23&module_id=19&items=%s&page=%s"
            # self.channelSlugs = ("kanal-5", "kanal-5-home")
            # - From the /kanal??/ recommended -> fastest and does not require filtering on slugs
            self.mainListFormat = "%s/shows/?items=%s&homechannel_id=48&page=%s&sort=title_asc"

        elif self.channelCode == "tv9json":
            self.noImage = "tv9seimage.png"
            self.baseUrl = "http://www.dplay.se/api/v2/ajax"
            # self.liveUrl = "https://secure.dplay.se/secure/api/v2/user/authorization/stream/132043"
            # self.fanart = "http://a2.res.cloudinary.com/dumrsasw1/image/upload/Thewalkingdead_hqwfz1.jpg"
            self.recentUrl = "%s/modules?page_id=132043&module_id=466&items=%s&page=0"
            # - From the /program/ page (requires slugs for filtering)
            # self.mainListFormat = "%s/modules?page_id=23&module_id=19&items=%s&page=%s"
            # self.channelSlugs = ("kanal-9", "kanal-9-home")
            # - From the /kanal??/ recommended -> fastest and does not require filtering on slugs
            self.mainListFormat = "%s/shows/?items=%s&homechannel_id=52&page=%s&sort=title_asc"

        elif self.channelCode == "tv11json":
            self.noImage = "tv11seimage.jpg"
            self.baseUrl = "http://www.dplay.se/api/v2/ajax"
            # self.liveUrl = "https://secure.dplay.se/secure/api/v2/user/authorization/stream/132039"
            # self.fanart = "http://a3.res.cloudinary.com/dumrsasw1/image/upload/unnamed_v3u5zt.jpg"
            self.recentUrl = "%s/modules?page_id=132039&module_id=470&items=%s&page=0"
            # - From the /program/ page (requires slugs for filtering)
            # self.mainListFormat = "%s/modules?page_id=23&module_id=19&items=%s&page=%s"
            # self.channelSlugs = ("kanal-11", "kanal-11-home")
            # - From the /kanal??/ recommended -> fastest and does not require filtering on slugs
            self.mainListFormat = "%s/shows/?items=%s&homechannel_id=46&page=%s&sort=title_asc"

        # elif self.channelCode == "dplaydk":
        #     self.noImage = ""
        #     self.baseUrl = "http://www.dplay.dk/api/v2/ajax"
        #     self.mainListFormat = "%s/modules?page_id=227&module_id=99&items=%s&page=%s"
        else:
            raise NotImplementedError("ChannelCode %s is not implemented" % (self.channelCode, ))

        #===========================================================================================
        # THIS CHANNEL DOES NOT SEEM TO WORK WITH PROXIES VERY WELL!
        #===========================================================================================
        self._AddDataParser("#programs", preprocessor=self.LoadPrograms)
        self._AddDataParser("https://secure.dplay.\w+/secure/api/v2/user/authorization/stream/",
                            matchType=ParserData.MatchRegex,
                            updater=self.UpdateChannelItem)

        self._AddDataParser("http://www.dplay.se/api/v2/ajax/search/?types=show&items=", json=True,
                            parser=("data", ), creator=self.CreateProgramItem)

        self._AddDataParser("http://www.dplay.se/api/v2/ajax/modules", json=True,
                            parser=("data",), creator=self.CreateVideoItemWithShowTitle,
                            updater=self.UpdateVideoItem)
        self._AddDataParser("*", json=True,
                            parser=("data",), creator=self.CreateVideoItem,
                            updater=self.UpdateVideoItem)
        self._AddDataParser("*", json=True,
                            parser=(), creator=self.CreatePageItem)

        #===========================================================================================
        # non standard items

        #===========================================================================================
        # Test cases:
        #  Arga snickaren : Has clips

        # ====================================== Actual channel setup STOPS here ===================
        return

    # noinspection PyUnusedLocal
    def LoadPrograms(self, data):
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

        # fetch al pages
        currentPage = 0
        url = self.mainListFormat % (self.baseUrl, self.programPageSize, currentPage)
        data = UriHandler.Open(url, proxy=self.proxy)
        json = JsonHelper(data)
        pages = json.GetValue("total_pages")
        programs = json.GetValue("data")

        for p in range(1, pages, 1):
            url = self.mainListFormat % (self.baseUrl, self.programPageSize, p)
            Logger.Debug("Loading: %s", url)
            data = UriHandler.Open(url, proxy=self.proxy)
            json = JsonHelper(data)
            programs += json.GetValue("data")
        Logger.Debug("Found a total of %s items over %s pages", len(programs), pages)

        for p in programs:
            item = self.CreateProgramItem(p)
            if item is not None:
                items.append(item)

        if self.recentUrl:
            url = self.recentUrl % (self.baseUrl, self.videoPageSize)
            recent = mediaitem.MediaItem("\b.: Recent :.", url)
            recent.dontGroup = True
            recent.fanart = self.fanart
            items.append(recent)

        # live items
        if self.liveUrl:
            live = mediaitem.MediaItem("\b.: Live :.", self.liveUrl)
            live.type = "video"
            live.dontGroup = True
            live.isGeoLocked = True
            live.isLive = True
            live.fanart = self.fanart
            items.append(live)

        search = mediaitem.MediaItem("\a.: S&ouml;k :.", "searchSite")
        search.type = "folder"
        search.dontGroup = True
        search.fanart = self.fanart
        items.append(search)

        return data, items

    def CreateProgramItem(self, p):
        """Creates a new MediaItem for a program

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        # Logger.Trace(p)
        name = p["title"]
        # showName = p.get("video_metadata_show", None)
        videoId = None
        channelSlug = None
        homeChannelSlug = None

        # get some meta data
        videoInfos = p["taxonomy_items"]
        for videoInfo in videoInfos:
            if videoInfo["type"] == "show":
                videoId = videoInfo["term_id"]
            elif videoInfo["type"] == "channel":
                channelSlug = videoInfo["slug"]
            elif videoInfo["type"] == "home-channel":
                homeChannelSlug = videoInfo["slug"]

        if videoId is None:
            Logger.Warning("Found '%s' without 'term_id'", name)
            return None

        # Logger.Trace("Found '%s/%s' with id='%s'", showName or "<noShowName>", name, videoId)

        if len(self.channelSlugs) > 0 \
                and channelSlug not in self.channelSlugs \
                and homeChannelSlug not in self.channelSlugs:
            Logger.Debug("Found show '%s' for channel '%s' needed '%s'",
                         name, channelSlug, self.channelSlugs)
            return None

        # now get the items
        url = "%s/shows/%s/seasons/?show_id=%s&items=%s&sort=episode_number_desc&page=0" \
              % (self.baseUrl, videoId, videoId, self.videoPageSize)
        item = mediaitem.MediaItem(name, url)
        item.description = p.get("secondary_title")

        # set the date
        date = p["modified"]
        datePart, timePart = date.split(" ")
        year, month, day = datePart.split("-")
        # hours, minutes, seconds = timePart.split(":")
        # item.SetDate(year, month, day, hours, minutes, seconds)
        item.SetDate(year, month, day)

        # set the images
        thumbId = p["image_data"].get("file", None)
        if thumbId is not None:
            thumb = "http://a1.res.cloudinary.com/dumrsasw1/image/upload/c_crop,h_901,w_1352,x_72,y_1/c_fill,h_245,w_368/%s" % (thumbId, )
            fanart = "http://a1.res.cloudinary.com/dumrsasw1/image/upload/%s" % (thumbId, )
            item.thumb = thumb
            item.fanart = fanart

        item.isPaid = p["content_info"]["package_label"]["value"] != "Free"
        return item

    def CreatePageItem(self, resultSet):
        """Creates a MediaItem of type 'page' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(string) - the resultSet of the self.pageNavigationRegex

        Returns:
        A new MediaItem of type 'page'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.Debug("Starting CreatePageItem")

        # current page?
        baseUrl, page = self.parentItem.url.rsplit("=", 1)
        page = int(page)
        maxPages = resultSet.get("total_pages", 0)
        Logger.Trace("Current Page: %d of %d (%s)", page, maxPages, baseUrl)
        if page + 1 >= maxPages:
            return None

        title = LanguageHelper.GetLocalizedString(LanguageHelper.MorePages)
        url = "%s=%s" % (baseUrl, page + 1)
        item = mediaitem.MediaItem(title, url)
        item.fanart = self.parentItem.fanart
        item.thumb = self.parentItem.thumb
        return item

    def SearchSite(self, url=None):
        """Creates an list of items by searching the site

        Keyword Arguments:
        url : String - Url to use to search with a %s for the search parameters

        Returns:
        A list of MediaItems that should be displayed.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with an URL encoded representation of the
        text to search for.

        """

        # http://www.dplay.se/api/v2/ajax/search/?q=test&items=12&types=video&video_types=episode,live
        # http://www.dplay.se/api/v2/ajax/search/?q=test&items=6&types=show

        needle = XbmcWrapper.ShowKeyBoard()
        if needle:
            Logger.Debug("Searching for '%s'", needle)
            needle = HtmlEntityHelper.UrlEncode(needle)

            url = "http://www.dplay.se/api/v2/ajax/search/?types=video&items=%s" \
                  "&video_types=episode,live&q=%%s&page=0" % (self.videoPageSize, )
            searchUrl = url % (needle, )
            temp = mediaitem.MediaItem("Search", searchUrl)
            episodes = self.ProcessFolderList(temp)

            url = "http://www.dplay.se/api/v2/ajax/search/?types=show&items=%s" \
                  "&q=%%s&page=0" % (self.programPageSize, )
            searchUrl = url % (needle, )
            temp = mediaitem.MediaItem("Search", searchUrl)
            shows = self.ProcessFolderList(temp)
            return shows + episodes

        return []

    def CreateVideoItemWithShowTitle(self, resultSet):
        """Creates a MediaItem with ShowTitle """

        # Logger.Trace(resultSet)
        if not resultSet:
            return None

        title = resultSet["title"]
        showTitle = resultSet.get("video_metadata_show", None)
        if showTitle:
            resultSet["title"] = "%s - %s" % (showTitle, title)
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
        if not resultSet:
            return None

        title = resultSet["title"]
        subtitle = resultSet.get("secondary_title", None)
        season = resultSet.get("season", None)
        episode = resultSet.get("episode", None)
        if not subtitle and season and episode:
            Logger.Debug("Found season (%s) and episode (%s) data", season, episode)

            subtitle = "s%02de%02d" % (int(season), int(episode))
        if subtitle:
            title = "%s - %s" % (title, subtitle)

        # url = resultSet["hls"]
        url = "%s/videos?video_id=%s&page=0&items=500" % (self.baseUrl, resultSet["id"])
        item = mediaitem.MediaItem(title, url)
        item.type = "video"

        item.description = resultSet.get("video_metadata_longDescription", None)
        if not item.description:
            item.description = resultSet.get("description", None)

        item.fanart = self.parentItem.fanart
        item.thumb = resultSet.get("video_metadata_videoStillURL", self.parentItem.thumb)

        # timeStamp = resultSet.get("video_metadata_first_startTime", None)
        timeStamp = resultSet.get("video_metadata_svod_start_time", None)
        if timeStamp:
            timeStamp = int(timeStamp)
            date = datetime.datetime.fromtimestamp(timeStamp)
            item.SetDate(date.year, date.month, date.day, date.hour, date.minute, date.second)

        item.isPaid = "Packages-Free" not in resultSet["video_metadata_package"]

        # not sure if this catches all, but it is a start
        if "open-drm" in resultSet.get("hls", ""):
            item.isGeoLocked = True
        return item

    def UpdateChannelItem(self, item):
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

        videoId = item.url.rsplit("/", 1)[-1]
        part = item.CreateNewEmptyMediaPart()
        item.complete = self.__GetVideoStreams(videoId, part)
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

        videoData = UriHandler.Open(item.url, proxy=self.proxy)

        if not videoData:
            return item

        videoData = JsonHelper(videoData)
        videoInfo = videoData.GetValue("data", 0)

        part = item.CreateNewEmptyMediaPart()
        item.complete = self.__GetVideoStreams(videoInfo["id"], part)

        if len(item.MediaItemParts) > 0:
            part = item.MediaItemParts[0]
            part.Subtitle = videoInfo[self.subtitleKey]
            Logger.Trace("Fetching subtitle from %s", part.Subtitle)
            if part.Subtitle.startswith("http"):
                part.Subtitle = subtitlehelper.SubtitleHelper.DownloadSubtitle(part.Subtitle, format="srt", proxy=self.proxy)

        return item

    def __GetVideoStreams(self, videoId, part):
        """ Fetches the video stream for a given videoId

        @param videoId: (integer) the videoId
        @param part:    (MediaPart) the mediapart to add the streams to
        @return:        (bool) indicating a successfull retrieval

        """

        # hardcoded for now as it does not seem top matter
        dscgeo = '{"countryCode":"%s","expiry":1446917369986}' % (self.language.upper(),)
        dscgeo = HtmlEntityHelper.UrlEncode(dscgeo)
        headers = {"Cookie": "dsc-geo=%s" % (dscgeo, )}

        # send the data
        http, nothing, host, other = self.baseUrl.split("/", 3)
        subdomain, domain = host.split(".", 1)
        url = "https://secure.%s/secure/api/v2/user/authorization/stream/%s?stream_type=hls" \
              % (domain, videoId,)
        data = UriHandler.Open(url, proxy=self.proxy, additionalHeaders=headers, noCache=True)
        json = JsonHelper(data)
        url = json.GetValue("hls")

        if url is None:
            return False

        streamsFound = False
        if "?" in url:
            qs = url.split("?")[-1]
        else:
            qs = None
        for s, b in M3u8.GetStreamsFromM3u8(url, self.proxy):
            # and we need to append the original QueryString
            if "X-I-FRAME-STREAM" in s:
                continue

            streamsFound = True
            if qs is not None:
                if "?" in s:
                    s = "%s&%s" % (s, qs)
                else:
                    s = "%s?%s" % (s, qs)

            part.AppendMediaStream(s, b)

        return streamsFound
