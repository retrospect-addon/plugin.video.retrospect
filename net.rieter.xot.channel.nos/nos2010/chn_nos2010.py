import datetime
import re

import mediaitem
import chn_class
from helpers.jsonhelper import JsonHelper

from regexer import Regexer
from helpers import subtitlehelper

from logger import Logger
from streams.npostream import NpoStream
from streams.mpd import Mpd
from urihandler import UriHandler
from helpers.datehelper import DateHelper
from parserdata import ParserData
from helpers.languagehelper import LanguageHelper
from helpers.htmlentityhelper import HtmlEntityHelper
from vault import Vault
from addonsettings import AddonSettings


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
        self._add_data_parser("#mainlist", preprocessor=self.GetInitialFolderItems)

        # live stuff
        self.baseUrlLive = "https://www.npostart.nl"

        # live radio, the folders and items
        self._add_data_parser("http://radio-app.omroep.nl/player/script/",
                              name="Live Radio Streams",
                              preprocessor=self.ExtractJsonForLiveRadio, json=True,
                              parser=[], creator=self.CreateLiveRadio)

        self._add_data_parser("/live", match_type=ParserData.MatchEnd,
                              name="Main Live Stream HTML parser",
                              preprocessor=self.GetAdditionalLiveItems,
                              parser='<a href="[^"]+/live/([^"]+)" class="npo-tile-link"[^>]+>[\w\W]{0,1000}?<img data-src="([^"]+)"[\w\W]{0,1000}?<h2>(?:Nu: )?([^<]+)</h2>\W+<p>(?:Straks: )?([^<]*)</p>',
                              creator=self.CreateLiveTv,
                              updater=self.UpdateVideoItemLive)

        self._add_data_parser("https://www.npostart.nl/live/", name="Live Video Updater from HTML",
                              updater=self.UpdateVideoItemLive)

        # Use old urls with new Updater
        self._add_data_parser("http://e.omroep.nl/metadata/", name="e.omroep.nl classic parser",
                              updater=self.UpdateFromPoms)

        # Standard updater
        self._add_data_parser("*",
                              updater=self.update_video_item)

        # recent and popular stuff and other Json data
        self._add_data_parser(".json", name="JSON List Parser for the recent/tips/populair",
                              parser=[], creator=self.CreateVideoItemJson,
                              json=True, match_type=ParserData.MatchEnd)

        self._add_data_parser("#recent", name="Recent items list",
                              preprocessor=self.AddRecentItems)

        # Alpha listing and paging for that list
        self._add_data_parser("#alphalisting", preprocessor=self.AlphaListing)

        episodeParser = Regexer.from_expresso('id="(?<powid>[^"]+)"[^>]*>\W*<a href="(?<url>[^"]+)" title="(?<title>[^"]+)"[^>]+\W+<div[^(>]+>\s*(?:<img[^>]+data-src="(?<thumburl>[^"]+)")?')
        self._add_data_parsers(["https://www.npostart.nl/media/series?page=", ],
                               name="Parser for main series overview pages",
                               preprocessor=self.ExtractTiles,
                               parser=episodeParser,
                               creator=self.create_episode_item)

        # very similar parser as the Live Channels!
        videoParser = Regexer.from_expresso('<div[^>]+class="(?<class>[^"]+)"[^>]+id="(?<powid>[^"]+)'
                                            '"[^>]*>\W*<a href="[^"]+/(?<url>[^/"]+)" class="npo-tile-link"[^>]+'
                                            'data-scorecard=\'(?<videodata>[^\']*)\'[^>]*>\W+<div[^>]+>\W+'
                                            '<div [^>]+data-from="(?<date>[^"]*)"[\w\W]{0,1000}?<img[^>]+'
                                            'data-src="(?<thumburl>[^"]+)"[\w\W]{0,1000}?<h2>(?<title>[^<]+)'
                                            '</h2>\W+<p>(?<subtitle>[^<]*)</p>')
        self._add_data_parsers(["https://www.npostart.nl/media/series/", "https://www.npostart.nl/search/extended", "https://www.npostart.nl/media/collections/"],
                               name="Parser for shows on the main series sub pages, the search and the genres",
                               preprocessor=self.ExtractTiles,
                               parser=videoParser,
                               creator=self.CreateNpoItem)

        # Genres
        self._add_data_parser("https://www.npostart.nl/programmas",
                              match_type=ParserData.MatchExact,
                              name="Genres",
                              parser='<a\W+class="close-dropdown"\W+href="/collectie/([^"]+)"\W+title="([^"]+)"[^>]+data-value="([^"]+)"[^>]+data-argument="genreId',
                              creator=self.CreateGenreItem)

        # Favourites
        self._add_data_parser("https://www.npostart.nl/ums/accounts/@me/favourites",
                              preprocessor=self.ExtractTiles,
                              parser=episodeParser,
                              creator=self.create_episode_item,
                              requires_logon=True)

        # Alpha listing based on JSON interface
        self._add_data_parser("%s/series.json" % (self.baseUrl,),
                              parser=[], creator=self.CreateJsonEpisodeItem,
                              json=True)

        tvGuideRegex = 'data-channel="(?<channel>[^"]+)"[^>]+data-title="(?<title>[^"]+)"[^>]+data-id=\'(?<url>[^\']+)\'[^>]*>\W*<div[^>]*>\W+<p>\W+<span[^>]+time"[^>]*>(?<hours>\d+):(?<minutes>\d+)</span>\W+<span[^<]+</span>\W+<span class="npo-epg-active"></span>\W+<span class="npo-epg-play"></span>'
        tvGuideRegex = Regexer.from_expresso(tvGuideRegex)
        self._add_data_parser("https://www.npostart.nl/gids?date=",
                              parser=tvGuideRegex, creator=self.CreateTvGuideItem)

        self.__IgnoreCookieLaw()

        # ===============================================================================================================
        # non standard items
        self.__NextPageAdded = False

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def log_on(self):
        """ Makes sure that we are logged on. """

        username = self._get_setting("username")
        if not username:
            Logger.info("No user name for NPO, not logging in")
            return False

        # cookieValue = self._get_setting("cookie")
        cookie = UriHandler.get_cookie("isAuthenticatedUser", "www.npostart.nl")
        if cookie:
            expireDate = DateHelper.get_date_from_posix(float(cookie.expires))
            Logger.info("Found existing valid NPO token (valid until: %s)", expireDate)
            return True

        v = Vault()
        password = v.get_channel_setting(self.guid, "password")

        # get a token (why?), cookies and an xsrf token
        token = UriHandler.open("https://www.npostart.nl/api/token", proxy=self.proxy, no_cache=True,
                                additional_headers={"X-Requested-With": "XMLHttpRequest"})

        jsonToken = JsonHelper(token)
        token = jsonToken.get_value("token")
        if not token:
            return False
        xsrfToken = UriHandler.get_cookie("XSRF-TOKEN", "www.npostart.nl").value
        xsrfToken = HtmlEntityHelper.url_decode(xsrfToken)

        data = "username=%s&password=%s" % (HtmlEntityHelper.url_encode(username),
                                            HtmlEntityHelper.url_encode(password))
        UriHandler.open("https://www.npostart.nl/api/login", proxy=self.proxy, no_cache=True,
                        additional_headers={
                            "X-Requested-With": "XMLHttpRequest",
                            "X-XSRF-TOKEN": xsrfToken
                        },
                        params=data)

        # token = Regexer.do_regex('name="authenticity_token"[^>]+value="([^"]+)"', tokenData)[0]
        #
        # # login: https://mijn.npo.nl/sessions POST
        # # utf8=%E2%9C%93&authenticity_token=<token>&email=<username>&password=<password>&remember_me=1&commit=Inloggen
        # postData = {
        #     "token": HtmlEntityHelper.url_encode(token),
        #     "email": HtmlEntityHelper.url_encode(username),
        #     "password": HtmlEntityHelper.url_encode(password)
        # }
        # postData = "utf8=%%E2%%9C%%93&authenticity_token=%(token)s&email=%(email)s&" \
        #            "password=%(password)s&remember_me=1&commit=Inloggen" % postData
        # data = UriHandler.open("https://mijn.npo.nl/sessions", noCache=True, proxy=self.proxy,
        #                        params=postData)
        # if not data:
        #     Logger.Error("Error logging in: no response data")
        #     return False
        #
        # # extract the cookie and store
        # authCookie = UriHandler.get_cookie("npo_portal_auth_token", ".mijn.npo.nl")
        # if not authCookie:
        #     Logger.Error("Error logging in: Cookie not found.")
        #     return False

        # The cookie should already be in the jar now
        return True

    def ExtractTiles(self, data):
        items = []
        newData = ""

        jsonData = JsonHelper(data)
        tiles = jsonData.get_value("tiles")
        if not isinstance(tiles,  (tuple, list)):
            Logger.debug("Found single tile data blob")
            newData = tiles
        else:
            Logger.debug("Found multiple tile data blobs")
            for itemData in tiles:
                newData = "%s%s\n" % (newData, itemData)

        # More pages?
        maxCount = 5
        currentCount = 1
        nextPage = jsonData.get_value("nextLink")
        queryString = self.parentItem.url.split("&", 1)[-1]

        httpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        httpHeaders.update(self.parentItem.HttpHeaders)
        httpHeaders.update(self.httpHeaders)
        while nextPage and currentCount < maxCount:
            currentCount += 1
            Logger.debug("Found next page: %s", nextPage)
            if nextPage.startswith("/search/extended") or nextPage.startswith("/media/series"):
                nextPage = nextPage.split("&", 1)[0]
                nextPage = "%s%s&%s" % (self.baseUrlLive, nextPage, queryString)
            elif not nextPage.startswith("http"):
                nextPage = "%s%s&%s" % (self.baseUrlLive, nextPage, queryString)
            else:
                nextPage = "%s&%s" % (nextPage, queryString)

            pageData = UriHandler.open(nextPage, proxy=self.proxy, additional_headers=httpHeaders)
            jsonData = JsonHelper(pageData)
            tiles = jsonData.get_value("tiles")
            if not isinstance(tiles, (tuple, list)):
                Logger.debug("Found single tile data blob")
                newData = "%s%s\n" % (newData, tiles)
            else:
                Logger.debug("Found multiple tile data blobs")
                for itemData in tiles:
                    newData = "%s%s\n" % (newData, itemData)
            nextPage = jsonData.get_value("nextLink")

        if nextPage and currentCount == maxCount:
            # There are more pages
            if nextPage.startswith("/search/extended") or nextPage.startswith("/media/series"):
                nextPage = nextPage.split("&", 1)[0]
                nextPage = "%s%s&%s" % (self.baseUrlLive, nextPage, queryString)
            elif not nextPage.startswith("http"):
                nextPage = "%s%s&%s" % (self.baseUrlLive, nextPage, queryString)
            else:
                nextPage = "%s&%s" % (nextPage, queryString)

            title = LanguageHelper.get_localized_string(LanguageHelper.MorePages)
            title = "\a.: %s :." % (title, )
            more = mediaitem.MediaItem(title, nextPage)
            more.thumb = self.parentItem.thumb
            more.fanart = self.parentItem.fanart
            more.HttpHeaders = httpHeaders
            more.HttpHeaders.update(self.parentItem.HttpHeaders)
            items.append(more)

        return newData, items

    def GetInitialFolderItems(self, data):
        items = []
        search = mediaitem.MediaItem("Zoeken", "searchSite")
        search.complete = True
        search.icon = self.icon
        search.thumb = self.noImage
        search.dontGroup = True
        search.set_date(2200, 1, 1, text="")
        search.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        items.append(search)

        # favs = mediaitem.MediaItem("Favorieten", "https://www.npostart.nl/ums/accounts/@me/favourites?page=1&type=series&tileMapping=normal&tileType=teaser")
        # favs.complete = True
        # favs.description = "Favorieten van de NPO.nl website. Het toevoegen van favorieten " \
        #                    "wordt nog niet ondersteund."
        # favs.icon = self.icon
        # favs.thumb = self.noImage
        # favs.dontGroup = True
        # favs.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        # favs.set_date(2200, 1, 1, text="")
        # items.append(favs)

        extra = mediaitem.MediaItem("Populair", "%s/episodes/popular.json" % (self.baseUrl,))
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.set_date(2200, 1, 1, text="")
        items.append(extra)

        # extra = mediaitem.MediaItem("Tips", "%s/tips.json" % (self.baseUrl,))
        # extra.complete = True
        # extra.icon = self.icon
        # extra.thumb = self.noImage
        # extra.dontGroup = True
        # extra.set_date(2200, 1, 1, text="")
        # items.append(extra)

        extra = mediaitem.MediaItem("Live Radio",
                                    "http://radio-app.omroep.nl/player/script/player.js")
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.set_date(2200, 1, 1, text="")
        items.append(extra)

        extra = mediaitem.MediaItem("Live TV", "%s/live" % (self.baseUrlLive,))
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.set_date(2200, 1, 1, text="")
        items.append(extra)

        extra = mediaitem.MediaItem("Programma's (Hele lijst)", "%s/series.json" % (self.baseUrl,))
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.description = "Volledige programma lijst van de NPO iOS/Android App."
        extra.set_date(2200, 1, 1, text="")
        items.append(extra)

        extra = mediaitem.MediaItem("Genres", "https://www.npostart.nl/programmas")
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.set_date(2200, 1, 1, text="")
        # extra.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        items.append(extra)

        extra = mediaitem.MediaItem("Programma's (A-Z)", "#alphalisting")
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.description = "Alfabetische lijst van de NPO.nl site."
        extra.dontGroup = True
        extra.set_date(2200, 1, 1, text="")
        items.append(extra)

        recent = mediaitem.MediaItem("Recent", "#recent")
        recent.complete = True
        recent.icon = self.icon
        recent.thumb = self.noImage
        recent.dontGroup = True
        recent.set_date(2200, 1, 1, text="")
        items.append(recent)

        return data, items

    def AddRecentItems(self, data):
        items = []
        today = datetime.datetime.now()
        days = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        for i in range(0, 7, 1):
            airDate = today - datetime.timedelta(i)
            Logger.trace("Adding item for: %s", airDate)

            # Determine a nice display date
            day = days[airDate.weekday()]
            if i == 0:
                day = "Vandaag"
            elif i == 1:
                day = "Gisteren"
            elif i == 2:
                day = "Eergisteren"
            title = "%04d-%02d-%02d - %s" % (airDate.year, airDate.month, airDate.day, day)

            # url = "https://www.npostart.nl/media/series?page=1&dateFrom=%04d-%02d-%02d&tileMapping=normal&tileType=teaser&pageType=catalogue" % \
            url = "https://www.npostart.nl/gids?date=%04d-%02d-%02d&type=tv" % \
                  (airDate.year, airDate.month, airDate.day)
            extra = mediaitem.MediaItem(title, url)
            extra.complete = True
            extra.icon = self.icon
            extra.thumb = self.noImage
            extra.dontGroup = True
            extra.HttpHeaders["X-Requested-With"] = "XMLHttpRequest"
            extra.HttpHeaders["Accept"] = "text/html, */*; q=0.01"
            extra.set_date(airDate.year, airDate.month, airDate.day, text="")

            items.append(extra)

        extra = mediaitem.MediaItem("Recent", "%s/broadcasts/recent.json" % (self.baseUrl,))
        extra.complete = True
        extra.icon = self.icon
        extra.thumb = self.noImage
        extra.dontGroup = True
        extra.set_date(2200, 1, 1, text="")

        items.append(extra)
        return data, items

    def GetAdditionalLiveItems(self, data):
        Logger.info("Processing Live items")

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
                    "thumb": self.get_image_location("radio2.png")
                    # "thumb": "http://www.radio2.nl/image/rm/48254/NPO_RD2_Logo_RGB_1200dpi.jpg?width=848&height=477"
                },
                "Radio 6 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RADIO6_300883",
                    # "thumb": "http://www.radio6.nl/data/thumb/abc_media_image/3000/3882/w500.1daa0.png"
                    "thumb": self.get_image_location("radio6.png")
                },
                "Radio 1 Live": {
                    "url": "http://e.omroep.nl/metadata/LI_RADIO1_300877",
                    # "thumb": "http://statischecontent.nl/img/tweederdevideo/1e7db3df-030a-4e5a-b2a2-840bd0fd8242.jpg"
                    "thumb": self.get_image_location("radio1.png")
                },
            }

            for stream in liveStreams:
                Logger.debug("Adding video item to '%s' sub item list: %s", parent, stream)
                liveData = liveStreams[stream]
                item = mediaitem.MediaItem(stream, liveData["url"])
                item.icon = parent.icon
                item.thumb = liveData["thumb"]
                item.type = 'video'
                item.isLive = True
                item.complete = False
                items.append(item)
        return data, items

    def ExtractJsonForLiveRadio(self, data):
        """ Extracts the JSON data from the HTML for the radio streams

        @param data: the HTML data
        @return:     a valid JSON string and no items

        """

        items = []
        data = Regexer.do_regex('NPW.config.channels=([\w\W]+?),NPW\.config\.', data)[-1].rstrip(";")
        # fixUp some json
        data = re.sub('(\w+):([^/])', '"\\1":\\2', data)
        Logger.trace(data)
        return data, items

    def AlphaListing(self, data):
        """Performs pre-process actions for data processing

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """

        Logger.info("Generating an Alpha list for NPO")

        items = []
        # https://www.npostart.nl/media/series?page=1&dateFrom=2014-01-01&tileMapping=normal&tileType=teaser
        # https://www.npostart.nl/media/series?page=2&dateFrom=2014-01-01&az=A&tileMapping=normal&tileType=teaser
        # https://www.npostart.nl/media/series?page=2&dateFrom=2014-01-01&az=0-9&tileMapping=normal&tileType=teaser

        titleFormat = LanguageHelper.get_localized_string(LanguageHelper.StartWith)
        urlFormat = "https://www.npostart.nl/media/series?page=1&dateFrom=2014-01-01&az=%s&tileMapping=normal&tileType=teaser&pageType=catalogue"
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0":
            if char == "0":
                char = "0-9"
            subItem = mediaitem.MediaItem(titleFormat % (char,), urlFormat % (char, ))
            subItem.complete = True
            subItem.icon = self.icon
            subItem.thumb = self.noImage
            subItem.dontGroup = True
            subItem.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
            items.append(subItem)
        return data, items

    def create_episode_item(self, resultSet):
        """ Create a video item """
        item = chn_class.Channel.create_episode_item(self, resultSet)

        # Update the URL
        # https://www.npostart.nl/media/series/POW_03094258/episodes?page=2&tileMapping=dedicated&tileType=asset
        url = "https://www.npostart.nl/media/series/%(powid)s/episodes?page=1&tileMapping=dedicated&tileType=asset&pageType=franchise" % resultSet
        item.url = url
        item.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        item.dontGroup = True
        return item

    def CreateJsonEpisodeItem(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.trace("CreateJsonShows(%s)", resultSet)
        if not resultSet:
            return None

        # if we should not use the mobile listing and we have a non-mobile ID)
        if 'mid' in resultSet:
            url = "https://www.npostart.nl/media/series/{mid}/episodes?page=1&tileMapping=dedicated&tileType=asset&pageType=franchise".format(**resultSet)
        else:
            Logger.warning("Skipping (no 'mid' ID): %(name)s", resultSet)
            return None

        name = resultSet['name']
        description = resultSet.get('description', '')
        thumbUrl = resultSet['image']

        item = mediaitem.MediaItem(name, url)
        item.type = 'folder'
        item.icon = self.icon
        item.complete = True
        item.description = description
        item.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        # This should always be a full list as we already have a default alphabet listing available
        # from NPO
        item.dontGroup = True

        if thumbUrl:
            item.thumb = thumbUrl
        else:
            item.thumb = self.noImage
        return item

    # noinspection PyUnusedLocal
    def search_site(self, url=None):  # @UnusedVariable
        """ Creates an list of items by searching the site.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        The %s the url will be replaced with an URL encoded representation of the
        text to search for.

        :param str url:     Url to use to search with a %s for the search parameters.

        :return: A list with search results as MediaItems.
        :rtype: list[MediaItem]

        """

        # Videos
        url = "https://www.npostart.nl/search/extended?page=1&query=%s&filter=episodes&dateFrom=2014-01-01&tileMapping=search&tileType=asset&pageType=search"

        # Shows
        # url = "https://www.npostart.nl/search/extended?page=1&query=%s&filter=programs&dateFrom=2014-01-01&tileMapping=normal&tileType=teaser&pageType=search"
        self.httpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        return chn_class.Channel.search_site(self, url)

    def CreateTvGuideItem(self, resultSet):
        Logger.trace(resultSet)
        channel = resultSet["channel"].replace("NED", "NPO ")
        title = "{0[hours]}:{0[minutes]} - {1} - {0[title]}".format(resultSet, channel)
        item = mediaitem.MediaItem(title, resultSet["url"])
        item.icon = self.icon
        item.description = resultSet["channel"]
        item.type = 'video'
        item.fanart = self.fanart
        item.HttpHeaders = self.httpHeaders
        item.complete = False
        return item

    def CreateNpoItem(self, resultSet):
        """ Call base method and then do some more stuff """
        item = chn_class.Channel.create_video_item(self, resultSet)
        # set the POW id
        if resultSet["videodata"]:
            item.type = "video"
            item.url = resultSet["powid"]
        else:
            item.type = "folder"
            item.url = "https://www.npostart.nl/media/series/%(powid)s/episodes?page=1&tileMapping=dedicated&tileType=asset&pageType=franchise" % resultSet
            item.HttpHeaders = {"X-Requested-With": "XMLHttpRequest"}
        item.isPaid = "premium" in resultSet["class"]

        try:
            dateTime = resultSet["subtitle"].strip().replace("  ", " ").split(" ")

            # For #933 we check for NOS Journaal
            if ":" in dateTime[-1] and item.name == "NOS Journaal":
                item.name = "{0} - {1}".format(item.name, dateTime[-1])

            Logger.trace(dateTime)
            if dateTime[0].lower() == "gisteren":
                dateTime = datetime.datetime.now() + datetime.timedelta(days=-1)
                item.set_date(dateTime.year, dateTime.month, dateTime.day)
            elif dateTime[0].lower() == "vandaag":
                dateTime = datetime.datetime.now()
                item.set_date(dateTime.year, dateTime.month, dateTime.day)
            elif ":" in dateTime[-1]:
                if dateTime[-2].isalpha():
                    year = datetime.datetime.now().year
                    dateTime.insert(-1, year)
                if item.name == "NOS Journaal":
                    item.name = "{0} - {1}".format(item.name, dateTime[-1])
                year = int(dateTime[-2])

                month = DateHelper.get_month_from_name(dateTime[-3], language="nl")
                day = int(dateTime[-4])

                stamp = datetime.datetime(year, month, day)
                if stamp > datetime.datetime.now():
                    year -= 1
                item.set_date(year, month, day)
            else:
                # there is an actual date present
                if dateTime[0].isalpha():
                    # first part is ma/di/wo/do/vr/za/zo
                    dateTime.pop(0)

                # translate the month
                month = DateHelper.get_month_from_name(dateTime[1], language="nl")

                # if the year is missing, let's assume it is this year
                if ":" in dateTime[2]:
                    dateTime[2] = datetime.datetime.now().year
                    # in the past of future, if future, we need to substract
                    stamp = datetime.datetime(dateTime[2], month, int(dateTime[0]))
                    if stamp > datetime.datetime.now():
                        dateTime[2] -= 1

                item.set_date(dateTime[2], month, dateTime[0])

        except:
            Logger.debug("Cannot set date from label: %s", resultSet["subtitle"], exc_info=True)
            # 2016-07-05T00:00:00Z
            dateValue = resultSet.get("date", None)
            if dateValue:
                timeStamp = DateHelper.get_date_from_string(dateValue, "%Y-%m-%dT%H:%M:%SZ")
                item.set_date(*timeStamp[0:6])
            else:
                Logger.warning("Cannot set date from 'data-from': %s", resultSet["date"], exc_info=True)
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
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        """
        Logger.trace(resultSet)

        # In some cases the name, posix and description are in the root, in other cases in the
        # 'episode' node
        posix = resultSet.get('starts_at', None)
        image = resultSet.get('image', None)
        name = resultSet.get('name', None)
        description = resultSet.get('description', '')

        # the tips has an extra 'episodes' key
        if 'episode' in resultSet:
            Logger.debug("Found subnode: episodes")
            # set to episode node
            data = resultSet['episode']
        else:
            Logger.warning("No subnode 'episodes' found, trying anyways")
            data = resultSet

        # look for better values
        posix = data.get('broadcasted_at', posix)
        broadcasted = DateHelper.get_date_from_posix(posix)
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

        item.set_date(broadcasted.year, broadcasted.month, broadcasted.day, broadcasted.hour,
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
        Logger.trace(resultSet)

        # url = "https://www.npostart.nl/media/series?page=1&dateFrom=2014-01-01&genreId=%s&tileMapping=normal&tileType=teaser" % (resultSet[1],)
        # url = "https://www.npostart.nl/media/%s/lanes/234?page=1&tileMapping=normal&tileType=asset&pageType=collection" % (resultSet[0],)
        url = "https://www.npostart.nl/media/collections/%s?page=1&tileMapping=normal&tileType=asset&pageType=collection" % (resultSet[0],)
        item = mediaitem.MediaItem(resultSet[1], url)
        item.thumb = self.parentItem.thumb
        item.icon = self.parentItem.icon
        item.type = 'folder'
        item.fanart = self.parentItem.fanart
        item.HttpHeaders["X-Requested-With"] = "XMLHttpRequest"
        # item.HttpHeaders["Accept"] = "text/html, */*; q=0.01"
        item.complete = True
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
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        """

        Logger.trace("Content = %s", resultSet)

        # first regex matched -> video channel
        channelId = resultSet[0]
        if channelId == "<exception>":
            name = "NPO 3"
        else:
            name = resultSet[0].replace("-", " ").title().replace("Npo", "NPO")

        # name = name.replace("-", " ").capitalize()
        nowPlaying = resultSet[2]
        nextUp = resultSet[3]
        name = "%s: %s" % (name, nowPlaying)
        if nextUp:
            description = "Nu: %s\nStraks om %s" % (nowPlaying, nextUp)
        else:
            description = "Nu: %s" % (resultSet[3].strip(), )

        item = mediaitem.MediaItem(name, "%s/live/%s" % (self.baseUrlLive, resultSet[0]), type="video")
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
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        """

        Logger.trace("Content = %s", resultSet)
        name = resultSet["name"]
        if name == "demo":
            return None

        item = mediaitem.MediaItem(name, "", type="audio")
        item.thumb = self.parentItem.thumb
        item.icon = self.icon
        item.isLive = True
        item.complete = False

        streams = resultSet.get("audiostreams", [])
        part = item.create_new_empty_media_part()

        # first check for the video streams
        for stream in resultSet.get("videostreams", []):
            Logger.trace(stream)
            # url = stream["url"]
            # if not url.endswith("m3u8"):
            if not stream["protocol"] == "prid":
                continue
            item.url = "http://e.omroep.nl/metadata/%(url)s" % stream
            item.complete = False
            return item

        # else the radio streams
        for stream in streams:
            Logger.trace(stream)
            if not stream["protocol"] or stream["protocol"] == "prid":
                continue
            bitrate = stream.get("bitrate", 0)
            url = stream["url"]
            part.append_media_stream(url, bitrate)
            item.complete = True
            # if not stream["protocol"] == "prid":
            #     continue
            # item.url = "http://e.omroep.nl/metadata/%(url)s" % stream
            # item.complete = False
        return item

    def update_video_item(self, item):
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
            Logger.info("Updating Live item: %s", item.url)
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

        Logger.debug('Starting update_video_item: %s', item.name)

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()

        # we need to determine radio or live tv
        Logger.debug("Fetching live stream data from item url: %s", item.url)
        htmlData = UriHandler.open(item.url, proxy=self.proxy)

        mp3Urls = Regexer.do_regex("""data-streams='{"url":"([^"]+)","codec":"[^"]+"}'""", htmlData)
        if len(mp3Urls) > 0:
            Logger.debug("Found MP3 URL")
            part.append_media_stream(mp3Urls[0], 192)
        else:
            Logger.debug("Finding the actual metadata url from %s", item.url)
            # NPO3 normal stream had wrong subs
            if "npo-3" in item.url and False:
                # NPO3 has apparently switched the normal and hearing impaired streams?
                jsonUrls = Regexer.do_regex('<div class="video-player-container"[^>]+data-alt-prid="([^"]+)"', htmlData)
            else:
                jsonUrls = Regexer.do_regex('<npo-player media-id="([^"]+)"', htmlData)

            for episodeId in jsonUrls:
                if AddonSettings.use_adaptive_stream_add_on(with_encryption=True):
                    return self.__UpdateDashItem(item, episodeId)
                return self.__UpdateVideoItem(item, episodeId)

            Logger.warning("Cannot update live item: %s", item)
            return item

        item.complete = True
        return item

    def __UpdateDashItem(self, item, episodeId):
        url = "https://start-player.npo.nl/video/{0}/streams?profile=dash-widevine&" \
              "quality=npo&streamType=livetv&mobile=0&ios=0&isChromecast=0".format(episodeId)
        dashData = UriHandler.open(url, proxy=self.proxy)
        dashJson = JsonHelper(dashData)
        dashUrl = dashJson.get_value("stream", "src")
        dashLicenseUrl = dashJson.get_value("stream", "keySystemOptions", 0, "options", "licenseUrl")
        dashHeaders = dashJson.get_value("stream", "keySystemOptions", 0, "options", "httpRequestHeaders")
        dashHeaders[u"Referer"] = unicode(url)
        dashLicense = Mpd.get_license_key(dashLicenseUrl, key_headers=dashHeaders, key_type="R")

        part = item.create_new_empty_media_part()
        stream = part.append_media_stream(dashUrl, 0)
        Mpd.set_input_stream_addon_input(stream, self.proxy, dashHeaders, license_key=dashLicense)
        item.complete = True
        return item

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

        Logger.trace("Using Generic update_video_item method")

        # get the subtitle
        subTitleUrl = "http://tt888.omroep.nl/tt888/%s" % (episodeId,)
        subTitlePath = subtitlehelper.SubtitleHelper.download_subtitle(subTitleUrl,
                                                                       episodeId + ".srt",
                                                                       format='srt',
                                                                       proxy=self.proxy)

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()
        part.Subtitle = subTitlePath

        for s, b in NpoStream.get_streams_from_npo(None, episodeId, proxy=self.proxy):
            item.complete = True
            # s = self.get_verifiable_video_url(s)
            part.append_media_stream(s, b)

        if False and AddonSettings.use_adaptive_stream_add_on():
            NpoStream.add_mpd_stream_from_npo(None, episodeId, part, proxy=self.proxy)

        return item

    def __IgnoreCookieLaw(self):
        """ Accepts the cookies from UZG in order to have the site available """

        Logger.info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        UriHandler.set_cookie(name='site_cookie_consent', value='yes',
                              domain='.www.uitzendinggemist.nl')
        UriHandler.set_cookie(name='npo_cc', value='tmp', domain='.www.uitzendinggemist.nl')

        UriHandler.set_cookie(name='site_cookie_consent', value='yes', domain='.npo.nl')
        UriHandler.set_cookie(name='npo_cc', value='30', domain='.npo.nl')

        UriHandler.set_cookie(name='site_cookie_consent', value='yes', domain='.npostart.nl')
        UriHandler.set_cookie(name='npo_cc', value='30', domain='.npostart.nl')
        return
