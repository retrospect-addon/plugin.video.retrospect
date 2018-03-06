# coding:UTF-8
import datetime

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
        self.mainListUri = "https://www.svtplay.se/api/all_titles_and_singles"
        self.baseUrl = "https://www.svtplay.se"
        self.swfUrl = "https://media.svt.se/swf/video/svtplayer-2016.01.swf"

        # setup the intial listing based on Alphabeth and specials
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
                            preprocessor=self.AddLiveItemsAndGenres)
        # in case we use the All Titles and Singles
        self._AddDataParser("https://www.svtplay.se/api/all_titles_and_singles",
                            matchType=ParserData.MatchExact, json=True,
                            # preprocessor=self.FetchThumbData,
                            parser=(), creator=self.MergeJsonEpisodeItem)

        # setup channel listing based on JSON data
        self._AddDataParser("#kanaler",
                            preprocessor=self.LoadChannelData,
                            json=True,
                            parser=("hits", ),
                            creator=self.CreateChannelItem)

        # special pages (using JSON) using a generic pre-processor to extract the data
        specialJsonPages = "^https?://www.svtplay.se/(senaste|sista-chansen|populara|live)\?sida=\d+$"
        self._AddDataParser(specialJsonPages,
                            matchType=ParserData.MatchRegex, preprocessor=self.ExtractJsonData)
        self._AddDataParser(specialJsonPages,
                            matchType=ParserData.MatchRegex, json=True,
                            parser=("gridPage", "content"),
                            creator=self.CreateJsonItem)
        self._AddDataParser(specialJsonPages,
                            matchType=ParserData.MatchRegex, json=True,
                            parser=("gridPage", "pagination"),
                            creator=self.CreateJsonPageItem)

        # genres (using JSON)
        self._AddDataParser("https://www.svtplay.se/genre",
                            preprocessor=self.ExtractJsonData, json=True,
                            name="Parser for dynamically parsing tags/genres from overview",
                            matchType=ParserData.MatchExact,
                            parser=("clusters", "alphabetical"),
                            creator=self.CreateJsonGenre)

        self._AddDataParser("https://www.svtplay.se/genre/",
                            preprocessor=self.ExtractJsonData, json=True,
                            name="Video/Folder parsers for items in a Genre/Tag",
                            parser=("clusterPage", "titlesAndEpisodes"),
                            creator=self.CreateJsonItem)

        self._AddDataParser("https://www.svtplay.se/sok?q=", preprocessor=self.ExtractJsonData)
        self._AddDataParser("https://www.svtplay.se/sok?q=", json=True,
                            parser=("searchPage", "episodes"),
                            creator=self.CreateJsonItem)
        self._AddDataParser("https://www.svtplay.se/sok?q=", json=True,
                            parser=("searchPage", "videosAndTitles"),
                            creator=self.CreateJsonItem)

        # slugged items for which we need to filter tab items
        self._AddDataParser("^https?://www.svtplay.se/[^?]+\?tab=", matchType=ParserData.MatchRegex,
                            preprocessor=self.ExtractSlugData, json=True, updater=self.UpdateVideoHtmlItem)

        # Other Json items
        self._AddDataParser("*", preprocessor=self.ExtractJsonData, json=True)

        self.__showSomeVideosInListing = True
        self.__listedRelatedTab = "RELATED_VIDEO_TABS_LATEST"
        self.__excludedTabs = ["RELATED_VIDEOS_ACCORDION_UPCOMING", ]
        self._AddDataParser("*", json=True,
                            preprocessor=self.ListSomeVideos,
                            parser=("relatedVideoContent", "relatedVideosAccordion"),
                            creator=self.CreateJsonFolderItem)

        # And the old stuff
        catRegex = Regexer.FromExpresso('<article[^>]+data-title="(?<Title>[^"]+)"[^"]+data-description="(?<Description>[^"]*)"[^>]+data-broadcasted="(?:(?<Date1>[^ "]+) (?<Date2>[^. "]+)[ .](?<Date3>[^"]+))?"[^>]+data-abroad="(?<Abroad>[^"]+)"[^>]+>\W+<a[^>]+href="(?<Url>[^"]+)"[\w\W]{0,5000}?<img[^>]+src="(?<Thumb>[^"]+)')
        self._AddDataParser("https://www.svtplay.se/barn",
                            matchType=ParserData.MatchExact,
                            preprocessor=self.StripNonCategories, parser=catRegex,
                            creator=self.CreateCategoryItem)

        # Update via HTML pages
        self._AddDataParser("https://www.svtplay.se/video/", updater=self.UpdateVideoHtmlItem)
        self._AddDataParser("https://www.svtplay.se/klipp/", updater=self.UpdateVideoHtmlItem)
        # Update via the new API urls
        self._AddDataParser("https://www.svt.se/videoplayer-api/", updater=self.UpdateVideoApiItem)
        self._AddDataParser("https://www.svt.se/videoplayer-api/", updater=self.UpdateVideoApiItem)

        # ===============================================================================================================
        # non standard items
        self.__thumbLookup = dict()

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

        url = "https://www.svtplay.se/sok?q=%s"
        return chn_class.Channel.SearchSite(self, url)

    def AddLiveItemsAndGenres(self, data):
        """ Adds the Live items, Channels and Last Episodes to the listing.

        @param data:    The data to use.

        Returns a list of MediaItems that were retrieved.

        """

        items = []

        extraItems = {
            "Kanaler": "#kanaler",
            "Livesändningar": "https://www.svtplay.se/live?sida=1",

            "S&ouml;k": "searchSite",
            "Senaste program": "https://www.svtplay.se/senaste?sida=1",
            "Sista chansen": "https://www.svtplay.se/sista-chansen?sida=1",
            "Populära": "https://www.svtplay.se/populara?sida=1",
        }

        # https://www.svtplay.se/ajax/dokumentar/titlar?filterAccessibility=&filterRights=
        categoryItems = {
            "Drama": (
                "https://www.svtplay.se/genre/drama",
                "https://www.svtstatic.se/play/play5/images/categories/posters/drama-d75cd2da2eecde36b3d60fad6b92ad42.jpg"
            ),
            "Dokumentär": (
                "https://www.svtplay.se/genre/dokumentar",
                "https://www.svtstatic.se/play/play5/images/categories/posters/dokumentar-00599af62aa8009dbc13577eff894b8e.jpg"
            ),
            "Humor": (
                "https://www.svtplay.se/genre/humor",
                "https://www.svtstatic.se/play/play5/images/categories/posters/humor-abc329317eedf789d2cca76151213188.jpg"
            ),
            "Livsstil": (
                "https://www.svtplay.se/genre/livsstil",
                "https://www.svtstatic.se/play/play5/images/categories/posters/livsstil-2d9cd77d86c086fb8908ce4905b488b7.jpg"
            ),
            "Underhållning": (
                "https://www.svtplay.se/genre/underhallning",
                "https://www.svtstatic.se/play/play5/images/categories/posters/underhallning-a60da5125e715d74500a200bd4416841.jpg"
            ),
            "Kultur": (
                "https://www.svtplay.se/genre/kultur",
                "https://www.svtstatic.se/play/play5/images/categories/posters/kultur-93dca50ed1d6f25d316ac1621393851a.jpg"
            ),
            "Samhälle & Fakta": (
                "https://www.svtplay.se/genre/samhalle-och-fakta",
                "https://www.svtstatic.se/play/play5/images/categories/posters/samhalle-och-fakta-3750657f72529a572f3698e01452f348.jpg"
            ),
            "Film": (
                "https://www.svtplay.se/genre/film",
                "https://www.svtstatic.se/image-cms/svtse/1436202866/svtplay/article2952281.svt/ALTERNATES/large/film1280-jpg"
            ),
            "Barn": (
                "https://www.svtplay.se/genre/barn",
                "https://www.svtstatic.se/play/play5/images/categories/posters/barn-c17302a6f7a9a458e0043b58bbe8ab79.jpg"
            ),
            "Nyheter": (
                "https://www.svtplay.se/genre/nyheter",
                "https://www.svtstatic.se/play/play6/images/categories/posters/nyheter.e67ff1b5770152af4690ad188546f9e9.jpg"
            ),
            "Sport": (
                "https://www.svtplay.se/genre/sport",
                "https://www.svtstatic.se/play/play6/images/categories/posters/sport.98b65f6627e4addbc4177542035ea504.jpg"
            )
        }

        for title, url in extraItems.iteritems():
            newItem = mediaitem.MediaItem("\a.: %s :." % (title, ), url)
            newItem.complete = True
            newItem.thumb = self.noImage
            newItem.dontGroup = True
            newItem.SetDate(2099, 1, 1, text="")
            items.append(newItem)

        newItem = mediaitem.MediaItem("\a.: Kategorier :.", "https://www.svtplay.se/genre")
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

        newItem = mediaitem.MediaItem("\a.: Genrer/Taggar :.", "https://www.svtplay.se/genre")
        newItem.complete = True
        newItem.thumb = self.noImage
        newItem.dontGroup = True
        newItem.SetDate(2099, 1, 1, text="")
        items.append(newItem)

        return data, items

    # def FetchThumbData(self, data):
    #     items = []
    #
    #     thumbData = UriHandler.Open("https://www.svtplay.se/ajax/sok/forslag.json", proxy=self.proxy)
    #     json = JsonHelper(thumbData)
    #     for jsonData in json.GetValue():
    #         if "thumbnail" not in jsonData:
    #             continue
    #         self.__thumbLookup[jsonData["url"]] = jsonData["thumbnail"]
    #
    #     return data, items

    def MergeJsonEpisodeItem(self, resultSet):

        thumb = self.__thumbLookup.get(resultSet["contentUrl"])
        if thumb:
            resultSet["poster"] = thumb

        item = self.CreateJsonEpisodeItem(resultSet)
        return item

    # noinspection PyUnusedLocal
    def LoadChannelData(self, data):
        """ Adds the channel items to the listing.

        @param data:    The data to use.

        Returns a list of MediaItems that were retrieved.

        """

        items = []
        # data = UriHandler.Open("https://www.svtplay.se/api/channel_page", proxy=self.proxy, noCache=True)

        now = datetime.datetime.now()
        try:
            serverTime = UriHandler.Open("https://www.svtplay.se/api/server_time",
                                         proxy=self.proxy, noCache=True)
            serverTimeJson = JsonHelper(serverTime)
            serverTime = serverTimeJson.GetValue("time")
        except:
            Logger.Error("Error determining server time", exc_info=True)
            serverTime = "%04d-%02d-%02dT%02d:%02d:%02d" % (now.year, now.month, now.day, now.hour, now.minute, now.second)

        data = UriHandler.Open(
            "https://www.svtplay.se/api/channel_page?now=%s" % (serverTime, ),
            proxy=self.proxy)
        return data, items

    def ExtractJsonData(self, data):
        return self.__ExtractJsonData(data, "(?:__svtplay|__reduxStore)")

    def ExtractSlugData(self, data):
        """ Extracts the correct Slugged Data for tabbed items """

        Logger.Info("Extracting Slugged data during pre-processing")
        data, items = self.ExtractJsonData(data)
        # data, items = self.ExtractJsonDataRedux(data)

        json = JsonHelper(data)
        slugs = json.GetValue("relatedVideoContent", "relatedVideosAccordion")
        for slugData in slugs:
            tabSlug = "?tab=%s" % (slugData["slug"], )
            if not self.parentItem.url.endswith(tabSlug):
                continue

            for item in slugData["videos"]:
                i = self.CreateJsonItem(item)
                if i:
                    items.append(i)

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

        if "titleArticleId" in resultSet:
            return None

        # url = "%s/%s?tab=program" % (self.baseUrl, resultSet['urlFriendlyTitle'], )
        url = "%s%s" % (self.baseUrl, resultSet['contentUrl'],)
        if "/video/" in url:
            return None

        item = mediaitem.MediaItem(resultSet['programTitle'], url)
        item.icon = self.icon
        item.isGeoLocked = resultSet.get('onlyAvailableInSweden', False)
        item.description = resultSet.get('description')

        thumb = self.noImage
        if "poster" in resultSet:
            thumb = resultSet["poster"]
            thumb = self.__GetThumb(thumb or self.noImage)

        item.thumb = thumb
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
        if url.startswith("/video") or url.startswith("/genre") or url.startswith('/oppetarkiv'):
            return None

        url = "%s%s" % (self.baseUrl, url, )
        item = mediaitem.MediaItem(resultSet['title'], url)
        item.icon = self.icon
        item.thumb = resultSet.get("thumbnail", self.noImage)
        if item.thumb.startswith("//"):
            item.thumb = "https:%s" % (item.thumb, )
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

        title = "\b.: %s :." % (LanguageHelper.GetLocalizedString(LanguageHelper.MorePages), )
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
        sections = jsonData.GetValue("relatedVideoContent", "relatedVideosAccordion")
        sections = filter(lambda s: s['type'] not in self.__excludedTabs, sections)

        Logger.Debug("Found %s folders/tabs", len(sections))
        if len(sections) == 1:
            # we should exclude that tab from the folders list and show the videos here
            self.__listedRelatedTab = sections[0]["type"]
            # otherwise the default "RELATED_VIDEO_TABS_LATEST" is used
        Logger.Debug("Excluded tab '%s' which will be show as videos", self.__listedRelatedTab)

        for section in sections:
            if not section["type"] == self.__listedRelatedTab:
                continue

            for videoData in section['videos']:
                items.append(self.CreateJsonItem(videoData))
        return data, items

    def CreateJsonFolderItem(self, resultSet):
        Logger.Trace(resultSet),
        if resultSet["type"] == self.__listedRelatedTab and self.__showSomeVideosInListing:
            return None
        if resultSet["type"] in self.__excludedTabs:
            return None

        slug = resultSet["slug"]
        title = resultSet["name"]
        url = "%s?tab=%s" % (self.parentItem.url, slug)
        item = mediaitem.MediaItem(title, url)
        item.thumb = self.parentItem.thumb
        return item

    def CreateJsonGenre(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        genres = []

        for cluster in resultSet['clusters']:
            Logger.Trace(cluster)
            url = "%s%s" % (self.baseUrl, cluster['contentUrl'])
            genre = mediaitem.MediaItem(cluster['name'], url)
            genre.icon = self.icon
            genre.description = cluster.get('description')
            genre.fanart = cluster.get('backgroundImage') or self.parentItem.fanart
            genre.fanart = self.__GetThumb(genre.fanart, thumbSize="/extralarge/")
            genre.thumb = cluster.get('thumbnailImage') or self.noImage
            genre.thumb = self.__GetThumb(genre.thumb)
            genres.append(genre)

        return genres

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
        programTitle = resultSet.get("programTitle", "") or ""
        showTitle = resultSet.get("title", "") or ""
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

        itemType = resultSet.get("contentType")
        if "contentUrl" in resultSet:
            url = resultSet["contentUrl"]
        else:
            url = resultSet["url"]
        broadCastDate = resultSet.get("broadcastDate", None)

        if itemType in ("videoEpisod", "videoKlipp", "singel"):
            if not url.startswith("/video/") and not url.startswith("/klipp/"):
                Logger.Warning("Found video item without a /video/ or /klipp/ url.")
                return None
            itemType = "video"
            if "programVersionId" in resultSet:
                url = "https://www.svt.se/videoplayer-api/video/%s" % (resultSet["programVersionId"],)
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

        if "season" in resultSet and "episodeNumber" in resultSet and resultSet["episodeNumber"]:
            season = int(resultSet["season"])
            episode = int(resultSet["episodeNumber"])
            if season > 0 and episode > 0:
                item.name = "s%02de%02d - %s" % (season, episode, item.name)
                item.SetSeasonInfo(season, episode)

        # thumb = resultSet.get("imageMedium", self.noImage).replace("/medium/", "/extralarge/")
        thumb = self.noImage
        if self.parentItem:
            thumb = self.parentItem.thumb

        for imageKey in ("image", "imageMedium", "thumbnailMedium", "thumbnail", "poster"):
            if imageKey in resultSet and resultSet[imageKey] is not None:
                thumb = resultSet[imageKey]
                break

        item.thumb = self.__GetThumb(thumb or self.noImage)

        if broadCastDate is not None:
            if "+" in broadCastDate:
                broadCastDate = broadCastDate.rsplit("+")[0]
            timeStamp = DateHelper.GetDateFromString(broadCastDate, "%Y-%m-%dT%H:%M:%S")
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
        if "http://" not in url and "https://" not in url:
            url = "%s%s" % (self.baseUrl, url)

        thumb = resultSet["Thumb"]
        if thumb.startswith("//"):
            thumb = "https:%s" % (thumb,)

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
            item.url = "https://www.svtplay.se/video/%s?type=embed&output=json" % (videoId,)
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

        title = channel["programmeTitle"]
        episode = channel.get("episodeTitle", None)
        thumb = self.noImage
        channelId = channel["channel"].lower()
        if channelId == "svtk":
            channelTitle = "Kunskapskanalen"
            channelId = "kunskapskanalen"
        elif channelId == "svtb":
            channelTitle = "Barnkanalen"
            channelId = "barnkanalen"
        else:
            channelTitle = channel["channel"]
        description = channel["longDescription"]

        dateFormat = "%Y-%m-%dT%H:%M:%S"
        startTime = DateHelper.GetDateFromString(channel["publishingTime"][:19], dateFormat)
        endTime = DateHelper.GetDateFromString(channel["publishingEndTime"][:19], dateFormat)

        if episode:
            title = "%s: %s - %s (%02d:%02d - %02d:%02d)" \
                    % (channelTitle, title, episode,
                       startTime.tm_hour, startTime.tm_min, endTime.tm_hour, endTime.tm_min)
        else:
            title = "%s: %s (%02d:%02d - %02d:%02d)" \
                    % (channelTitle, title,
                       startTime.tm_hour, startTime.tm_min, endTime.tm_hour, endTime.tm_min)
        channelItem = mediaitem.MediaItem(title, "https://www.svt.se/videoplayer-api/video/ch-%s" % (channelId.lower(), ))
        channelItem.type = "video"
        channelItem.description = description
        channelItem.isLive = True
        channelItem.isGeoLocked = True

        channelItem.thumb = thumb
        if "titlePageThumbnailIds" in channel and channel["titlePageThumbnailIds"]:
            channelItem.thumb = "https://www.svtstatic.se/image/wide/650/%s.jpg" % (channel["titlePageThumbnailIds"][0], )
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
        data = self.ExtractJsonData(data)[0]
        json = JsonHelper(data, logger=Logger.Instance())

        # check for direct streams:
        streams = json.GetValue("videoTitlePage", "video", "videoReferences")
        subtitles = json.GetValue("videoTitlePage", "video", "subtitles")

        if streams:
            Logger.Info("Found stream information within HTML data")
            return self.__UpdateItemFromVideoReferences(item, streams, subtitles)

        videoId = json.GetValue("videoPage", "video", "id")
        # in case that did not work, try the old version.
        if not videoId:
            videoId = json.GetValue("videoPage", "video", "programVersionId")
        if videoId:
            # item.url = "https://www.svt.se/videoplayer-api/video/%s" % (videoId, )
            item.url = "https://api.svt.se/videoplayer-api/video/%s" % (videoId, )
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
        if self.localIP:
            part.HttpHeaders.update(self.localIP)

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

    def __GetThumb(self, thumb, thumbSize="/large/"):
        """ Converts images into the correct url format

        @param thumb:       the original URL 
        @param thumbSize:   the size to make them
        @return:            the actual url
        
        """

        if "<>" in thumb:
            thumbParts = thumb.split("<>")
            thumbIndex = int(thumbParts[1])
            thumbStores = ["https://www.svtstatic.se/image-cms-stage/svtse",
                           "//www.svtstatic.se/image-cms-stage/svtse",
                           "https://www.svtstatic.se/image-cms/svtse",
                           "//www.svtstatic.se/image-cms/svtse",
                           "https://www.svtstatic.se/image-cms-stage/barn",
                           "//www.svtstatic.se/image-cms-stage/barn",
                           "https://www.svtstatic.se/image-cms/barn",
                           "//www.svtstatic.se/image-cms/barn"]
            thumb = "%s%s" % (thumbStores[thumbIndex], thumbParts[-1])

        if thumb.startswith("//"):
            thumb = "https:%s" % (thumb,)

        thumb = thumb.replace("/{format}/", thumbSize)\
            .replace("/medium/", thumbSize)\
            .replace("/small/", thumbSize)
        Logger.Trace(thumb)
        return thumb

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
