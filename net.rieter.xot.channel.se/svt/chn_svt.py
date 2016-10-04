# coding:UTF-8
import datetime
import time

# import contextmenu
import chn_class
import mediaitem

from regexer import Regexer
from helpers import subtitlehelper
from helpers.jsonhelper import JsonHelper
from helpers.datehelper import DateHelper
from helpers.languagehelper import LanguageHelper
from streams.m3u8 import M3u8

from logger import Logger
from urihandler import UriHandler
from parserdata import ParserData


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
        self.noImage = "svtimage.png"

        # setup the urls
        # self.mainListUri = "http://www.svtplay.se/program"
        self.mainListUri = "http://www.svtplay.se/ajax/sok/forslag.json"
        self.baseUrl = "http://www.svtplay.se"
        self.swfUrl = "http://media.svt.se/swf/video/svtplayer-2016.01.swf"

        # setup the intial listing based on Alphabeth and specials
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
                            preprocessor=self.AddLiveItemsAndGenres)
        # in case we use the program HTML page
        # self._AddDataParser("http://www.svtplay.se/program", matchType=ParserData.MatchExact,
        #                     json=True, preprocessor=self.AddShowItems)
        # in case we use the forslag.json
        self._AddDataParser("http://www.svtplay.se/ajax/sok/forslag.json",
                            matchType=ParserData.MatchExact, json=True,
                            parser=(), creator=self.CreateJsonEpisodeItemSok)

        # setup channel listing based on JSON data
        self._AddDataParser("#kanaler",
                            preprocessor=self.LoadChannelData,
                            json=True,
                            parser=("channels", ),
                            creator=self.CreateChannelItem)

        # special pages (using JSON) using a generic pre-processor to extract the data
        specialJsonPages = "^https?://www.svtplay.se/(senaste|sista-chansen|populara|live)\?sida=\d+$"
        self._AddDataParser(specialJsonPages,
                            matchType=ParserData.MatchRegex, preprocessor=self.ExtractJsonDataRedux)
        self._AddDataParser(specialJsonPages,
                            matchType=ParserData.MatchRegex, json=True,
                            parser=("gridPage", "content"),
                            creator=self.CreateJsonItem)
        self._AddDataParser(specialJsonPages,
                            matchType=ParserData.MatchRegex, json=True,
                            parser=("gridPage", "pagination"),
                            creator=self.CreateJsonPageItem)

        # genres (using JSON)
        self._AddDataParser("http://www.svtplay.se/genre/",
                            preprocessor=self.ExtractJsonDataRedux, json=True,
                            parser=("clusterPage", "content", "titles"),
                            creator=self.CreateJsonItem)

        self._AddDataParser("http://www.svtplay.se/sok?q=", preprocessor=self.ExtractJsonDataRedux)
        self._AddDataParser("http://www.svtplay.se/sok?q=", json=True,
                            parser=("searchResult", "episodes"),
                            creator=self.CreateJsonItem)
        self._AddDataParser("http://www.svtplay.se/sok?q=", json=True,
                            parser=("searchResult", "titles"),
                            creator=self.CreateJsonItem)

        # slugged items for which we need to filter tab items
        self._AddDataParser("^https?://www.svtplay.se/[^?]+\?tab=", matchType=ParserData.MatchRegex,
                            preprocessor=self.ExtractSlugData, json=True)

        # Other Json items
        self._AddDataParser("*", preprocessor=self.ExtractJsonDataRedux, json=True)

        self.__showSomeVideosInListing = True
        self.__listedRelatedTab = "RELATED_VIDEO_TABS_LATEST"
        self._AddDataParser("*", json=True,
                            preprocessor=self.ListSomeVideos,
                            parser=("videoTitlePage", "realatedVideoTabs"),
                            creator=self.CreateJsonFolderItem)

        # self._AddDataParser("*", json=True,
        #                     parser=("context", "dispatcher", "stores", "VideoTitlePageStore",
        #                             "data", "relatedVideoTabs", 0, "videos"),
        #                     creator=self.CreateJsonItem)

        # And the old stuff
        catRegex = Regexer.FromExpresso('<article[^>]+data-title="(?<Title>[^"]+)"[^"]+data-description="(?<Description>[^"]*)"[^>]+data-broadcasted="(?:(?<Date1>[^ "]+) (?<Date2>[^. "]+)[ .](?<Date3>[^"]+))?"[^>]+data-abroad="(?<Abroad>[^"]+)"[^>]+>\W+<a[^>]+href="(?<Url>[^"]+)"[\w\W]{0,5000}?<img[^>]+src="(?<Thumb>[^"]+)')
        self._AddDataParser("http://www.svtplay.se/barn",
                            matchType=ParserData.MatchExact,
                            preprocessor=self.StripNonCategories, parser=catRegex,
                            creator=self.CreateCategoryItem)

        # Update via HTML pages
        self._AddDataParser("http://www.svtplay.se/video/", updater=self.UpdateVideoHtmlItem)
        self._AddDataParser("http://www.svtplay.se/klipp/", updater=self.UpdateVideoHtmlItem)
        # Update via the new API urls
        self._AddDataParser("http://www.svt.se/videoplayer-api/", updater=self.UpdateVideoApiItem)

        # ===============================================================================================================
        # non standard items

        # ===============================================================================================================
        # Test cases:
        #   Affaren Ramel: just 1 folder -> should only list videos

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def SearchSite(self, url=None):  # @UnusedVariable
        """Creates an list of items by searching the site

        Returns:
        A list of MediaItems that should be displayed.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        """

        url = "http://www.svtplay.se/sok?q=%s"
        return chn_class.Channel.SearchSite(self, url)

    # def AddShowItems(self, data):
    #     """ Adds the shows from the alpabetical list
    #
    #     @param data:    The data to use.
    #
    #     Returns a list of MediaItems that were retrieved.
    #
    #     """
    #
    #     items = []
    #
    #     # add the json data as the actual data
    #     dataStart = 'root[\'__svtplay\'] = '
    #     dataStartLen = len(dataStart)
    #     dataStart = data.index(dataStart)
    #     dataEnd = data.index(';root[\'__svtplay\'].env')
    #     data = data[dataStart + dataStartLen:dataEnd]
    #     json = JsonHelper(data)
    #     alphaList = json.GetValue('context', 'dispatcher', 'stores', 'ProgramsStore', 'alphabeticList')
    #     for alpha in alphaList:
    #         for show in alpha['titles']:
    #             items.append(self.CreateJsonEpisodeItem(show))
    #
    #     # clusters = json.GetValue('context', 'dispatcher', 'stores', 'ProgramsStore', 'allClusters')
    #     # for cluster in clusters:
    #     #     for alphaList in clusters[cluster]:
    #     #         for show in alphaList:
    #     #             items.append(self.CreateJsonEpisodeItem(show))
    #     return data, items

    def AddLiveItemsAndGenres(self, data):
        """ Adds the Live items, Channels and Last Episodes to the listing.

        @param data:    The data to use.

        Returns a list of MediaItems that were retrieved.

        """

        items = []

        extraItems = {
            "Kanaler": "#kanaler",
            "Livesändningar": "http://www.svtplay.se/live?sida=1",

            "S&ouml;k": "searchSite",
            "Senaste program": "http://www.svtplay.se/senaste?sida=1",
            "Sista chansen": "http://www.svtplay.se/sista-chansen?sida=1",
            "Populära": "http://www.svtplay.se/populara?sida=1",
        }

        # http://www.svtplay.se/ajax/dokumentar/titlar?filterAccessibility=&filterRights=
        categoryItems = {
            "Drama": (
                "http://www.svtplay.se/genre/drama",
                "http://www.svtstatic.se/play/play5/images/categories/posters/drama-d75cd2da2eecde36b3d60fad6b92ad42.jpg"
            ),
            "Dokumentär": (
                "http://www.svtplay.se/genre/dokumentar",
                "http://www.svtstatic.se/play/play5/images/categories/posters/dokumentar-00599af62aa8009dbc13577eff894b8e.jpg"
            ),
            "Humor": (
                "http://www.svtplay.se/genre/humor",
                "http://www.svtstatic.se/play/play5/images/categories/posters/humor-abc329317eedf789d2cca76151213188.jpg"
            ),
            "Livsstil": (
                "http://www.svtplay.se/genre/livsstil",
                "http://www.svtstatic.se/play/play5/images/categories/posters/livsstil-2d9cd77d86c086fb8908ce4905b488b7.jpg"
            ),
            "Underhållning": (
                "http://www.svtplay.se/genre/underhallning",
                "http://www.svtstatic.se/play/play5/images/categories/posters/underhallning-a60da5125e715d74500a200bd4416841.jpg"
            ),
            "Kultur": (
                "http://www.svtplay.se/genre/kultur",
                "http://www.svtstatic.se/play/play5/images/categories/posters/kultur-93dca50ed1d6f25d316ac1621393851a.jpg"
            ),
            "Samhälle & Fakta": (
                "http://www.svtplay.se/genre/samhalle-och-fakta",
                "http://www.svtstatic.se/play/play5/images/categories/posters/samhalle-och-fakta-3750657f72529a572f3698e01452f348.jpg"
            ),
            "Film": (
                "http://www.svtplay.se/genre/film",
                "http://www.svtstatic.se/image-cms/svtse/1436202866/svtplay/article2952281.svt/ALTERNATES/large/film1280-jpg"
            ),
            # Category items that are in the old layout and won't work yet.
            # "Barn": "http://www.svtplay.se/barn",
            # "Nyheter": "http://www.svtplay.se/nyheter",
            # "Sport": "http://www.svtplay.se/sport",
        }

        for title, url in extraItems.iteritems():
            newItem = mediaitem.MediaItem("\a.: %s :." % (title, ), url)
            newItem.complete = True
            newItem.thumb = self.noImage
            newItem.dontGroup = True
            newItem.SetDate(2099, 1, 1, text="")
            items.append(newItem)

        newItem = mediaitem.MediaItem("\a.: Genrer :.", "")
        newItem.complete = True
        newItem.thumb = self.noImage
        newItem.dontGroup = True
        newItem.SetDate(2099, 1, 1, text="")
        for title, (url, thumb) in categoryItems.iteritems():
            catItem = mediaitem.MediaItem(title, url)
            catItem.complete = True
            catItem.thumb = thumb or self.noImage
            catItem.dontGroup = True
            # catItem.SetDate(2099, 1, 1, text="")
            newItem.items.append(catItem)
        items.append(newItem)
        return data, items

    # noinspection PyUnusedLocal
    def LoadChannelData(self, data):
        """ Adds the channel items to the listing.

        @param data:    The data to use.

        Returns a list of MediaItems that were retrieved.

        """

        items = []
        data = UriHandler.Open("http://www.svtplay.se/api/channel_page", proxy=self.proxy, noCache=True)
        return data, items

    # def ExtractJsonDataSvt(self, data):
    #     return self.__ExtractJsonData(data, "__svtplay")

    def ExtractJsonDataRedux(self, data):
        return self.__ExtractJsonData(data, "__reduxStore")

    def __ExtractJsonData(self, data, root):
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

        Logger.Info("Extracting JSON data during pre-processing")
        data = Regexer.DoRegex('root\[[\'"]%s[\'"]\] = ([\w\W]+?);\W*root\[' % (root, ), data)[-1]
        items = []
        Logger.Trace("JSON data found: %s", data)
        return data, items

    def ExtractSlugData(self, data):
        """ Extracts the correct Slugged Data for tabbed items """

        Logger.Info("Extracting Slugged data during pre-processing")
        data, items = self.ExtractJsonDataRedux(data)

        json = JsonHelper(data)
        slugs = json.GetValue("videoTitlePage", "realatedVideoTabs")
        for slugData in slugs:
            tabSlug = "?tab=%s" % (slugData["slug"], )
            if not self.parentItem.url.endswith(tabSlug):
                continue

            for item in slugData["videos"]:
                items.append(self.CreateJsonItem(item))

        return data, items

    def CreateJsonEpisodeItem(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.Trace(resultSet)
        # url = "%s/%s?tab=program" % (self.baseUrl, resultSet['urlFriendlyTitle'], )
        url = "%s/%s" % (self.baseUrl, resultSet['urlFriendlyTitle'],)
        item = mediaitem.MediaItem(resultSet['title'], url)
        item.icon = self.icon
        item.thumb = self.noImage
        item.isGeoLocked = resultSet.get('onlyAvailableInSweden', False)
        # url = "%s/%s" % (self.baseUrl, resultSet['term'], )
        # item = mediaitem.MediaItem(resultSet['name'], url)
        # item.icon = self.icon
        # item.thumb = self.noImage
        # item.isGeoLocked = resultSet["metaData"].get('onlyAvailableInSweden', False)
        return item

    def CreateJsonEpisodeItemSok(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.Trace(resultSet)
        url = resultSet["url"]
        if url.startswith("/video") or url.startswith("/genre"):
            return None

        url = "%s%s" % (self.baseUrl, url, )
        item = mediaitem.MediaItem(resultSet['title'], url)
        item.icon = self.icon
        item.thumb = resultSet.get("thumbnail", self.noImage)
        if item.thumb.startswith("//"):
            item.thumb = "http:%s" % (item.thumb, )
        item.thumb = item.thumb.replace("/small/", "/large/")

        item.isGeoLocked = resultSet.get('onlyAvailableInSweden', False)
        item.complete = True
        return item

    def CreateJsonPageItem(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """
        Logger.Trace(resultSet)

        if "nextPageUrl" not in resultSet:
            return None

        title = LanguageHelper.GetLocalizedString(LanguageHelper.MorePages)
        url = "%s%s" % (self.baseUrl, resultSet["nextPageUrl"])
        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.thumb = self.noImage
        item.complete = True
        return item

    def ListSomeVideos(self, data):
        """ If there was a Lastest section in the data return those video files """
        items = []

        if not self.__showSomeVideosInListing:
            return data, items

        jsonData = JsonHelper(data)
        sections = jsonData.GetValue("videoTitlePage", "realatedVideoTabs")

        Logger.Debug("Found %s folders/tabs", len(sections))
        if len(sections) == 1:
            # we should exclude that tab from the folders list and show the videos here
            self.__listedRelatedTab = sections[0]["key"]
            # otherwise the default "RELATED_VIDEO_TABS_LATEST" is used
        Logger.Debug("Excluded tab '%s' which will be show as videos", self.__listedRelatedTab)

        for section in sections:
            if not section["key"] == self.__listedRelatedTab:
                continue

            for videoData in section['videos']:
                items.append(self.CreateJsonItem(videoData))
        return data, items

    def CreateJsonFolderItem(self, resultSet):
        Logger.Trace(resultSet)
        if resultSet["key"] == self.__listedRelatedTab and self.__showSomeVideosInListing:
            return None

        slug = resultSet["slug"]
        title = resultSet["name"]
        url = "%s?tab=%s" % (self.parentItem.url, slug)
        item = mediaitem.MediaItem(title, url)
        item.thumb = self.parentItem.thumb
        return item

    def CreateJsonItem(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """
        Logger.Trace(resultSet)

        # determine the title
        programTitle = resultSet.get("programTitle", "")
        showTitle = resultSet.get("title", "")
        if showTitle == "" and programTitle != "":
            title = programTitle
        elif showTitle != "" and programTitle == "":
            title = showTitle
        elif programTitle == "" and showTitle == "":
            Logger.Warning("Could not find title for item: %s", resultSet)
            return None
        elif showTitle != "" and showTitle != programTitle:
            title = "%s - %s" % (programTitle, showTitle)
        else:
            # they are the same
            title = showTitle

        if "live" in resultSet and resultSet["live"]:
            title = "%s (&middot;Live&middot;)" % (title, )

        itemType = resultSet["contentType"]
        if "contentUrl" in resultSet:
            url = resultSet["contentUrl"]
        else:
            url = resultSet["url"]
        broadCastDate = resultSet.get("broadcastDate", None)

        if itemType in ("videoEpisod", "videoKlipp"):
            if not url.startswith("/video/") and not url.startswith("/klipp/"):
                Logger.Warning("Found video item without a /video/ or /klipp/ url.")
                return None
            itemType = "video"
            if "programVersionId" in resultSet:
                url = "http://www.svt.se/videoplayer-api/video/%s" % (resultSet["programVersionId"], )
            else:
                url = "%s%s" % (self.baseUrl, url)
        else:
            itemType = "folder"
            url = "%s%s" % (self.baseUrl, url)

        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.type = itemType
        item.isGeoLocked = resultSet.get("onlyAvailableInSweden", False)
        item.description = resultSet.get("description", "")

        if "season" in resultSet and "episodeNumber" in resultSet:
            season = int(resultSet["season"])
            episode = int(resultSet["episodeNumber"])
            if season > 0 and episode > 0:
                item.name = "s%02de%02d - %s" % (season, episode, item.name)
                item.SetSeasonInfo(season, episode)

        # thumb = resultSet.get("imageMedium", self.noImage).replace("/medium/", "/extralarge/")
        thumb = self.parentItem.thumb
        if "imageMedium" in resultSet:
            thumb = resultSet["imageMedium"]
        elif "thumbnailMedium" in resultSet:
            thumb = resultSet["thumbnailMedium"]
        elif "thumbnail" in resultSet:
            thumb = resultSet["thumbnail"]
        item.thumb = self.__GetThumb(thumb)

        if broadCastDate is not None:
            timeStamp = time.strptime(broadCastDate[:-5], "%Y-%m-%dT%H:%M:%S")
            item.SetDate(*timeStamp[0:6])
        return item

    def CreateCategoryItem(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """
        Logger.Trace(resultSet)

        url = resultSet["Url"]
        if "http://" not in url:
            url = "%s%s" % (self.baseUrl, url)

        thumb = resultSet["Thumb"]
        if thumb.startswith("//"):
            thumb = "http:%s" % (thumb,)

        item = mediaitem.MediaItem(resultSet['Title'], url)
        item.icon = self.icon
        item.thumb = thumb
        item.isGeoLocked = resultSet["Abroad"] == "false"

        if resultSet["Date1"] is not None and resultSet["Date1"].lower() != "imorgon":
            year, month, day, hour, minutes = self.__GetDate(resultSet["Date1"], resultSet["Date2"], resultSet["Date3"])
            item.SetDate(year, month, day, hour, minutes, 0)

        if "/video/" in url:
            item.type = "video"
            videoId = url.split("/")[4]
            item.url = "http://www.svtplay.se/video/%s?type=embed&output=json" % (videoId, )
        # else:
        #     # make sure we get the right tab for displaying
        #     item.url = "%s?tab=program" % (item.url, )

        return item

    def StripNonCategories(self, data):
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
        start = data.find('<div id="playJs-alphabetic-list"')
        end = data.find('<div id="playJs-', start + 1)
        if end == 0:
            end = -1
        data = data[start:end]
        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateChannelItem(self, channel):
        """ Creates a mediaitem for a live channel
        @param channel:     The Regex result from the parser object

        @return:            A MediaItem object for the channel

        """

        Logger.Trace(channel)
        if "schedule" not in channel or not channel["schedule"]:
            return None

        title = channel["name"]
        thumb = self.noImage
        channelId = channel["title"]
        currentSchedule = channel["schedule"][0]

        currentItem = currentSchedule["title"]
        title = "%s : %s" % (title, currentItem)
        description = channel["schedule"][0].get("description", None)
        if "titlePage" in channel["schedule"][0]:
            thumb = channel["schedule"][0]["titlePage"]["thumbnailMedium"]

        # dateFormat = "2016-03-02T19:55:00+0100"
        dateFormat = "%Y-%m-%dT%H:%M:%S"
        startTime = time.strptime(currentSchedule["broadcastStartTime"][:-5], dateFormat)
        endTime = time.strptime(currentSchedule["broadcastEndTime"][:-5], dateFormat)
        title = "%s (%02d:%02d - %02d:%02d)" % (title, startTime.tm_hour, startTime.tm_min, endTime.tm_hour, endTime.tm_min)

        # In theory we could also extract the video URL here.....

        channelItem = mediaitem.MediaItem(title, "http://www.svt.se/videoplayer-api/video/ch-%s" % (channelId, ))
        channelItem.type = "video"
        channelItem.description = description
        channelItem.isLive = True
        channelItem.thumb = thumb
        channelItem.isGeoLocked = True
        return channelItem

    def UpdateVideoHtmlItem(self, item):
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
        data = UriHandler.Open(item.url, proxy=self.proxy)
        # Logger.Trace(data)
        data = self.ExtractJsonDataRedux(data)[0]
        json = JsonHelper(data)

        # check for direct streams:
        streams = json.GetValue("videoTitlePage", "video", "videoReferences")
        subtitles = json.GetValue("videoTitlePage", "video", "subtitles")

        if streams:
            Logger.Info("Found stream information within HTML data")
            return self.__UpdateItemFromVideoReferences(item, streams, subtitles)

        programVersionId = json.GetValue("context", "dispatcher", "stores", "VideoTitlePageStore", "data", "video", "programVersionId")
        if programVersionId:
            item.url = "http://www.svt.se/videoplayer-api/video/%s" % (programVersionId, )
        return self.UpdateVideoApiItem(item)

    def UpdateVideoApiItem(self, item):
        """ Updates an existing MediaItem with more data.

        Arguments:
        item : MediaItem - the MediaItem that needs to be updated
        date : String    - the json content of the item's URL

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
        Logger.Debug('Starting UpdateChannelItem for %s (%s)', item.name, self.channelName)

        data = UriHandler.Open(item.url, proxy=self.proxy)

        json = JsonHelper(data, logger=Logger.Instance())
        videos = json.GetValue("videoReferences")
        subtitles = json.GetValue("subtitleReferences")
        Logger.Trace(videos)
        return self.__UpdateItemFromVideoReferences(item, videos, subtitles)

    def __UpdateItemFromVideoReferences(self, item, videos, subtitles=None):
        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()
        spoofIp = self._GetSetting("spoof_ip", "0.0.0.0")
        if spoofIp is not None:
            part.HttpHeaders["X-Forwarded-For"] = spoofIp

        for video in videos:
            videoFormat = video.get("format", "")
            if not videoFormat:
                videoFormat = video.get("playerType", "")
            videoFormat = videoFormat.lower()

            if "dash" in videoFormat or "hds" in videoFormat:
                Logger.Debug("Skipping video format: %s", videoFormat)
                continue
            Logger.Debug("Found video item for format: %s", videoFormat)

            url = video['url']
            if len(filter(lambda s: s.Url == url, part.MediaStreams)) > 0:
                Logger.Debug("Skippping duplicate Stream url: %s", url)
                continue

            if "m3u8" in url:
                altIndex = url.find("m3u8?")
                # altIndex = videoUrl.find("~uri")
                if altIndex > 0:
                    url = url[0:altIndex + 4]

                for s, b in M3u8.GetStreamsFromM3u8(url, proxy=self.proxy, headers=part.HttpHeaders):
                    part.AppendMediaStream(s, b)

            elif video["url"].startswith("rtmp"):
                # just replace some data in the URL
                part.AppendMediaStream(self.GetVerifiableVideoUrl(video["url"]).replace("_definst_", "?slist="), video[1])
            else:
                part.AppendMediaStream(url, 0)

        if subtitles:
            Logger.Info("Found subtitles to play")
            for sub in subtitles:
                subFormat = sub["format"].lower()
                url = sub["url"]
                if subFormat == "websrt":
                    subUrl = url
                # elif subFormat == "webvtt":
                #     Logger.Info("Found M3u8 subtitle, replacing with WSRT")
                #     start, name, index = sub[-1].rsplit("/", 2)
                #     subUrl = "%s/%s/%s.wsrt" % (start, name, name)
                else:
                    # look for more
                    continue

                part.Subtitle = subtitlehelper.SubtitleHelper.DownloadSubtitle(subUrl, format="srt", proxy=self.proxy)
                # stop when finding one
                break

        item.complete = True
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

    def __GetThumb(self, thumb):
        thumbSize = "/large/"
        if "<>" in thumb:
            thumbParts = thumb.split("<>")
            thumbIndex = int(thumbParts[1])
            thumbStores = ["http://www.svtstatic.se/image-cms-stage/svtse",
                           "//www.svtstatic.se/image-cms-stage/svtse",
                           "http://www.svtstatic.se/image-cms/svtse",
                           "//www.svtstatic.se/image-cms/svtse",
                           "http://www.svtstatic.se/image-cms-stage/barn",
                           "//www.svtstatic.se/image-cms-stage/barn",
                           "http://www.svtstatic.se/image-cms/barn",
                           "//www.svtstatic.se/image-cms/barn"]
            thumb = "%s%s" % (thumbStores[thumbIndex], thumbParts[-1])

        if thumb.startswith("//"):
            thumb = "http:%s" % (thumb,)

        thumb = thumb.replace("/{format}/", thumbSize)\
            .replace("/medium/", thumbSize)\
            .replace("/small/", thumbSize)
        Logger.Trace(thumb)
        return thumb
