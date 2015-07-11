import time
import datetime
import cookielib
import os

import mediaitem
import contextmenu
import chn_class

from config import Config
from regexer import Regexer
from helpers import subtitlehelper
from helpers.jsonhelper import JsonHelper

from logger import Logger
from streams.m3u8 import M3u8
from urihandler import UriHandler
from addonsettings import AddonSettings
from helpers.datehelper import DateHelper
from parserdata import ParserData
from helpers.languagehelper import LanguageHelper


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
        self.noImage = "nosimage.png"

        # set context menu items
        self.contextMenuItems.append(contextmenu.ContextMenuItem("Download item", "CtMnDownload", itemTypes='video'))

        # setup the urls
        if self.channelCode == "uzgjson":
            self.baseUrl = "http://apps-api.uitzendinggemist.nl"
            self.mainListUri = "#mainlist"
            # self.mainListUri = "%s/series.json" % (self.baseUrl,)
            self.noImage = "nosimage.png"
        else:
            raise NotImplementedError("Code %s is not implemented" % (self.channelCode,))

        # mainlist stuff
        self._AddDataParser("#mainlist", preprocessor=self.GetInitialFolderItems)
        self._AddDataParser("%s/series.json" % (self.baseUrl,),
                            parser=(), creator= self.CreateEpisodeItem,
                            json=True)

        # live stuff
        self.baseUrlLive = "http://www.npo.nl"

        # live radio, the folders and items
        self._AddDataParser("/radio", matchType=ParserData.MatchEnd,
                            parser='<a href="/(radio)/([^/"]+)"[^>]+><img[^>]+src="([^"]+)',
                            creator=self.CreateLiveRadioFolder)

        self._AddDataParser("/radio/", matchType=ParserData.MatchContains,
                            preprocessor=self.GetAdditionalLiveItems,
                            parser="<option value=\"(http://[^\"]+)\"[^>]+>([^<]+)</option>",
                            creator=self.CreateLiveRadio,
                            updater=self.UpdateVideoItemLive)

        self._AddDataParser("/live", matchType=ParserData.MatchEnd, preprocessor=self.GetAdditionalLiveItems,
                            parser='<img[^>]+src="([^"]+)" /></a>[\w\W]{0,400}?<div class=\'item current-item\'>\W+'
                                   '<div class=\'time now\'>Nu</div>\W+<div class=\'description\'>\W+'
                                   '<a href="/live/([^"]+)" class="now">([^<]+)[\w\W]{0,200}?'
                                   '<div class=\'item next-item\'>\W+<div class=\'time next\'>([^<]+)</div>\W+'
                                   '<div class=\'description next\'>\W+<a[^>]+class="next">([^<]+)',
                            creator=self.CreateLiveTv, updater=self.UpdateVideoItemLive)

        # and some additional ones that might not appear in the first list
        self._AddDataParser("/live", matchType=ParserData.MatchEnd,
                            parser='<a href="/(live)/([^/"]+)"[^>]*>[\w\W]{0,300}?<div[^>]+'
                                   'style="background-image: url\(&#x27;([^)]+)&#x27;\)"[^>]*></div>',
                            creator=self.CreateLiveTv2)

        # recent and popular stuff and other Json data
        self._AddDataParser(".json",
                            parser=(), creator=self.CreateVideoItemJson,
                            json=True, matchType=ParserData.MatchEnd)

        # json for video's if mobile mode
        self._AddDataParser("apps-api.uitzendinggemist.nl/series/",
                            parser=("episodes", ), creator=self.CreateVideoItemJson,
                            json=True, matchType=ParserData.MatchContains)

        # Set self.nonMobilePageSize to 0 to enable mobile pages
        self.nonMobilePageSize = 50
        self.nonMobileMaxPageSize = 100

        # Non-mobile folders -> indicator if there are more items
        self.nonMobilePageRegex = "<div class=\Wsearch-results\W (?:data-num-found=\W(?<Total>\d+)\W " \
                                  "data-rows=\W(?<PageSize>\d+)\W data-start=\W(?<CurrentStart>\d+)\W|" \
                                  "data-page=\W(?<Page>\d+)\W)".replace("(?<", "(?P<")
        self._AddDataParser("*", parser=self.nonMobilePageRegex, creator=self.CreateFolderItemNonMobile)

        # Non-mobile videos
        self.nonMobileVideoItemRegex = 'src="(?<Image>[^"]+)"\W+>[\w\W]{0,500}?</a></div>\W*</div>\W*<div[^>]*>\W*' \
                                       '<a href="(?<Url>[^"]+/(?<Day>\d+)-(?<Month>\d+)-(?<Year>\d+)/(?<WhatsOnId>' \
                                       '[^/"]+))"[^>]*><h4>(?<Title>[^<]+)<[\W\w]{0,600}?<p[^>]+>(?<Description>' \
                                       '[^<]*)'.replace('(?<', '(?P<')

        self._AddDataParser("*", parser=self.nonMobileVideoItemRegex, creator=self.CreateVideoItemNonMobile,
                            updater=self.UpdateVideoItem)

        # Alpha listing and paging for that list
        self._AddDataParser("#alphalisting", preprocessor=self.AlphaListing)
        programRegex = Regexer.FromExpresso('<a href="(?<Url>[^"]+)/(?<WhatsOnId>[^"]+)">\W*<img[^>]+src="'
                                            '(?<Image>[^"]+)" />\W*</a>\W*</div>\W*</div>\W*<div[^<]+<a[^>]*><h4>'
                                            '[\n\r]*(?<Title>[^<]+)\W*<span[^>]*>[^>]+>\W*<span[^>]*>[^>]+>\W*</h4>'
                                            '\W*<h5>(?:[^>]*>){2}[^<]*(?:<a[^>]*>\w+ (?<Day>\d+) (?<MonthName>\w+) '
                                            '(?<Year>\d+)[^>]*(?<Hour>\d+):(?<Minutes>\d+)</a></h5>\W*)?<p[^>]*>'
                                            '(?:<span>)?(?<Description>[^<]*)')
        # programRegex = Regexer.FromExpresso('src="(?<Image>[^"]+)" />\W*(?:<div[^/]+</div><div[^/]+</div></div>\W*)?'
        #                                     '</a></div>\W*</div>\W*<div[^>]*>\W*<a href="(?<Url>[^"]+\/(?<WhatsOnId>'
        #                                     '[^/"]+))"[^>]*><h4>(?<Title>[^<]+)<[\W\w]{0,200}?<h5>([^>]*>){3}[^<]*?'
        #                                     '(?<Day>\d+) (?<Month>\w+) (?<Year>\d+)[^<]+(?<Hours>\d+):(?<Minutes>\d+)'
        #                                     '[^>]+></h5>\W*<p[^>]+>(?<Description>[^<]*)')
        self._AddDataParser("^http://www.npo.nl/series/([a-z]|0-9)\?page=\d+$", matchType=ParserData.MatchRegex,
                            parser=programRegex, creator=self.CreateFolderItemAlpha)
        self._AddDataParser("^http://www.npo.nl/series/([a-z]|0-9)\?page=\d+$", matchType=ParserData.MatchRegex,
                            parser=self.nonMobilePageRegex, creator=self.CreateFolderItemNonMobile)

        # needs to be here because it will be too late in the script version
        self.__IgnoreCookieLaw()

        # ===============================================================================================================
        # non standard items
        # self.__TokenTest()

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def GetAdditionalLiveItems(self, data):
        Logger.Info("Processing Live items")

        items = []
        if "/radio/" in self.parentItem.url:
            # we should always add the parent as radio item
            parent = self.parentItem
            Logger.Debug("Adding main radio item to sub item list: %s", parent)
            item = mediaitem.MediaItem("%s (Hoofd kanaal)" % (parent.name,), parent.url)
            item.icon = parent.icon
            item.thumb = parent.thumb
            item.type = 'video'
            item.isLive = True
            item.complete = False
            items.append(item)

        elif self.parentItem.url.endswith("/live"):
            # let's add the 3FM live stream
            parent = self.parentItem
            Logger.Debug("Adding 3fm live video item to sub item list: %s", parent)
            item = mediaitem.MediaItem("3FM Live",
                                       "http://e.omroep.nl/metadata/LI_3FM_300881")
            item.icon = parent.icon
            item.thumb = "http://www.3fm.nl/data/thumb/abc_media_image/113000/113453/w210.1b764.jpg"
            item.type = 'video'
            item.isLive = True
            item.complete = False
            items.append(item)
        return data, items

    def GetInitialFolderItems(self, data):
        items = []
        search = mediaitem.MediaItem("Zoeken", "searchSite")
        search.complete = True
        search.icon = self.icon
        search.thumb = self.noImage
        search.dontGroup = True
        search.SetDate(2200, 1, 1, text="")
        items.append(search)

        extra = mediaitem.MediaItem("Populair", "%s/episodes/popular.json" % (self.baseUrl,))
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.SetDate(2200, 1, 1, text="")
        items.append(extra)

        extra = mediaitem.MediaItem("Tips", "%s/tips.json" % (self.baseUrl,))
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.SetDate(2200, 1, 1, text="")
        items.append(extra)

        extra = mediaitem.MediaItem("Recent", "%s/broadcasts/recent.json" % (self.baseUrl,))
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.SetDate(2200, 1, 1, text="")
        items.append(extra)

        extra = mediaitem.MediaItem("Live Radio", "%s/radio" % (self.baseUrlLive,))
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.SetDate(2200, 1, 1, text="")
        items.append(extra)

        extra = mediaitem.MediaItem("Live TV", "%s/live" % (self.baseUrlLive,))
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.SetDate(2200, 1, 1, text="")
        items.append(extra)

        extra = mediaitem.MediaItem("Programma's (Hele lijst)", "%s/series.json" % (self.baseUrl,))
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.description = "Volledige programma lijst van de NPO iOS/Android App."
        extra.SetDate(2200, 1, 1, text="")
        items.append(extra)

        extra = mediaitem.MediaItem("Programma's (A-Z)", "#alphalisting")
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.description = "Alfabetische lijst van de NPO.nl site."
        extra.dontGroup = True
        extra.SetDate(2200, 1, 1, text="")

        items.append(extra)

        today = datetime.datetime.now()
        days = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        for i in range(0, 7, 1):
            airDate = today - datetime.timedelta(i)
            Logger.Trace("Adding item for: %s", airDate)

            # Determine a nice display date
            day = days[airDate.weekday()]
            if i == 0:
                day = "Vandaag"
            elif i == 1:
                day = "Gisteren"
            elif i == 2:
                day = "Eergisteren"
            title = "%04d-%02d-%02d - %s" % (airDate.year, airDate.month, airDate.day, day)

            url = "http://www.npo.nl/zoeken?utf8=%%E2%%9C%%93&sort_date=%02d-%02d-%04d&page=1" % \
                  (airDate.day, airDate.month, airDate.year)
            extra = mediaitem.MediaItem(title, url)
            extra.complete = True
            extra.icon = self.icon
            extra.thumb = self.noImage
            extra.dontGroup = True
            extra.HttpHeaders["X-Requested-With"] = "XMLHttpRequest"
            extra.HttpHeaders["Accept"] = "text/html, */*; q=0.01"

            extra.SetDate(airDate.year, airDate.month, airDate.day, text="")
            items.append(extra)

        return data, items

    def AlphaListing(self, data):
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

        Logger.Info("Generating an Alpha list for NPO")

        items = []
        titleFormat = LanguageHelper.GetLocalizedString(LanguageHelper.StartWith)
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0":
            if char == "0":
                char = "0-9"
            subItem = mediaitem.MediaItem(titleFormat % (char,),
                                          "http://www.npo.nl/series/%s?page=1" % (char.lower(), ))
            subItem.complete = True
            subItem.icon = self.icon
            subItem.thumb = self.noImage
            subItem.dontGroup = True
            items.append(subItem)
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

        Logger.Trace("CreateEpisodeItem(%s)", resultSet)

        episodeId = resultSet['nebo_id']
        # if we should not use the mobile listing and we have a non-mobile ID)
        if 'mid' in resultSet and self.nonMobilePageSize > 0:
            nonMobileId = resultSet['mid']
            url = "http://www.npo.nl/series/%s/search?media_type=broadcast&start_date=&end_date=&start=0&rows=%s" \
                  % (nonMobileId, self.nonMobilePageSize)
        else:
            url = "%s/series/%s.json" % (self.baseUrl, episodeId)

        name = resultSet['name']
        description = resultSet.get('description', '')
        thumbUrl = resultSet['image']

        item = mediaitem.MediaItem(name, url)
        item.type = 'folder'
        item.icon = self.icon
        item.complete = True
        item.description = description

        if thumbUrl:
            item.thumb = thumbUrl
        else:
            item.thumb = self.noImage

        # Logger.Trace("Created %s", item.guid)
        return item

    def CreateVideoItemJson(self, resultSet):
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

        # in some case some properties are at the root and some at the subnode
        # get the root items here
        posix = resultSet.get('starts_at', None)
        name = resultSet.get('name', None)
        description = resultSet.get('description', '')
        image = resultSet.get('image', None)

        # the tips has an extra 'episodes' key
        if 'episode' in resultSet:
            Logger.Debug("Found subnode: episodes")
            # set to episode node
            data = resultSet['episode']
            Logger.Trace(data)
            titleExtra = resultSet.get('title', '')
        else:
            titleExtra = None
            data = resultSet

        posix = data.get('broadcasted_at', posix)
        broadcasted = datetime.datetime.fromtimestamp(posix)

        if not name:
            Logger.Debug("Trying alternative ways to get the title")
            name = data.get('series', {'name': self.parentItem.name})['name']

        name.strip("")
        if titleExtra:
            name = "%s - %s" % (name, titleExtra)

        # url = data['video']['m3u8']

        videoId = data.get('whatson_id', None)
        item = mediaitem.MediaItem(name, videoId)
        item.icon = self.icon
        item.type = 'video'
        item.complete = False
        item.description = description

        images = data.get('stills', None)
        if images:
            # there were images in the stills
            item.thumb = images[-1]['url']
        elif image:
            # no stills, or empty, check for image
            item.thumb = image

        item.SetDate(broadcasted.year, broadcasted.month, broadcasted.day, broadcasted.hour, broadcasted.minute,
                     broadcasted.second)

        return item

    def CreateFolderItemAlpha(self, resultSet):
        """Creates a MediaItem of type 'folder' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(strig) - the resultSet of the self.folderItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        item = self.CreateVideoItemNonMobile(resultSet)
        item.type = 'folder'
        item.url = "http://www.npo.nl/series/%s/search?media_type=broadcast&start_date=&end_date=&start=0&rows=%s" \
                   % (item.url, self.nonMobilePageSize)
        return item

    def CreateFolderItemNonMobile(self, resultSet):
        """Creates a MediaItem of type 'folder' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(strig) - the resultSet of the self.folderItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        # Used for paging in the episode listings
        Logger.Trace(resultSet)

        if "Page" in resultSet and resultSet["Page"]:
            # page from date search result
            title = "\a.: Meer programma's :."
            page = int(resultSet["Page"])
            url = self.parentItem.url.replace("page=%s" % (page, ), "page=%s" % (page + 1, ))

            # if "page=" in self.parentItem.url:
            #     url = self.parentItem.url.replace("page=%s" % (page, ), "page=%s" % (page + 1, ))
            # elif "/zoeken?" in self.parentItem.url:
            #     url = "%s&page=%s" % (self.parentItem.url, page + 1)
            # else:
            #     url = "%s?page=%s" % (self.parentItem.url, page + 1)

            item = mediaitem.MediaItem(title, url)
            item.description = "Meer items ophalen."
            item.thumb = self.parentItem.thumb
            item.icon = self.parentItem.icon
            item.type = 'folder'
            item.fanart = self.parentItem.fanart
            item.HttpHeaders["X-Requested-With"] = "XMLHttpRequest"
            item.HttpHeaders["Accept"] = "text/html, */*; q=0.01"
            item.complete = True
            return item
        else:
            # page from episode list
            totalSize = int(resultSet["Total"])
            currentPage = int(resultSet["CurrentStart"])
            currentPageSize = int(resultSet["PageSize"])
            nextPage = currentPage + currentPageSize
            if nextPage >= totalSize:
                Logger.Debug("Not adding next page item. All items displayed (Total=%s vs Current=%s)",
                             totalSize, nextPage)
                return None
            else:
                pageSize = self.nonMobileMaxPageSize
                Logger.Debug("Adding next page item starting at %s and with %s items (Total=%s)",
                             nextPage, pageSize, totalSize)

                url = self.parentItem.url
                url = url.replace("start=%s" % (currentPage,), "start=%s" % (nextPage,))
                url = url.replace("rows=%s" % (currentPageSize,), "rows=%s" % (pageSize, ))

                pageItem = mediaitem.MediaItem("\a.: Meer afleveringen :.", url)
                pageItem.thumb = self.parentItem.thumb
                pageItem.complete = True
                pageItem.SetDate(2200, 1, 1, text="")
                return pageItem

    def CreateVideoItemNonMobile(self, resultSet):
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

        name = resultSet["Title"].strip()
        videoId = resultSet["WhatsOnId"]
        description = resultSet["Description"]

        item = mediaitem.MediaItem(name, videoId)
        item.icon = self.icon
        item.type = 'video'
        item.complete = False
        item.description = description
        item.thumb = resultSet["Image"].replace("s174/c174x98", "s348/c348x196")
        if item.thumb.startswith("//"):
            item.thumb = self.noImage

        try:
            if "Year" in resultSet:
                year = resultSet["Year"]
                if "MonthName" in resultSet:
                    month = DateHelper.GetMonthFromName(resultSet["MonthName"], "nl")
                else:
                    month = resultSet["Month"]

                day = resultSet["Day"]
                hour = resultSet.get("Hour", "0")
                minute = resultSet.get("Minutes", "0")
                item.SetDate(year, month, day, hour, minute, 0)
        except:
            Logger.Warning("Could not set date", exc_info=True)
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

        if "/radio/" in item.url or "/live/" in item.url or "/LI_3FM" in item.url:
            Logger.Info("Updating Live item: %s", item.url)
            return self.UpdateVideoItemLive(item)

        whatson_id = item.url
        return self.__UpdateVideoItem(item, whatson_id)

    def CreateLiveRadioFolder(self, resultSet):
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

        name = resultSet[1]
        name = name.replace("-", " ").capitalize()

        item = mediaitem.MediaItem(name, "%s/radio/%s" % (self.baseUrlLive, resultSet[1]))

        if resultSet[2].startswith("http"):
            item.thumb = resultSet[2].replace("regular_", "").replace("larger_", "")
        elif resultSet[2].startswith("//"):
            item.thumb = "http:%s" % (resultSet[2].replace("regular_", "").replace("larger_", ""),)
        else:
            item.thumb = "%s%s" % (self.baseUrlLive, resultSet[2].replace("regular_", "").replace("larger_", ""))

        item.icon = self.icon
        item.isLive = True
        return item

    def CreateLiveTv(self, resultSet):
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

        Logger.Trace("Content = %s", resultSet)

        # first regex matched -> video channel
        name = resultSet[1]
        name = name.replace("-", " ").capitalize()
        name = "%s: %s" % (name, resultSet[2].strip())
        description = "Nu: %s\nStraks om %s: %s" % (resultSet[2].strip(), resultSet[3], resultSet[4].strip())

        item = mediaitem.MediaItem(name, "%s/live/%s" % (self.baseUrlLive, resultSet[1]), type="video")
        item.description = description

        if resultSet[0].startswith("http"):
            item.thumb = resultSet[0].replace("regular_", "").replace("larger_", "")
        elif resultSet[0].startswith("//"):
            item.thumb = "http:%s" % (resultSet[0].replace("regular_", "").replace("larger_", ""),)
        else:
            item.thumb = "%s%s" % (self.baseUrlLive, resultSet[0].replace("regular_", "").replace("larger_", ""))

        item.icon = self.icon
        item.complete = False
        item.isLive = True
        return item

    def CreateLiveTv2(self, resultSet):
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

        if resultSet[1] in ('npo-1', 'npo-2', 'npo-3', 'npo-nieuws', 'npo-cultura', 'npo-101', 'npo-politiek',
                            'npo-best', 'npo-doc', 'npo-zappxtra', 'npo-humor-tv''npo-1', 'npo-2', 'npo-3',
                            'npo-nieuws', 'npo-cultura', 'npo-101', 'npo-politiek', 'npo-best', 'npo-doc',
                            'npo-zappxtra', 'npo-humor-tv'):
            # We already have those
            return None

        # first regex matched -> video channel
        name = resultSet[1]
        name = name.replace("-", " ").capitalize()

        item = mediaitem.MediaItem(name, "%s/%s/%s" % (self.baseUrlLive, resultSet[0], resultSet[1]), type="video")

        if resultSet[2].startswith("http"):
            item.thumb = resultSet[2].replace("regular_", "").replace("larger_", "")
        elif resultSet[2].startswith("//"):
            item.thumb = "http:%s" % (resultSet[2].replace("regular_", "").replace("larger_", ""),)
        else:
            item.thumb = "%s%s" % (self.baseUrlLive, resultSet[2].replace("regular_", "").replace("larger_", ""))
        item.icon = self.icon
        item.complete = False
        item.isLive = True
        return item

    def CreateLiveRadio(self, resultSet):
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

        Logger.Trace("Content = %s", resultSet)

        item = mediaitem.MediaItem(resultSet[1], resultSet[0], type="video")
        item.thumb = self.parentItem.thumb

        item.icon = self.icon
        item.complete = False
        item.isLive = True
        return item

    def UpdateVideoItemLive(self, item):
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

        Logger.Debug('Starting UpdateVideoItem: %s', item.name)

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()

        if item.url.startswith("http://ida.omroep.nl/aapi/"):
            # we already have the m3u8
            actualStreamData = UriHandler.Open(item.url, proxy=self.proxy, referer=self.baseUrlLive)
            self.__AppendM3u8ToPart(part, actualStreamData)
        else:
            # we need to determine radio or live tv
            Logger.Debug("Fetching live stream data")
            htmlData = UriHandler.Open(item.url, proxy=self.proxy)

            mp3Urls = Regexer.DoRegex("""data-streams='{"url":"([^"]+)","codec":"[^"]+"}'""", htmlData)
            if len(mp3Urls) > 0:
                Logger.Debug("Found MP3 URL")
                part.AppendMediaStream(mp3Urls[0], 192)
            else:
                jsonUrl = item.url
                if not item.url.startswith("http://e.omroep.nl/metadata/"):
                    Logger.Debug("Finding the actual metadata url from %s", item.url)
                    jsonUrls = Regexer.DoRegex('<div class="video-player-container"[^>]+data-prid="([^"]+)"', htmlData)
                    jsonUrl = None
                    for url in jsonUrls:
                        jsonUrl = "http://e.omroep.nl/metadata/%s" % (url,)

                jsonData = UriHandler.Open(jsonUrl, proxy=self.proxy)
                json = JsonHelper(jsonData, Logger.Instance())

                # we need an hash code
                hashCode = self.__GetHashCode(item)
                for stream in json.GetValue("streams"):
                    if stream['type'] == "hls":
                        url = stream['url']

                        # http://ida.omroep.nl/aapi/?type=jsonp&stream=http://livestreams.omroep.nl/live/npo/thematv/journaal24/journaal24.isml/journaal24.m3u8
                        Logger.Debug("Opening IDA server for actual URL retrieval")
                        actualStreamData = UriHandler.Open("http://ida.omroep.nl/aapi/?stream=%s&token=%s" % (url, hashCode),
                                                           proxy=self.proxy, referer=self.baseUrlLive)
                        self.__AppendM3u8ToPart(part, actualStreamData)

                thumbs = json.GetValue('images', fallback=None)
                if thumbs:
                    item.thumb = thumbs[-1]['url']

        item.complete = True
        # Logger.Trace(item)
        return item

    def GetDefaultCachePath(self):
        """ returns the default cache path for this channel"""

        # set the UZG path
        if AddonSettings.GetUzgCacheDuration() > 0:
            cachPath = AddonSettings.GetUzgCachePath()
            if cachPath:
                Logger.Trace("UZG Cache path resolved to: %s", cachPath)
                return cachPath

        cachePath = chn_class.Channel.GetDefaultCachePath(self)
        Logger.Trace("UZG Cache path resolved chn_class default: %s", cachePath)
        return cachePath

    # noinspection PyUnusedLocal
    def SearchSite(self, url=None):  # @UnusedVariable
        """Creates an list of items by searching the site

        Returns:
        A list of MediaItems that should be displayed.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        """
        # url = "%s/episodes/search/%s.json" % (self.baseUrl, "%s")
        url = "http://www.npo.nl/zoeken?av_type=video&document_type=program&q=%s&page=1"
        return chn_class.Channel.SearchSite(self, url)

    def CtMnDownload(self, item):
        """ downloads a video item and returns the updated one
        """
        #noinspection PyUnusedLocal
        item = self.DownloadVideoItem(item)

    def __AppendM3u8ToPart(self, part, idaData):
        actualStreamJson = JsonHelper(idaData, Logger.Instance())
        m3u8Url = actualStreamJson.GetValue('stream')

        # now we have the m3u8 URL, but it will do a HTML 302 redirect
        (headData, m3u8Url) = UriHandler.Header(m3u8Url, proxy=self.proxy)  # : @UnusedVariables

        for s, b in M3u8.GetStreamsFromM3u8(m3u8Url, self.proxy):
            part.AppendMediaStream(s, b)

    def __UpdateVideoItem(self, item, episodeId):
        """Updates an existing MediaItem with more data.

        Arguments:
        item      : MediaItem - the MediaItem that needs to be updated
        episodeId : String    - The episodeId, e.g.: VARA_xxxxxx

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

        Logger.Trace("Using Generic UpdateVideoItem method")

        # get the subtitle
        subTitleUrl = "http://e.omroep.nl/tt888/%s" % (episodeId,)
        subTitlePath = subtitlehelper.SubtitleHelper.DownloadSubtitle(subTitleUrl, episodeId + ".srt", format='srt',
                                                                      proxy=self.proxy)

        # we need an hash code
        hashCode = self.__GetHashCode(item)

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()
        part.Subtitle = subTitlePath

        # then we fetch alternative streams locations and start with the non-adapative ones
        streamsUrls = []
        directStreamVideos = AddonSettings.GetUzgCacheDuration() == 0
        streamSource = [
            "http://ida.omroep.nl/odi/?prid=%s&puboptions=h264_bb,h264_sb,h264_std&adaptive=no&part=1&token=%s" % (
                episodeId, hashCode,)]
        if directStreamVideos:
            # if we stream, then we first look for adaptive streams
            Logger.Debug("UZG is configured to streams, so also check for the adaptive streams")
            streamSource.insert(0,
                                "http://ida.omroep.nl/odi/?prid=%s&puboptions=adaptive&adaptive=yes&part=1&token=%s" % (
                                    episodeId, hashCode,))
        else:
            Logger.Debug("UZG is configured to download. Not going to fetch the adaptive streams")

        # get the actual stream locations streams:
        for streamSourceUrl in streamSource:
            streamUrlData = UriHandler.Open(streamSourceUrl, proxy=self.proxy, noCache=True)
            streamJson = JsonHelper(streamUrlData, logger=Logger.Instance())
            for url in streamJson.GetValue('streams'):
                Logger.Trace("Going to look for streams in: %s", url)
                streamsUrls.append(url)

        # should we cache before playback
        if not directStreamVideos:
            part.CanStream = False

        # now we should now actually go and fetch urls
        for url in streamsUrls:
            data = UriHandler.Open(url, proxy=self.proxy)
            jsonData = JsonHelper(data, logger=Logger.Instance())

            # check for errors
            streamData = jsonData.GetValue()
            if "errorstring" in streamData:
                Logger.Warning("Found error response: %s", streamData["errorstring"])
                continue

            # either do m3u8 or hls
            if "m3u8" in url.lower():
                Logger.Trace("Processing M3U8 Json: %s", url)
                m3u8url = jsonData.GetValue("url")
                if m3u8url is None:
                    Logger.Warning("Could not find stream in: %s", m3u8url)
                    continue
                Logger.Trace("Processing M3U8 Streams: %s", m3u8url)

                for s, b in M3u8.GetStreamsFromM3u8(m3u8url, self.proxy):
                    item.complete = True
                    part.AppendMediaStream(s, b)

                # if we found an adaptive m3u8, we take that one as it's better
                Logger.Info("Found M3u8 streams and using those. Stop looking further for non-adaptive ones.")
                break
            else:
                Logger.Trace("Processing HLS: %s", url)
                if "h264_bb" in url:
                    bitrate = 500
                elif "h264_sb" in url:
                    bitrate = 220
                elif "h264_std" in url:
                    bitrate = 1000
                else:
                    bitrate = None

                protocol = jsonData.GetValue('protocol')
                if protocol:
                    url = "%s://%s%s" % (protocol, jsonData.GetValue('server'), jsonData.GetValue('path'))
                    part.AppendMediaStream(url, bitrate=bitrate)
                else:
                    Logger.Warning("Found UZG Stream without a protocol. Probably a expired page.")

        if not item.HasMediaItemParts():
            Logger.Warning("Apparently no streams were present in the normal places. Trying streams in metadata")

            # fetch the meta data to get more streams
            metaUrl = "http://e.omroep.nl/metadata/aflevering/%s" % (episodeId,)
            metaData = UriHandler.Open(metaUrl, proxy=self.proxy)
            metaJson = JsonHelper(metaData, logger=Logger.Instance())

            # sometimes there are streams direct in the meta data file
            directStreams = metaJson.GetValue("streams", fallback=[])
            for stream in directStreams:
                quality = stream.get("kwaliteit", 0)
                if quality == 1:
                    bitrate = 180
                elif quality == 2:
                    bitrate = 1000
                elif quality == 3:
                    bitrate = 1500
                else:
                    bitrate = 0
                part.AppendMediaStream(stream["url"], bitrate)

            # now we can get extra info from the data
            item.description = metaJson.GetValue("info")
            item.title = metaJson.GetValue('aflevering_titel')
            station = metaJson.GetValue('streamSense', 'station')

            if station.startswith('nederland_1'):
                item.icon = self.GetImageLocation("1large.png")
            elif station.startswith('nederland_2'):
                item.icon = self.GetImageLocation("2large.png")
            elif station.startswith('nederland_3'):
                item.icon = self.GetImageLocation("3large.png")
            Logger.Trace("Icon for station %s = %s", station, item.icon)

            # <image size="380x285" ratio="4:3">http://u.omroep.nl/n/a/2010-12/380x285_boerzoektvrouw_yvon.png</image>
            thumbUrls = metaJson.GetValue('images')  # , {"size": "380x285"}, {"ratio":"4:3"})
            Logger.Trace(thumbUrls)
            if thumbUrls:
                thumbUrl = thumbUrls[-1]['url']
                if "http" not in thumbUrl:
                    thumbUrl = "http://u.omroep.nl/n/a/%s" % (thumbUrl,)
            else:
                thumbUrl = self.noImage

            item.thumb = thumbUrl

        item.complete = True
        return item

    def __GetHashCode(self, item):
        tokenUrl = "http://ida.omroep.nl/npoplayer/i.js"
        tokenExpired = True
        tokenFile = "uzg-i.js"
        tokenPath = os.path.join(Config.cacheDir, tokenFile)

        # determine valid token
        if os.path.exists(tokenPath):
            mTime = os.path.getmtime(tokenPath)
            timeDiff = time.time() - mTime
            maxTime = 30 * 60  # if older than 15 minutes, 30 also seems to work.
            Logger.Debug("Found token '%s' which is %s seconds old (maxAge=%ss)", tokenFile, timeDiff, maxTime)
            if timeDiff > maxTime:
                Logger.Debug("Token expired.")
                tokenExpired = True
            elif timeDiff < 0:
                Logger.Debug("Token modified time is in the future. Ignoring token.")
                tokenExpired = True
            else:
                tokenExpired = False
        else:
            Logger.Debug("No Token Found.")

        if tokenExpired:
            Logger.Debug("Fetching a Token.")
            tokenData = UriHandler.Open(tokenUrl, proxy=self.proxy, noCache=True)
            tokenHandle = file(tokenPath, 'w')
            tokenHandle.write(tokenData)
            tokenHandle.close()
            Logger.Debug("Token saved for future use.")
        else:
            Logger.Debug("Reusing an existing Token.")
            # noinspection PyArgumentEqualDefault
            tokenHandle = file(tokenPath, 'r')
            tokenData = tokenHandle.read()
            tokenHandle.close()

        token = Regexer.DoRegex('npoplayer.token = "([^"]+)', tokenData)[-1]
        actualToken = self.__SwapToken(token)
        Logger.Info("Found NOS token: %s\n          was: %s\nfor %s", actualToken, token, item)
        return actualToken

    def __SwapToken(self, token):
        """ Swaps some chars of the token to make it a valid one. NPO introduced this in july 2015

        @param token: the original token from their file.

        @return: the swapped version

        """

        first = -1
        second = -1
        startAt = 5
        Logger.Debug("Starting Token swap at position in: %s %s %s", token[0:startAt], token[startAt:len(token) - startAt], token[len(token) - startAt:])
        for i in range(startAt, len(token) - startAt, 1):
            # Logger.Trace("Checking %s", token[i])
            if token[i].isdigit():
                if first < 0:
                    first = i
                    Logger.Trace("Storing first digit at position %s: %s", first, token[i])
                elif second < 0:
                    second = i
                    Logger.Trace("Storing second digit at position %s: %s", second, token[i])
                    break

        # swap them
        newToken = list(token)
        if first < 0 or second < 0:
            Logger.Debug("No number combo found in range %s. Swapping middle items", token[startAt:len(token) - startAt])
            first = 12
            second = 13

        Logger.Debug("Swapping position %s with %s", first, second)
        newToken[first] = token[second]
        newToken[second] = token[first]
        newToken = ''.join(newToken)
        return newToken

    def __GetThumbUrl(self, thumbnails):
        """ fetches the thumburl from an coded string

        Arguments:
        thumbnails  : string - a list of thumbnails in the format:
                               &quot;<URL>&quot;,&quot;<URL>&quote;

        returns the URL of single thumb

        """

        # thumb splitting
        if len(thumbnails) > 0:
            thumbnails = thumbnails.split(';')
            # Logger.Trace(thumbnails)
            thumbUrl = thumbnails[1].replace('140x79', '280x158').replace('60x34', '280x158').replace("&quot", "")
            # Logger.Trace(thumbUrl)
        else:
            thumbUrl = ""

        return thumbUrl

    def __IgnoreCookieLaw(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.Info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        # the rfc2109 parameters is not valid in Python 2.4 (Xbox), so we ommit it.
        c = cookielib.Cookie(version=0, name='site_cookie_consent', value='yes', port=None, port_specified=False,
                             domain='.www.uitzendinggemist.nl', domain_specified=True, domain_initial_dot=False,
                             path='/', path_specified=True, secure=False, expires=2327431273, discard=False,
                             comment=None, comment_url=None, rest={'HttpOnly': None})  # , rfc2109=False)
        UriHandler.Instance().cookieJar.set_cookie(c)

        # a second cookie seems to be required
        c = cookielib.Cookie(version=0, name='npo_cc', value='tmp', port=None, port_specified=False,
                             domain='.www.uitzendinggemist.nl', domain_specified=True, domain_initial_dot=False,
                             path='/', path_specified=True, secure=False, expires=2327431273, discard=False,
                             comment=None, comment_url=None, rest={'HttpOnly': None})  # , rfc2109=False)
        UriHandler.Instance().cookieJar.set_cookie(c)

        # the rfc2109 parameters is not valid in Python 2.4 (Xbox), so we ommit it.
        c = cookielib.Cookie(version=0, name='site_cookie_consent', value='yes', port=None, port_specified=False,
                             domain='.www.npo.nl', domain_specified=True, domain_initial_dot=False, path='/',
                             path_specified=True, secure=False, expires=2327431273, discard=False, comment=None,
                             comment_url=None, rest={'HttpOnly': None})  # , rfc2109=False)
        UriHandler.Instance().cookieJar.set_cookie(c)

        # Set-Cookie: npo_cc=30; path=/; domain=www.npo.nl; expires=Tue, 09-Aug-2044 21:55:39 GMT
        c = cookielib.Cookie(version=0, name='npo_cc', value='30', port=None, port_specified=False,
                             domain='.www.npo.nl', domain_specified=True, domain_initial_dot=False, path='/',
                             path_specified=True, secure=False, expires=2327431273, discard=False, comment=None,
                             comment_url=None, rest={'HttpOnly': None})  # , rfc2109=False)
        UriHandler.Instance().cookieJar.set_cookie(c)

        # http://pilot.odcontent.omroep.nl/codem/h264/1/nps/rest/2013/NPS_1220255/NPS_1220255.ism/NPS_1220255.m3u8
        # balancer://sapi2cluster=balancer.sapi2a

        # c = cookielib.Cookie(version=0, name='balancer://sapi2cluster', value='balancer.sapi2a', port=None, port_specified=False, domain='.pilot.odcontent.omroep.nl', domain_specified=True, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=2327431273, discard=False, comment=None, comment_url=None, rest={'HttpOnly': None})  # , rfc2109=False)
        # UriHandler.Instance().cookieJar.set_cookie(c)
        # c = cookielib.Cookie(version=0, name='balancer://sapi1cluster', value='balancer.sapi1a', port=None, port_specified=False, domain='.pilot.odcontent.omroep.nl', domain_specified=True, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=2327431273, discard=False, comment=None, comment_url=None, rest={'HttpOnly': None})  # , rfc2109=False)
        # UriHandler.Instance().cookieJar.set_cookie(c)
        return

    def __TokenTest(self):
        # some test cases
        tokenTests = {
            "kouansr1o89hu1u0lnr20b6f60": "kouansr8o19hu1u0lnr20b6f60",
            "h05npjekmn478nhfqft7g2i6q1": "h05npjekmn748nhfqft7g2i6q1",
            "ncjamt9gu2d9qmg4dpu1plqd37": "ncjamt2gu9d9qmg4dpu1plqd37",
            "m9mvj51ittnuglub3ibgoptvi4": "m9mvj15ittnuglub3ibgoptvi4",
            "vgkn9j8r3135a7vf0e6992vmi1": "vgkn9j3r8135a7vf0e6992vmi1",
            "eqn86lpcdadda9ajrceedcpef3": "eqn86lpcdadd9aajrceedcpef3",
            "vagiq9ejnqbmcodtncp77uomj1": "vagiq7ejnqbmcodtncp97uomj1",
        }

        for inputToken, outputToken in tokenTests.iteritems():
            token = self.__SwapToken(inputToken)
            if token != outputToken:
                raise Exception("Token mismatch:\nInput:   %s\nOutput:  %s\nShould be: %s")
