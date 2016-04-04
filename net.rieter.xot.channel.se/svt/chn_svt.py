# coding:UTF-8
import urlparse
import datetime
import time

# import contextmenu
import chn_class
import mediaitem

from regexer import Regexer
from helpers import htmlentityhelper
from helpers.subtitlehelper import SubtitleHelper
from helpers.jsonhelper import JsonHelper
from helpers.xmlhelper import XmlHelper
from helpers.datehelper import DateHelper
from xbmcwrapper import XbmcWrapper
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
        self.useAtom = False  # : The atom feeds just do not give all videos
        self.noImage = "svtimage.png"

        # setup the urls
        self.mainListUri = "http://www.svtplay.se/program"
        # self.baseUrl = "http://www.svtplay.se/ajax/sok/forslag.json"
        self.baseUrl = "http://www.svtplay.se"
        self.swfUrl = "%s/public/swf/video/svtplayer-2013.23.swf" % (self.baseUrl,)

        # Generic pre-processor
        self._AddDataParser("*", preprocessor=self.PreProcessFolderList)

        # setup the intial listing based on Alphabeth and specials
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
                            preprocessor=self.AddLiveItems)
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
                            preprocessor=self.AddShowItems)

        # setup channel listing
        self._AddDataParser("#kanaler",
                            preprocessor=self.LoadChannelData,
                            json=True,
                            parser=("channels", ),
                            creator=self.CreateChannelItem)
        self._AddDataParser("http://www.svt.se/videoplayer-api/", updater=self.UpdateChannelItem)

        # genres (using JSON)
        self._AddDataParser("http://www.svtplay.se/genre/",
                            preprocessor=self.ExtractJsonData, json=True,
                            parser=("context", "dispatcher", "stores", "ClusterStore", "titles"),
                            creator=self.CreateJsonItem)

        # special pages (using JSON)
        self._AddDataParser("^http://www.svtplay.se/(senaste|sista-chansen|populara)\?sida=\d+$",
                            matchType=ParserData.MatchRegex, preprocessor=self.ExtractJsonData)
        self._AddDataParser("^http://www.svtplay.se/(senaste|sista-chansen|populara)\?sida=\d+$",
                            matchType=ParserData.MatchRegex, json=True,
                            parser=("context", "dispatcher", "stores", "GridStore", "content"),
                            creator=self.CreateJsonItem)
        self._AddDataParser("^http://www.svtplay.se/(senaste|sista-chansen|populara)\?sida=\d+$",
                            matchType=ParserData.MatchRegex, json=True,
                            parser=("context", "dispatcher", "stores", "MetaStore"),
                            creator=self.CreateJsonPageItem)

        # setup the normal video items
        liveItemRegex = '<a href="/((?:live|video)/\d+)[\W\w]{0,2000}?<time\W+datetime="(\d+)-(\d+)-(\d+)T' \
                        '(\d+):(\d+)\+\d+:\d+">\d+[:.]\d+</time>[^/]+</time>\W+</(?:span|div)>\W+<(?:div[^>]+>' \
                        '|h5|h1[^>]+>|span[^>]+>)([^<]+)'
        videoItemRegex = '<img[^>]+src="([^"]+)" />\W+<span class="play_vertical[^"]+?(only-sweden){0,1}">[\w\W]{0,1500}?<a href="/((?:live|video|klipp)/\d+)[^>]+>([^<]+)<[\w\W]{0,1500}?<p[^>]+description-text"\W*>([^<]+)<'

        self.videoItemRegex = (videoItemRegex, liveItemRegex)
        self._AddDataParser("*", parser=self.videoItemRegex, creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        # setup the categories
        catRegex = Regexer.FromExpresso('<article[^>]+data-title="(?<Title>[^"]+)"[^"]+data-description="(?<Description>[^"]*)"[^>]+data-broadcasted="(?:(?<Date1>[^ "]+) (?<Date2>[^. "]+)[ .](?<Date3>[^"]+))?"[^>]+data-abroad="(?<Abroad>[^"]+)"[^>]+>\W+<a[^>]+href="(?<Url>[^"]+)"[\w\W]{0,5000}?<img[^>]+src="(?<Thumb>[^"]+)')
        self._AddDataParser("^http://www.svtplay.se/[^/?]+\?tab=titlar$", matchType=ParserData.MatchRegex,
                            preprocessor=self.StripNonCategories, parser=catRegex, creator=self.CreateCategoryItem)
        self._AddDataParser("http://www.svtplay.se/sok", parser=catRegex, creator=self.CreateCategoryItem)
        # self._AddDataParser("^http://www.svtplay.se/[^/?]+\?tab=titlar$", matchType=ParserData.MatchRegex,
        #                     parser=extendedRegex, creator=self.CreateVideoItemExtended)

        # set the more items
        moreitemsRegex = 'tab=(\w+)[^>]+data-target="play_title-page__content--more-\w+">'
        self._AddDataParser("*", parser=moreitemsRegex, creator=self.CreateMoreItem)

        self.mediaUrlRegex = '"url":"([^"]+)","bitrate":(\d+)'

        self.atomItemRegex = "<entry>.+</entry>"
        if self.useAtom:
            # self.videoItemRegex = self.atomItemRegex
            # self.CreateVideoItem = self.CreateVideoItemXml
            self._AddDataParser("*", parser=self.atomItemRegex, creator=self.CreateVideoItemXml)

        # ===============================================================================================================
        # non standard items
        # self.categoryName = ""
        # self.currentUrlPart = ""
        self.__klippName = LanguageHelper.GetLocalizedString(LanguageHelper.Clips)
        self.__klippUrlIndicator = "tab=klipp"

        # ===============================================================================================================
        # Test cases:
        #   Östnytt: /klipp
        #   Alfons Åberg: pages, /klipp /video, folders, subtitles
        #   Nobel: Live channels / klipps / subtitles
        #
        #   artists_in_residence - FLV

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

    def AddShowItems(self, data):
        """ Adds the shows from the alpabetical list

        @param data:    The data to use.

        Returns a list of MediaItems that were retrieved.

        """

        items = []

        # add the json data as the actual data
        dataStart = 'root["__svtplay"] = '
        dataStartLen = len(dataStart)
        dataStart = data.index(dataStart)
        dataEnd = data.index(';root["__svtplay"].env')
        data = data[dataStart + dataStartLen:dataEnd]
        json = JsonHelper(data)
        alphaList = json.GetValue('context', 'dispatcher', 'stores', 'ProgramsStore', 'alphabeticList')
        for alpha in alphaList:
            for show in alpha['titles']:
                items.append(self.CreateEpisodeItemJson(show))
        return data, items

    def AddLiveItems(self, data):
        """ Adds the Live items, Channels and Last Episodes to the listing.

        @param data:    The data to use.

        Returns a list of MediaItems that were retrieved.

        """

        items = []

        extraItems = {
            "Kanaler": "#kanaler",
            "Livesändningar": "http://www.svtplay.se/ajax/live?sida=1",

            "S&ouml;k": "searchSite",
            "Senaste program": "http://www.svtplay.se/senaste?sida=1",
            "Sista chansen": "http://www.svtplay.se/sista-chansen?sida=1",
            "Populära": "http://www.svtplay.se/populara?sida=1",
        }

        # http://www.svtplay.se/ajax/dokumentar/titlar?filterAccessibility=&filterRights=
        categoryItems = {
            "Drama": "http://www.svtplay.se/genre/drama",
            "Barn": "http://www.svtplay.se/barn?tab=titlar",
            "Dokumentär": "http://www.svtplay.se/dokumentar?tab=titlar",
            "Kultur & Nöje": "http://www.svtplay.se/kulturochnoje?tab=titlar",
            "Nyheter": "http://www.svtplay.se/nyheter?tab=titlar",
            "Samhälle & Fakta": "http://www.svtplay.se/samhalleochfakta?tab=titlar",
            "Sport": "http://www.svtplay.se/sport?tab=titlar",
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
        for title, url in categoryItems.iteritems():
            catItem = mediaitem.MediaItem(title, url)
            catItem.complete = True
            catItem.thumb = self.noImage
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

    def ExtractJsonData(self, data):
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
        data = Regexer.DoRegex('root\["__svtplay"\] = ([\w\W]+?);root\[', data)[-1]
        items = []
        Logger.Trace("JSON data found: %s", data)
        return data, items

    def CreateEpisodeItemJson(self, resultSet):
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
        url = "%s/%s?tab=program" % (self.baseUrl, resultSet['urlFriendlyTitle'], )
        item = mediaitem.MediaItem(resultSet['title'], url)
        item.icon = self.icon
        item.thumb = self.noImage
        item.isGeoLocked = resultSet.get('onlyAvailableInSweden', False)
        return item

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
        Logger.Trace(resultSet)
        url = htmlentityhelper.HtmlEntityHelper.StripAmp(urlparse.urljoin(self.baseUrl, resultSet[1]))

        if not self.useAtom:
            # if we put page 20, we usually get all items.
            # url = "%s?tab=program&sida=100&antal=100" % (url, )
            url = "%s?tab=program" % (url, )
            # url = "%s?sida=2&tab=helaprogram&embed=true" % (url, )
            # url = "%s?sida=100&tab=helaprogram" % (url, )
        else:
            url = "%s/atom.xml" % (url, )

        item = mediaitem.MediaItem(resultSet[2], url)
        item.icon = self.icon
        item.thumb = self.noImage
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
        title = resultSet["programTitle"]
        showTitle = resultSet.get("title", "")
        if showTitle != "" and showTitle != title:
            title = "%s - %s" % (title, showTitle)
        itemType = resultSet["contentType"]
        url = resultSet["contentUrl"]
        broadCastDate = resultSet.get("broadcastDate", None)

        if itemType == "videoEpisod":
            if not url.startswith("/video/"):
                Logger.Warning("Found video item without a /video/ url.")
                return None
            itemType = "video"
            url = url.split("/")
            # Logger.Trace(url)
            url = "%s/video/%s?type=embed&output=json" % (self.baseUrl, url[2])
        else:
            itemType = "folder"
            url = "%s%s?tab=program" % (self.baseUrl, url)

        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.type = itemType
        item.isGeoLocked = resultSet.get("onlyAvailableInSweden", False)
        item.description = resultSet.get("description", "")

        # thumb = resultSet.get("imageMedium", self.noImage).replace("/medium/", "/extralarge/")
        thumb = resultSet.get("imageMedium", self.noImage).replace("/medium/", "/large/")
        if thumb.startswith("//"):
            thumb = "http:%s" % (thumb, )
        item.thumb = thumb

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
        else:
            # make sure we get the right tab for displaying
            item.url = "%s?tab=program" % (item.url, )

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

        if "live=1" in self.parentItem.url:
            # don't add folders, this should no longer be the case as we use AJAX pages now.
            start = data.find('<div class="svtUnit svtNth-1">')
            end = data.find('<div class="playBoxContainer playBroadcastItemLast">')
            Logger.Debug("Stripping folders for live items")
            return data[start:end], items

        # if "=klipp" in self.parentItem.url:
        # self.pageNavigationRegex = self.pageNavigationRegexBase % ("klipp", )
        # elif "tab=news" in self.parentItem.url:
        # self.pageNavigationRegex = self.pageNavigationRegexBase % ("news", )
        # else:
        #     self.pageNavigationRegex = self.pageNavigationRegexBase % ("program", )
        # Logger.Debug("PageNav Regex set to: %s", self.pageNavigationRegex)

        end = data.find('<div id="playJs-videos-in-same-category" ')
        Logger.Debug("Stripping from position: %s", end)
        data = data[:end]

        if '<a href="?tab=klipp"' in data and self.parentItem.name != self.__klippName:
            klippItem = mediaitem.MediaItem(self.__klippName,
                                            self.parentItem.url.replace("tab=program", self.__klippUrlIndicator))
            klippItem.icon = self.icon
            klippItem.thumb = self.parentItem.thumb
            klippItem.complete = True
            items.append(klippItem)

        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateMoreItem(self, resultSet):
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

        if resultSet == "klipp" and self.__klippUrlIndicator not in self.parentItem.url:
            return None

        more = LanguageHelper.GetLocalizedString(LanguageHelper.MorePages)

        item = mediaitem.MediaItem(more, "%s&sida=2&embed=true" % (self.parentItem.url, ))
        item.thumb = self.parentItem.thumb
        item.icon = self.parentItem.icon
        item.type = 'folder'
        item.httpHeaders = self.httpHeaders
        item.complete = True
        return item

    def CreateVideoItemXml(self, resultSet):
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

        xmlData = XmlHelper(resultSet)
        title = xmlData.GetSingleNodeContent("title")
        url = xmlData.GetTagAttribute("link", {"rel": "alternate"}, {"href": None})
        description = xmlData.GetSingleNodeContent("description")
        date = xmlData.GetSingleNodeContent("updated")

        item = mediaitem.MediaItem(title, url)
        item.type = 'video'
        item.description = description
        thumbUrl = xmlData.GetTagAttribute("link", {"rel": "enclosure"}, {"href": None})
        if thumbUrl:
            thumbUrl = thumbUrl.replace("/medium/", "/large/")  # or extralarge
            if thumbUrl.startswith("//"):
                thumbUrl = "http:%s" % (thumbUrl, )
            item.thumb = thumbUrl
        else:
            item.thumb = self.noImage

        item.complete = False
        Logger.Trace("%s - %s - %s - %s - %s", title, description, date, thumbUrl, url)
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
        return None

    def CreateVideoItemExtended(self, resultSet):
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

        year = month = day = hour = minutes = 0
        isLive = False

        url = "http://www.svtplay.se/%s?type=embed&output=json" % (resultSet[9])
        thumb = resultSet[10]
        thumb = thumb.replace("small", "large").replace("medium", "large").replace(" ", "%20")

        name = resultSet[0].replace('\n', '')

        if "/klipp/" in url and self.parentItem.name != self.__klippName:
            # Klipp in episodes list
            Logger.Trace("Klipp in episode list: %s", url)
            return None
        elif "/klipp/" not in url and self.parentItem.name == self.__klippName:
            # Episode in klipp list
            Logger.Trace("Episode in klipp list: %s", url)
            return None

        # if "/klipp/" in url:
        # name = "[Klipp] %s" % (name,)

        description = resultSet[1]
        if resultSet[2] == "imorgon":
            # no need to show future episodes
            return None

        if resultSet[2]:
            year, month, day, hour, minutes = self.__GetDate(resultSet[2], resultSet[3], resultSet[4])

        if resultSet[5]:
            year, month, day, hour, minutes = self.__GetDate(resultSet[5], resultSet[6], resultSet[7])

        geoLocked = resultSet[8] == "false"

        item = mediaitem.MediaItem(name, url)
        item.type = 'video'
        if year > 0:
            item.SetDate(year, month, day, hour, minutes, 0)

        if not thumb:
            item.thumb = self.noImage
        else:
            if thumb.startswith("//"):
                item.thumb = "http:%s" % (thumb, )
            elif not thumb.startswith("http"):
                item.thumb = "%s%s" % (self.baseUrl, thumb)
            else:
                item.thumb = thumb

        item.icon = self.icon
        item.complete = False
        item.description = description
        item.isLive = isLive
        item.isGeoLocked = geoLocked
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

        name = url = thumb = description = None
        year = month = day = hour = minutes = 0
        isLive = False
        geoLocked = False
        if resultSet[0] == 0:  # first regex match
            geoLocked = resultSet[2] == "only-sweden"

            url = "http://www.svtplay.se/%s?type=embed&output=json" % (resultSet[3])
            # if not resultSet[11]:
            #     thumb = resultSet[12]
            # else:
            thumb = resultSet[1]
            thumb = thumb.replace("small", "large").replace("medium", "large").replace(" ", "%20")
            if thumb.startswith("//"):
                thumb = "http:%s" % (thumb, )

            name = resultSet[4].replace('\n', '')

            if "/klipp/" in url and self.__klippUrlIndicator not in self.parentItem.url:
                # Klipp in episodes list
                Logger.Trace("Klipp in episode list: %s", url)
                return None
            elif "/klipp/" not in url and self.__klippUrlIndicator in self.parentItem.url:
                # Episode in klipp list
                Logger.Trace("Episode in klipp list: %s", url)
                return None

            # if "/klipp/" in url:
            # name = "[Klipp] %s" % (name,)

            description = resultSet[5]
            # if resultSet[3] == "imorgon":
            #     # no need to show future episodes
            #     return None
            #
            # if resultSet[3]:
            #     year, month, day, hour, minutes = self.__GetDate(resultSet[3], resultSet[4], resultSet[5])
            #
            # if resultSet[6]:
            #     year, month, day, hour, minutes = self.__GetDate(resultSet[6], resultSet[7], resultSet[8])
            #
            # geoLocked = resultSet[9] == "false"

        elif resultSet[0] == 1:  # second regex match (Live items)
            if "/live?" not in self.parentItem.url and "?tab=live" not in self.parentItem.url:
                return None

            url = "http://www.svtplay.se/%s?output=json" % (resultSet[1])
            description = ""
            year = resultSet[2]
            month = resultSet[3]
            day = resultSet[4]
            hour = resultSet[5]
            minutes = resultSet[6]
            isLive = True

            name = "%s - %s:%s (Live)" % (resultSet[7], hour, minutes)

        item = mediaitem.MediaItem(name, url)
        item.type = 'video'
        if year > 0:
            item.SetDate(year, month, day, hour, minutes, 0)

        if not thumb:
            item.thumb = self.noImage
        else:
            if thumb.startswith("//"):
                item.thumb = "http:%s" % (thumb, )
            elif not thumb.startswith("http"):
                item.thumb = "%s%s" % (self.baseUrl, thumb)
            else:
                item.thumb = thumb

        # set the date
        if resultSet[0] == 1:
            timeStamp = item.SetDate(year, month, day, hour, minutes, 0)
            # let's limit the live items for 1 week from now
            if timeStamp and timeStamp > datetime.datetime.now() + datetime.timedelta(7):
                return None

        item.icon = self.icon
        item.complete = False
        item.description = description
        item.isLive = isLive
        item.isGeoLocked = geoLocked
        return item

    def UpdateChannelItem(self, item):
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
        Logger.Trace(videos)

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()
        spoofIp = self._GetSetting("spoof_ip", "0.0.0.0")
        if spoofIp is not None:
            part.HttpHeaders["X-Forwarded-For"] = spoofIp

        for video in videos:
            # bitrate = video['bitrate']
            url = video['url']
            # player = video['playerType']
            # if "ios" in player:
            #     bitrate += 1

            if "akamaihd" in url and "f4m" in url:
                continue
                # these are not supported as they return a 503 error
                #noinspection PyUnreachableCode
                #url = url.replace("/z/", "/i/").replace("/manifest.f4m", "/master.m3u8")

            if len(filter(lambda s: s.Url == url, part.MediaStreams)) > 0:
                Logger.Debug("Skippping duplicate Stream url: %s", url)
                continue

            if "m3u8" in url:
                for s, b in M3u8.GetStreamsFromM3u8(url, proxy=self.proxy, headers=part.HttpHeaders):
                    part.AppendMediaStream(s, b)
            else:
                part.AppendMediaStream(url, 0)

        item.complete = True
        return item

    #noinspection PyUnreachableCode
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

        data = UriHandler.Open(item.url, proxy=self.proxy)
        Logger.Trace(data)

        if 'livestart":-' in data:
            Logger.Debug("Live item that has not yet begun.")
            json = JsonHelper(data, Logger.Instance())
            secondsToStart = json.GetValue("video", "livestart")
            if secondsToStart:
                secondsToStart = -int(secondsToStart)
                Logger.Debug("Seconds till livestream: %s", secondsToStart)
                timeLeft = "%s:%02d:%02d" % (secondsToStart / 3600, (secondsToStart % 3600) / 60, secondsToStart % 60)
                Logger.Debug("Live items starts at %s", timeLeft)
                lines = list(LanguageHelper.GetLocalizedString(LanguageHelper.NoLiveStreamId))
                lines[-1] = "%s ETA: %s" % (lines[-1], timeLeft)
                XbmcWrapper.ShowDialog(LanguageHelper.GetLocalizedString(LanguageHelper.NoLiveStreamTitleId),
                                       lines)
            else:
                XbmcWrapper.ShowDialog(LanguageHelper.GetLocalizedString(LanguageHelper.NoLiveStreamTitleId),
                                       LanguageHelper.GetLocalizedString(LanguageHelper.NoLiveStreamId))
            return item

        item.MediaItemParts = []
        mediaPart = item.CreateNewEmptyMediaPart()
        spoofIp = self._GetSetting("spoof_ip", "0.0.0.0")
        if spoofIp is not None:
            mediaPart.HttpHeaders["X-Forwarded-For"] = spoofIp

        # mediaPart.UserAgent = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:17.0) Gecko/20100101 Firefox/17.0"

        # isLive = False
        if '"live":true' in data or "/live/" in item.url:
            mediaPart.AddProperty("IsLive", "true")
            Logger.Debug("Live video item found.")
            # isLive = True
        else:
            Logger.Debug("Normal (not live, or possible was live) video item found")

        # replace items
        #videos = map(lambda v: self.__ReplaceClist(v), videos)

        jsonVideoData = JsonHelper(data)
        videos = jsonVideoData.GetValue("video", "videoReferences")
        # videos = Regexer.DoRegex(self.mediaUrlRegex, data)
        for video in videos:
            playerType = video.get("playerType", "")
            if "dash" in playerType:
                continue

            if video["url"].startswith("rtmp"):
                # just replace some data in the URL
                mediaPart.AppendMediaStream(self.GetVerifiableVideoUrl(video["url"]).replace("_definst_", "?slist="),
                                            video[1])

            elif "m3u8" in video["url"]:
                Logger.Info("SVTPlay.se m3u8 stream found: %s", video["url"])

                # apparently the m3u8 do not work well for server www0.c91001.dna.qbrick.com
                if "www0.c91001.dna.qbrick.com" in video["url"]:
                    continue

                # m3u8 we need to parse. Get more streams from this file.
                videoUrl = video["url"]
                altIndex = videoUrl.find("m3u8?")
                # altIndex = videoUrl.find("~uri")
                if altIndex > 0:
                    videoUrl = videoUrl[0:altIndex + 4]
                for s, b in M3u8.GetStreamsFromM3u8(videoUrl, self.proxy, headers=mediaPart.HttpHeaders):
                    item.complete = True
                    mediaPart.AppendMediaStream(s, b)

            elif "f4m" in video["url"]:
                Logger.Info("SVTPlay.se manifest.f4m stream found: %s", video["url"])

                #if "manifest.f4m?start=" in video["url"]:
                #    # this was a live stream, convert it to M3u8
                #    # http://svt06-lh.akamaihd.net/z/svt06_0@77501/manifest.f4m?start=1386566700&end=1386579600
                #    # to
                #    # http://svt06hls-lh.akamaihd.net/i/svt06_0@77501/master.m3u8?__b__=563&start=1386566700&end=1386579600
                #    m3u8Url = video["url"].replace("-lh.akamaihd.net/z", "hls-lh.akamaihd.net/i").replace("manifest.f4m?", "master.m3u8?__b__=563&")
                #    Logger.Info("Found f4m stream for an old Live stream. Converting to M3U8:\n%s -to -\n%s", video["url"], m3u8Url)
                #    videos.append((m3u8Url, 0))
                #    continue

                # for now we skip these as they do not yet work with XBMC
                continue
                # http://svtplay8m-f.akamaihd.net/z/se/krypterat/20120830/254218/LILYHAMMER-003A-mp4-,c,d,b,e,-v1-4bc7ecc090b19c82.mp4.csmil/manifest.f4m?hdcore=2.8.0&g=TZOMVRTEILSE
                #videoDataUrl = video["url"]
                # videoUrl = "%s?hdcore=2.8.0&g=TZOMVRTEILSE" % (videoDataUrl,)
                #videoUrl = "%s?hdcore=2.10.3&g=IJGTWSVWPPKH" % (videoDataUrl,)

                # metaData = UriHandler.Open(videoUrl, proxy=self.proxy, referer=self.swfUrl)
                # Logger.Debug(metaData)

                # The referer seems to be unimportant
                # header = "referer=%s" % (urllib.quote(self.swfUrl),)
                # videoUrl = "%s|%s" % (videoUrl, header)
                #mediaPart.AppendMediaStream(videoUrl, video[1])

            else:
                Logger.Info("SVTPlay.se standard HTTP stream found.")
                # else just use the URL
                mediaPart.AppendMediaStream(video["url"], video["bitrate"])

        subtitle = Regexer.DoRegex('"url":"([^"]+.wsrt)"|"url":"(http://media.svt.se/download/[^"]+.m3u8)', data)
        for sub in subtitle:
            if sub[-1]:
                Logger.Info("Found M3u8 subtitle, replacing with WSRT")
                start, name, index = sub[-1].rsplit("/", 2)
                subUrl = "%s/%s/%s.wsrt" % (start, name, name)
            else:
                subUrl = sub[0]
            mediaPart.Subtitle = SubtitleHelper.DownloadSubtitle(subUrl, format="srt", proxy=self.proxy,
                                                                 replace=SubtitleHelper.ANSIColours)

        item.complete = True
        return item

    # def __ReplaceClist(self, video):
    #     """ Replaces HTTP Dynamic streaming urls with corresponding M3U8 Urls
    #
    #     Arguments:
    #     video - Tuple - that holds the video results
    #
    #     """
    #
    #     # Logger.Trace(video)
    #     video = list(video)
    #
    #     if "akamaihd" in video[0] and "f4m" in video[0]:
    #         Logger.Info("SVTPlay.se manifest.f4m stream found: %s", video[0])
    #
    #         video[0] = video[0].replace("/z/", "/i/").replace("/manifest.f4m", "/master.m3u8")
    #         # Logger.Debug("New URL: %s", video[0])
    #
    #     # Logger.Debug(video)
    #     return video

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
