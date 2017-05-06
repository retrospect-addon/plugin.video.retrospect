import datetime
import re

import mediaitem
import chn_class

from regexer import Regexer
from helpers import subtitlehelper
# from helpers.jsonhelper import JsonHelper

from logger import Logger
from streams.npostream import NpoStream
from urihandler import UriHandler
from helpers.datehelper import DateHelper
from parserdata import ParserData
from helpers.languagehelper import LanguageHelper
from helpers.htmlentityhelper import HtmlEntityHelper
from vault import Vault


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

        # setup the urls
        if self.channelCode == "uzgjson":
            self.baseUrl = "https://apps-api.uitzendinggemist.nl"
            self.mainListUri = "#mainlist"
            # self.mainListUri = "%s/series.json" % (self.baseUrl,)
            self.noImage = "nosimage.png"
        else:
            raise NotImplementedError("Code %s is not implemented" % (self.channelCode,))

        # mainlist stuff
        self._AddDataParser("#mainlist", preprocessor=self.GetInitialFolderItems)

        # Alpha listing and paging for that list
        self._AddDataParser("#alphalisting", preprocessor=self.AlphaListing)

        # Alpha listing based on JSON interface
        self._AddDataParser("%s/series.json" % (self.baseUrl,),
                            parser=(), creator=self.CreateJsonShows,
                            json=True)

        # Use old urls with new Updater
        self._AddDataParser("http://e.omroep.nl/metadata/", name="e.omroep.nl classic parser",
                            updater=self.UpdateFromPoms)

        # live stuff
        self.baseUrlLive = "https://www.npo.nl"

        # live radio, the folders and items
        self._AddDataParser("http://radio-app.omroep.nl/player/script/",
                            name="Live Radio Streams",
                            preprocessor=self.ExtractJsonForLiveRadio, json=True,
                            parser=(), creator=self.CreateLiveRadio)

        self._AddDataParser("/live", matchType=ParserData.MatchEnd,
                            name="Main Live Stream HTML parser",
                            preprocessor=self.GetAdditionalLiveItems,
                            parser="<img[^>]+alt=\"Logo van ([^\"]+)\" [^>]+src=\"([^\"]+)\" /></a>[\w\W]{0,400}?<div class='item current-item'>\W+<div class='time now'>Nu</div>\W+<div class='description'>\W+<a[^>]+href=\"/live/([^\"]+)\"[^>]*>([^<]+)[\w\W]{0,400}?<div class='item next-item'>\W+(?:<div class='time next'>([^<]+)</div>\W+<div class='description next'>\W+<[^>]+>([^<]+)|</div>)",
                            creator=self.CreateLiveTv,
                            updater=self.UpdateVideoItemLive)

        self._AddDataParser("https://www.npo.nl/live/", name="Live Video Updater from HTML",
                            updater=self.UpdateVideoItemLive)

        # recent and popular stuff and other Json data
        self._AddDataParser(".json", name="JSON List Parser",
                            parser=(), creator=self.CreateVideoItemJson,
                            json=True, matchType=ParserData.MatchEnd)

        # json for video's if mobile mode
        self._AddDataParser("apps-api.uitzendinggemist.nl/series/",
                            parser=("episodes",), creator=self.CreateVideoItemJson,
                            json=True, matchType=ParserData.MatchContains)

        # genres
        self._AddDataParser("https://www.npo.nl", matchType=ParserData.MatchExact,
                            parser='<li><a[^>]*\.genre\.[^>]*href="[^"]+=(\d+)">([^>]+)</a></li>',
                            creator=self.CreateGenreItem)

        # Set self.nonMobilePageSize to 0 to enable mobile pages
        self.nonMobilePageSize = 50
        self.nonMobileMaxPageSize = 100

        # Non-mobile folders -> indicator if there are more items
        self.nonMobilePageRegex = "(?:data-num-found=\W(?<Total>\d+)\W data-rows=\W(?<PageSize>" \
                                  "\d+)\W data-start=\W(?<CurrentStart>\d+)\W|data-current-page=" \
                                  "'(?<CurrentPage>\d+)' data-pages='(?<TotalPages>\d+)'|" \
                                  "data-page=\W(?<Page>\d+)\W)".replace("(?<", "(?P<")
        # Non-mobile videos: for the old pages such as the 'day' pages
        self.nonMobileVideoItemRegex = 'src="(?<Image>[^"]+)"\W+>(?<Premium><div class="not-' \
                                       'available-image-overlay">)?[\w\W]{0,500}?</a></div>\W*' \
                                       '</div>\W*<div[^>]*>\W*<a[^>]*href="(?<Url>[^"]+/(?<Day>\d+)-' \
                                       '(?<Month>\d+)-(?<Year>\d+)/(?<WhatsOnId>[^/"]+))"[^>]*>' \
                                       '<h4>(?<Title>[^<]+)<[\W\w]{0,600}?<p[^>]*>(?<Description>' \
                                       '[^<]*)'.replace('(?<', '(?P<')

        # Pages based on searching
        self._AddDataParser("https://www.npo.nl/zoeken?",
                            preprocessor=self.AddNextPageItem,
                            parser=self.nonMobileVideoItemRegex,
                            creator=self.CreateVideoItemNonMobile,
                            updater=self.UpdateVideoItem)

        # The A-Z pages
        programRegex = Regexer.FromExpresso(
            '<div[^>]+strip-item[^>]+>\W+<a[^>]+href="(?<Url>[^"]+)/(?<WhatsOnId>[^"]+)"[^>]*>'
            '[^<]*</a>\W*<div[^>]*>\W*<img[^>]+data-img-src="(?<Image>[^"]+)"[\w\W]{0,1000}?'
            '<h3[^>]*>[\n\r]*(?<Title>[^<]+)[\n\r]*<')
        self._AddDataParser("^https://www.npo.nl/programmas/a-z(/[a-z])?",
                            matchType=ParserData.MatchRegex,
                            name="The A-Z Page 'video' items",
                            parser=programRegex, creator=self.CreateFolderItemAlpha)
        self._AddDataParser("^https://www.npo.nl/programmas/a-z(/[a-z])?",
                            matchType=ParserData.MatchRegex,
                            name="The A-Z Page 'page' items",
                            parser=self.nonMobilePageRegex, creator=self.CreatePageItemNonMobile)

        # favorites
        favRegex = 'data-mid=\'(?<id>[^"\']+)\'>\W*<a[^>]*href="(?<url>[^"]+)[^>]*>[^>]*</a>\W*' \
                   '<div[^>]*>\W*<img[^>]*src="(?<thumburl>[^"]+)"[^>]*>\W*</div>[\w\W]{0,400}?' \
                   '<div[^>]*title\'[^>]*>(?<title>[^<]*)</div>'
        favRegex = Regexer.FromExpresso(favRegex)
        self._AddDataParser("https://mijn.npo.nl/profiel/favorieten", name="Favourites with logon",
                            requiresLogon=True, parser=favRegex, creator=self.CreateFolderItem)

        # Non-mobile videos: for the new pages with a direct URL
        self.nonMobileVideoItemRege2 = 'src="(?<Image>[^"]+)"[^>]+>\W*</a></div>\W*<div[^>]*>\W*<h3><a href="' \
                                       '(?<Url>[^"]+/(?<Day>\d+)-(?<Month>\d+)-(?<Year>\d+)/(?<WhatsOnId>[^/"]+))"' \
                                       '[^>]*>(?<Title>[^<]+)<[\W\w]{0,600}?<p[^>]*>' \
                                       '(?<Description>[^<]*)'.replace('(?<', '(?P<')

        self._AddDataParser("*", preprocessor=self.AddNextPageItem)
        self._AddDataParser("*",
                            parser=self.nonMobileVideoItemRege2,
                            creator=self.CreateVideoItemNonMobile,
                            updater=self.UpdateVideoItem)

        self._AddDataParser("*", parser=self.nonMobileVideoItemRegex,
                            creator=self.CreateVideoItemNonMobile)
        self._AddDataParser("*", parser=self.nonMobilePageRegex,
                            creator=self.CreatePageItemNonMobile)

        # needs to be here because it will be too late in the script version
        self.__IgnoreCookieLaw()

        # ===============================================================================================================
        # non standard items
        # self.__TokenTest()
        self.__NextPageAdded = False

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def LogOn(self):
        """ Makes sure that we are logged on. """

        username = self._GetSetting("username")
        if not username:
            Logger.Info("No user name for NPO, not logging in")
            return False

        # cookieValue = self._GetSetting("cookie")
        cookie = UriHandler.GetCookie("npo_portal_auth_token", ".mijn.npo.nl")
        if cookie:
            expireDate = DateHelper.GetDateFromPosix(float(cookie.expires))
            Logger.Info("Found existing valid NPO token (valid until: %s)", expireDate)
            return True

        v = Vault()
        password = v.GetChannelSetting(self.guid, "password")
        # get the logon security token: http://www.npo.nl/sign_in_modal
        tokenData = UriHandler.Open("http://www.npo.nl/sign_in_modal",
                                    proxy=self.proxy, noCache=True,
                                    additionalHeaders={"X-Requested-With": "XMLHttpRequest"})
        token = Regexer.DoRegex('name="authenticity_token"[^>]+value="([^"]+)"', tokenData)[0]

        # login: https://mijn.npo.nl/sessions POST
        # utf8=%E2%9C%93&authenticity_token=<token>&email=<username>&password=<password>&remember_me=1&commit=Inloggen
        postData = {
            "token": HtmlEntityHelper.UrlEncode(token),
            "email": HtmlEntityHelper.UrlEncode(username),
            "password": HtmlEntityHelper.UrlEncode(password)
        }
        postData = "utf8=%%E2%%9C%%93&authenticity_token=%(token)s&email=%(email)s&" \
                   "password=%(password)s&remember_me=1&commit=Inloggen" % postData
        data = UriHandler.Open("https://mijn.npo.nl/sessions", noCache=True, proxy=self.proxy,
                               params=postData)
        if not data:
            Logger.Error("Error logging in: no response data")
            return False

        # extract the cookie and store
        authCookie = UriHandler.GetCookie("npo_portal_auth_token", ".mijn.npo.nl")
        if not authCookie:
            Logger.Error("Error logging in: Cookie not found.")
            return False

        # The cookie should already be in the jar now
        return True

    def GetAdditionalLiveItems(self, data):
        Logger.Info("Processing Live items")

        items = []
        # if "/radio/" in self.parentItem.url:
        #     # we should always add the parent as radio item
        #     parent = self.parentItem
        #     Logger.Debug("Adding main radio item to sub item list: %s", parent)
        #     item = mediaitem.MediaItem("%s (Hoofd kanaal)" % (parent.name,), parent.url)
        #     item.icon = parent.icon
        #     item.thumb = parent.thumb
        #     item.type = 'video'
        #     item.isLive = True
        #     item.complete = False
        #     items.append(item)

        if self.parentItem.url.endswith("/live"):
            # let's add the 3FM live stream
            parent = self.parentItem

            liveStreams = {
                "3FM Live": {
                    "url": "http://e.omroep.nl/metadata/LI_3FM_300881",
                    "thumb": "http://www.3fm.nl/data/thumb/abc_media_image/113000/113453/w210.1b764.jpg"
                },
                "Radio 2 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RADIO2_300879",
                    "thumb": self.GetImageLocation("radio2.png")
                    # "thumb": "http://www.radio2.nl/image/rm/48254/NPO_RD2_Logo_RGB_1200dpi.jpg?width=848&height=477"
                },
                "Radio 6 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RADIO6_300883",
                    # "thumb": "http://www.radio6.nl/data/thumb/abc_media_image/3000/3882/w500.1daa0.png"
                    "thumb": self.GetImageLocation("radio6.png")
                },
                "Radio 1 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RADIO1_300877",
                    # "thumb": "http://statischecontent.nl/img/tweederdevideo/1e7db3df-030a-4e5a-b2a2-840bd0fd8242.jpg"
                    "thumb": self.GetImageLocation("radio1.png")
                },
            }

            for stream in liveStreams:
                Logger.Debug("Adding video item to '%s' sub item list: %s", parent, stream)
                liveData = liveStreams[stream]
                item = mediaitem.MediaItem(stream, liveData["url"])
                item.icon = parent.icon
                item.thumb = liveData["thumb"]
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

        favs = mediaitem.MediaItem("Favorieten", "https://mijn.npo.nl/profiel/favorieten")
        favs.complete = True
        favs.description = "Favorieten van de NPO.nl website. Het toevoegen van favorieten " \
                           "wordt nog niet ondersteund."
        favs.icon = self.icon
        favs.thumb = self.noImage
        favs.dontGroup = True
        favs.SetDate(2200, 1, 1, text="")
        items.append(favs)

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

        extra = mediaitem.MediaItem("Live Radio",
                                    "http://radio-app.omroep.nl/player/script/player.js")
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

        extra = mediaitem.MediaItem("Genres", "https://www.npo.nl")
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
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

            url = "https://www.npo.nl/zoeken?utf8=%%E2%%9C%%93&sort_date=%02d-%02d-%04d&page=1" % \
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

    def ExtractJsonForLiveRadio(self, data):
        """ Extracts the JSON data from the HTML for the radio streams

        @param data: the HTML data
        @return:     a valid JSON string and no items

        """

        items = []
        data = Regexer.DoRegex('NPW.config.channels=([\w\W]+?),NPW\.config\.', data)[-1].rstrip(";")
        # fixUp some json
        data = re.sub('(\w+):([^/])', '"\\1":\\2', data)
        Logger.Trace(data)
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
                                              "https://www.npo.nl/programmas/a-z")
            else:
                subItem = mediaitem.MediaItem(titleFormat % (char,),
                                              "https://www.npo.nl/programmas/a-z/%s" % (
                                              char.lower(),))
            subItem.complete = True
            subItem.icon = self.icon
            subItem.thumb = self.noImage
            subItem.dontGroup = True
            items.append(subItem)
        return data, items

    def CreateFolderItem(self, resultSet):
        item = chn_class.Channel.CreateFolderItem(self, resultSet)
        if item.thumb.startswith("//"):
            item.thumb = "https:%s" % (item.thumb,)
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
        item.url = "https://www.npo.nl%(Url)s/%(WhatsOnId)s/search?end_date=&media_type=broadcast&rows=%%s&start=0&start_date=" % resultSet
        item.url %= self.nonMobilePageSize,

        return item

    def CreateJsonShows(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.Trace("CreateJsonShows(%s)", resultSet)
        if not resultSet:
            return None

        episodeId = resultSet['nebo_id']
        # if we should not use the mobile listing and we have a non-mobile ID)
        if 'mid' in resultSet and self.nonMobilePageSize > 0:
            nonMobileId = resultSet['mid']
            url = "http://www.npo.nl/a-z/%s/search?media_type=broadcast&start_date=&end_date=&start=0&rows=%s" \
                  % (nonMobileId, self.nonMobilePageSize)
        # Apparently the first one still works
        # elif 'mid' in resultSet:
        #     nonMobileId = resultSet['mid']
        #     url = "http://www.npo.nl/a-z/%s?page=1" % (nonMobileId, )
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

        # In some cases the name, posix and description are in the root, in other cases in the
        # 'episode' node
        posix = resultSet.get('starts_at', None)
        image = resultSet.get('image', None)
        name = resultSet.get('name', None)
        description = resultSet.get('description', '')

        # the tips has an extra 'episodes' key
        if 'episode' in resultSet:
            Logger.Debug("Found subnode: episodes")
            # set to episode node
            data = resultSet['episode']
        else:
            Logger.Warning("No subnode 'episodes' found, trying anyways")
            data = resultSet

        # look for better values
        posix = data.get('broadcasted_at', posix)
        broadcasted = DateHelper.GetDateFromPosix(posix)
        description = resultSet.get('description', description)
        videoId = data.get('whatson_id', None)

        # try to fetch more name data
        names = []
        name = data.get("name", name)
        if name:
            names = [name, ]
        if "series" in data and "name" in data["series"]:
            names.insert(0, data["series"]["name"])

        # Filter the duplicates
        title = " - ".join(set(names))

        item = mediaitem.MediaItem(title, videoId)
        item.icon = self.icon
        item.type = 'video'
        item.complete = False
        item.description = description
        #
        images = data.get('stills', None)
        if images:
            # there were images in the stills
            item.thumb = images[-1]['url']
        elif image:
            # no stills, or empty, check for image
            item.thumb = image

        item.SetDate(broadcasted.year, broadcasted.month, broadcasted.day, broadcasted.hour,
                     broadcasted.minute,
                     broadcasted.second)

        return item

    def CreateGenreItem(self, resultSet):
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
        item = mediaitem.MediaItem(resultSet[1], "https://www.npo.nl/zoeken?main_genre=%s&page=1" % (resultSet[0],))
        item.thumb = self.parentItem.thumb
        item.icon = self.parentItem.icon
        item.type = 'folder'
        item.fanart = self.parentItem.fanart
        # item.HttpHeaders["X-Requested-With"] = "XMLHttpRequest"
        # item.HttpHeaders["Accept"] = "text/html, */*; q=0.01"
        item.complete = True
        return item

    def AddNextPageItem(self, data):
        """ Add a possible next-page item
        @param data: the input data

        """

        items = []
        if self.__NextPageAdded:
            return data, items

        currentPage = Regexer.DoRegex("page=(\d+)", self.parentItem.url)
        for page in currentPage:
            nextPage = int(page) + 1
            url = self.parentItem.url.replace("page=%s" % (page,), "page=%s" % (nextPage,))
            pageItem = mediaitem.MediaItem("\a.: Meer afleveringen :.", url)
            pageItem.thumb = self.parentItem.thumb
            pageItem.complete = True
            pageItem.SetDate(2200, 1, 1, text="")
            pageItem.HttpHeaders["X-Requested-With"] = "XMLHttpRequest"
            pageItem.HttpHeaders["Accept"] = "text/html, */*; q=0.01"
            items.append(pageItem)
            Logger.Debug("Adding page item based on URL")
            self.__NextPageAdded = True
            break
        return data, items

    def CreatePageItemNonMobile(self, resultSet):
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
        if self.__NextPageAdded:
            return None

        if "Page" in resultSet and resultSet["Page"]:
            Logger.Debug("Adding page item based on 'Page' index only.")
            # page from date search result
            title = "\a.: Meer programma's :."
            page = int(resultSet["Page"])
            if "page=" in self.parentItem.url:
                url = self.parentItem.url.replace("page=%s" % (page,), "page=%s" % (page + 1,))
            elif "?" in self.parentItem.url:
                url = "%s&page=%s" % (self.parentItem.url, page + 1)
            else:
                url = "%s?page=%s" % (self.parentItem.url, page + 1)

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
            self.__NextPageAdded = True
            return item

        elif "CurrentStart" in resultSet and resultSet['CurrentStart']:
            Logger.Debug("Adding page item based on 'Total, CurrentStart, PageSize' values.")
            # page from episode list
            totalSize = int(resultSet["Total"])
            currentPage = int(resultSet["CurrentStart"])
            currentPageSize = int(resultSet["PageSize"])
            nextPage = currentPage + currentPageSize
            if nextPage >= totalSize:
                Logger.Debug(
                    "Not adding next page item. All items displayed (Total=%s vs Current=%s)",
                    totalSize, nextPage)
                self.__NextPageAdded = True
                return None
            else:
                pageSize = self.nonMobileMaxPageSize
                Logger.Debug("Adding next page item starting at %s and with %s items (Total=%s)",
                             nextPage, pageSize, totalSize)

                url = self.parentItem.url
                url = url.replace("start=%s" % (currentPage,), "start=%s" % (nextPage,))
                url = url.replace("rows=%s" % (currentPageSize,), "rows=%s" % (pageSize,))

                pageItem = mediaitem.MediaItem("\a.: Meer afleveringen :.", url)
                pageItem.thumb = self.parentItem.thumb
                pageItem.complete = True
                pageItem.SetDate(2200, 1, 1, text="")
                self.__NextPageAdded = True
                return pageItem

        elif "TotalPages" in resultSet and resultSet["TotalPages"]:
            Logger.Debug("Adding page item based on 'TotalPages' and 'CurrentPage'")
            # Page 2 is:
            # http://www.npo.nl/baby-te-huur/POMS_S_BNN_097316/search?page=2&category=all
            # But page 1 is:
            # http://www.npo.nl/baby-te-huur/POMS_S_BNN_097316/search?end_date=&media_type=broadcast&rows=50&start=0&start_date=
            currentPage = int(resultSet["CurrentPage"])
            totalPages = int(resultSet["TotalPages"])
            if currentPage >= totalPages:
                Logger.Debug("No more additional pages")
                self.__NextPageAdded = True
                return None

            url = self.parentItem.url.split("?")[0]
            url = "%s?page=%s&category=all" % (url, currentPage + 1)
            pageItem = mediaitem.MediaItem("\a.: Meer afleveringen :.", url)
            pageItem.thumb = self.parentItem.thumb
            pageItem.complete = True
            pageItem.SetDate(2200, 1, 1, text="")
            self.__NextPageAdded = True
            return pageItem

        else:
            Logger.Warning("No paging information found.")
            return None

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
        description = resultSet.get("Description")

        item = mediaitem.MediaItem(name, videoId)
        item.icon = self.icon
        item.type = 'video'
        item.complete = False
        item.description = description
        item.thumb = resultSet["Image"].replace("s174/c174x98", "s348/c348x196")
        if item.thumb.startswith("//"):
            item.thumb = "https:%s" % (item.thumb,)

        if "Premium" in resultSet and resultSet["Premium"]:
            item.isPaid = True
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
        name = resultSet[0]
        # name = name.replace("-", " ").capitalize()
        name = "%s: %s" % (name, resultSet[3].strip())
        if resultSet[4]:
            description = "Nu: %s\nStraks om %s: %s" % (resultSet[3].strip(), resultSet[4], resultSet[4].strip())
        else:
            description = "Nu: %s" % (resultSet[3].strip(), )

        item = mediaitem.MediaItem(name, "%s/live/%s" % (self.baseUrlLive, resultSet[2]), type="video")
        item.description = description

        if resultSet[1].startswith("http"):
            item.thumb = resultSet[1].replace("regular_", "").replace("larger_", "")
        elif resultSet[1].startswith("//"):
            item.thumb = "http:%s" % (resultSet[1].replace("regular_", "").replace("larger_", ""),)
        else:
            item.thumb = "%s%s" % (self.baseUrlLive, resultSet[1].replace("regular_", "").replace("larger_", ""))

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
        name = resultSet["name"]
        if name == "demo":
            return None

        item = mediaitem.MediaItem(name, "", type="audio")
        item.thumb = self.parentItem.thumb
        item.icon = self.icon
        item.isLive = True
        item.complete = False

        streams = resultSet.get("audiostreams", [])
        part = item.CreateNewEmptyMediaPart()

        # first check for the video streams
        for stream in resultSet.get("videostreams", []):
            Logger.Trace(stream)
            # url = stream["url"]
            # if not url.endswith("m3u8"):
            if not stream["protocol"] == "prid":
                continue
            item.url = "http://e.omroep.nl/metadata/%(url)s" % stream
            item.complete = False
            return item

        # else the radio streams
        for stream in streams:
            Logger.Trace(stream)
            if not stream["protocol"] or stream["protocol"] == "prid":
                continue
            bitrate = stream.get("bitrate", 0)
            url = stream["url"]
            part.AppendMediaStream(url, bitrate)
            item.complete = True
            # if not stream["protocol"] == "prid":
            #     continue
            # item.url = "http://e.omroep.nl/metadata/%(url)s" % stream
            # item.complete = False
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

        if "/radio/" in item.url or "/live/" in item.url or "/LI_" in item.url:
            Logger.Info("Updating Live item: %s", item.url)
            return self.UpdateVideoItemLive(item)

        whatson_id = item.url
        return self.__UpdateVideoItem(item, whatson_id)

    def UpdateFromPoms(self, item):
        poms = item.url.split("/")[-1]
        return self.__UpdateVideoItem(item, poms)

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

        # we need to determine radio or live tv
        Logger.Debug("Fetching live stream data from item url: %s", item.url)
        htmlData = UriHandler.Open(item.url, proxy=self.proxy)

        mp3Urls = Regexer.DoRegex("""data-streams='{"url":"([^"]+)","codec":"[^"]+"}'""", htmlData)
        if len(mp3Urls) > 0:
            Logger.Debug("Found MP3 URL")
            part.AppendMediaStream(mp3Urls[0], 192)
        else:
            Logger.Debug("Finding the actual metadata url from %s", item.url)
            if "npo-3" in item.url:
                # NPO3 has apparently switched the normal and hearing impaired streams?
                jsonUrls = Regexer.DoRegex('<div class="video-player-container"[^>]+data-alt-prid="([^"]+)"', htmlData)
            else:
                jsonUrls = Regexer.DoRegex('<div class="video-player-container"[^>]+data-prid="([^"]+)"', htmlData)
            for episodeId in jsonUrls:
                return self.__UpdateVideoItem(item, episodeId)
            Logger.Warning("Cannot update live item: %s", item)
            return item

        item.complete = True
        return item

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
        url = "https://www.npo.nl/zoeken?av_type=video&document_type=program&q=%s&page=1"
        return chn_class.Channel.SearchSite(self, url)

    def CtMnDownload(self, item):
        """ downloads a video item and returns the updated one
        """
        # noinspection PyUnusedLocal
        item = self.DownloadVideoItem(item)

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
        subTitleUrl = "http://tt888.omroep.nl/tt888/%s" % (episodeId,)
        subTitlePath = subtitlehelper.SubtitleHelper.DownloadSubtitle(subTitleUrl,
                                                                      episodeId + ".srt",
                                                                      format='srt',
                                                                      proxy=self.proxy)

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()
        part.Subtitle = subTitlePath

        for s, b in NpoStream.GetStreamsFromNpo(None, episodeId, proxy=self.proxy):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)

        return item

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
            thumbUrl = thumbnails[1].replace('140x79', '280x158').\
                replace('60x34', '280x158').\
                replace("&quot", "")
        else:
            thumbUrl = ""

        return thumbUrl

    def __IgnoreCookieLaw(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.Info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        UriHandler.SetCookie(name='site_cookie_consent', value='yes',
                             domain='.www.uitzendinggemist.nl')
        UriHandler.SetCookie(name='npo_cc', value='tmp', domain='.www.uitzendinggemist.nl')

        UriHandler.SetCookie(name='site_cookie_consent', value='yes', domain='.npo.nl')
        UriHandler.SetCookie(name='npo_cc', value='30', domain='.npo.nl')
        return
