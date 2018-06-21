# coding:UTF-8
import math
import datetime

import mediaitem
import chn_class
from addonsettings import AddonSettings
from helpers.jsonhelper import JsonHelper
# from helpers.subtitlehelper import SubtitleHelper

from parserdata import ParserData
from regexer import Regexer
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.languagehelper import LanguageHelper
from logger import Logger
from streams.m3u8 import M3u8
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
        self.__channelId = "tv4"
        if self.channelCode == "tv4se":
            self.noImage = "tv4image.png"
            self.__channelId = "tv4"
        elif self.channelCode == "tv7se":
            self.noImage = "tv7image.png"
            self.__channelId = "sjuan"
        elif self.channelCode == "tv12se":
            self.noImage = "tv12image.png"
            self.__channelId = "tv12"
        else:
            raise Exception("Invalid channel code")

        # setup the urls
        # self.mainListUri = "http://webapi.tv4play.se/play/programs?is_active=true&platform=tablet&per_page=1000" \
        #                    "&fl=nid,name,program_image&start=0"

        self.mainListUri = "http://webapi.tv4play.se/play/programs?is_active=true&platform=tablet&per_page=1000" \
                           "&fl=nid,name,program_image,is_premium,updated_at,channel&start=0"

        self.baseUrl = "http://www.tv4play.se"
        self.swfUrl = "http://www.tv4play.se/flash/tv4playflashlets.swf"

        self.episodeItemJson = ("results",)
        self._AddDataParser(self.mainListUri,
                            preprocessor=self.AddCategoriesAndSpecials, json=True,
                            matchType=ParserData.MatchExact,  # requiresLogon=True,
                            parser=self.episodeItemJson, creator=self.CreateEpisodeItem)

        # favRegex = '<a href="/program/(?<nid>[^"]+)"><img[^>]+alt="(?<name>[^"]+)"[^>]+src="(?<program_image>[^"]+)'
        # self._AddDataParser("http://www.tv4play.se/program/favourites", name="Favourite parser",
        #                     requiresLogon=True,
        #                     parser=Regexer.FromExpresso(favRegex), creator=self.CreateEpisodeItem)

        self._AddDataParser("http://webapi.tv4play.se/play/categories.json", json=True, matchType=ParserData.MatchExact,
                            parser=(), creator=self.CreateCategoryItem)
        self._AddDataParser("http://webapi.tv4play.se/play/programs?platform=tablet&category=", json=True,
                            parser=self.episodeItemJson, creator=self.CreateEpisodeItem)

        self._AddDataParser("http://tv4live-i.akamaihd.net/hls/live/", updater=self.UpdateLiveItem)
        self._AddDataParser("http://tv4events1-lh.akamaihd.net/i/EXTRAEVENT5_1", updater=self.UpdateLiveItem)

        self.videoItemJson = ("results",)
        self._AddDataParser("*", preprocessor=self.PreProcessFolderList, json=True,
                            parser=self.videoItemJson, creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        #===============================================================================================================
        # non standard items
        self.maxPageSize = 25  # The Android app uses a page size of 20

        #===============================================================================================================
        # Test cases:
        #   Batman - WideVine
        #   Antikdeckarna - Clips

        # ====================================== Actual channel setup STOPS here =======================================
        return

    # def LogOn(self):
    #     """ Makes sure that we are logged on. """
    #
    #     username = AddonSettings.GetSetting("channel_tv4play_se_username")
    #     if not username:
    #         Logger.Info("No user name for TV4 Play, not logging in")
    #         return False
    #
    #     # Fetch an existing token
    #     tokenSettingId = "channel_tv4play_se_token"
    #     token = AddonSettings.GetSetting(tokenSettingId)
    #     sessionToken = None
    #     if token:
    #         expiresAt, vimondSessionToken, sessionToken = token.split("|")
    #         expireDate = DateHelper.GetDateFromPosix(float(expiresAt))
    #         if expireDate > datetime.datetime.now():
    #             Logger.Info("Found existing valid TV4Play token (valid until: %s)", expireDate)
    #             self.httpHeaders["Cookie"] = "JSESSIONID=%s; sessionToken=%s" % (vimondSessionToken, sessionToken)
    #             return True
    #         Logger.Warning("Found existing expired TV4Play token")
    #
    #     Logger.Info("Fetching a new TV4Play token")
    #     data = None
    #     if sessionToken:
    #         # 2a: try reauthenticating
    #         # POST https://account.services.tv4play.se/session/reauthenticate
    #         # session_token=<sessionToken>&client=tv4play-web
    #         # returns the same as authenticate
    #         Logger.Info("Reauthenticating based on the old TV4Play token")
    #         params = "session_token=%s&" \
    #                  "client=tv4play-web" % (
    #                      HtmlEntityHelper.UrlEncode(sessionToken)
    #                  )
    #         data = UriHandler.Open("https://account.services.tv4play.se/session/reauthenticate",
    #                                noCache=True, proxy=self.proxy, params=params)
    #
    #     if not data or "vimond_session_token" not in data:
    #         # 1: https://www.tv4play.se/session/new
    #         # Extract the "authenticity_token"
    #         Logger.Info("Authenticating based on username and password")
    #
    #         v = Vault()
    #         password = v.GetSetting("channel_tv4play_se_password")
    #         if not password:
    #             XbmcWrapper.ShowDialog(
    #                 title=None,
    #                 lines=LanguageHelper.GetLocalizedString(LanguageHelper.MissingCredentials),
    #                 # notificationType=XbmcWrapper.Error,
    #                 # displayTime=5000
    #             )
    #
    #         # 2b: https://account.services.tv4play.se/session/authenticate
    #         # Content-Type: application/x-www-form-urlencoded; charset=UTF-8
    #         params = "username=%s&" \
    #                  "password=%s&" \
    #                  "remember_me=true&" \
    #                  "client=tv4play-web" % (
    #                      HtmlEntityHelper.UrlEncode(username),
    #                      HtmlEntityHelper.UrlEncode(password),
    #                  )
    #         data = UriHandler.Open("https://account.services.tv4play.se/session/authenticate",
    #                                noCache=True, proxy=self.proxy, params=params)
    #         if not data:
    #             Logger.Error("Error logging in")
    #             return
    #
    #     # Extract the data we need
    #     data = JsonHelper(data)
    #     vimondSessionToken = data.GetValue('vimond_session_token')
    #     # vimondRememberMe = data.GetValue('vimond_remember_me')
    #     sessionToken = data.GetValue('session_token')
    #
    #     # 2c: alternative: POST https://account.services.tv4play.se/session/keep_alive
    #     # vimond_session_token=<vimondSessionToken>&session_token=<sessionToken>&client=tv4play-web
    #     # returns:
    #     # {"vimond_session_token":".....", # "vimond_remember_me":"......"}
    #
    #     # 3: https://token.services.tv4play.se/jwt?jsessionid=<vimondSessionToken>&client=tv4play-web
    #     # Get an OAuth token -> not really needed for the standard HTTP calls but it gets us the
    #     # expiration date
    #     tokenUrl = "https://token.services.tv4play.se/jwt?jsessionid=%s&client=tv4play-web" % (vimondSessionToken, )
    #     token = UriHandler.Open(tokenUrl, noCache=True, proxy=self.proxy)
    #     # Figure out the expiration data
    #     data, expires, other = token.split('.')
    #     expires += "=" * (4 - len(expires) % 4)
    #     Logger.Debug("Found data: \n%s\n%s\n%s", data, expires, other)
    #     tokenData = EncodingHelper.DecodeBase64(expires)
    #     tokenData = JsonHelper(tokenData)
    #     expiresAt = tokenData.GetValue("exp")
    #
    #     Logger.Debug("Token expires at: %s (%s)", DateHelper.GetDateFromPosix(float(expiresAt)), expiresAt)
    #     # AddonSettings.SetSetting(tokenSettingId, "%s|%s" % (expiresAt, token))
    #     AddonSettings.SetSetting(tokenSettingId, "%s|%s|%s" % (expiresAt, vimondSessionToken, sessionToken))
    #
    #     # 4: use with: Authorization: Bearer <token>
    #     # 4: use cookies:
    #     #  Cookie: JSESSIONID=<vimondSessionToken>;
    #     #  Cookie: sessionToken=<sessionToken>;
    #     #  Cookie: rememberme=<sessionToken>;
    #
    #     # return {"JSESSIONID": vimondSessionToken, "sessionToken": sessionToken}
    #     self.httpHeaders["Cookie"] = "JSESSIONID=%s; sessionToken=%s" % (vimondSessionToken, sessionToken)
    #     return True

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

        # Logger.Trace(resultSet)
        json = resultSet
        title = json["name"]

        programId = json["nid"]
        programId = HtmlEntityHelper.UrlEncode(programId)
        url = "http://webapi.tv4play.se/play/video_assets?platform=tablet&per_page=%s&is_live=false&type=episode&" \
              "page=1&node_nids=%s&start=0" % (self.maxPageSize, programId, )

        if "channel" in json and json["channel"]:
            channelId = json["channel"]["nid"]
            Logger.Trace("ChannelId found: %s", channelId)
        else:
            channelId = "tv4"
            Logger.Warning("ChannelId NOT found. Assuming %s", channelId)

        # match the exact channel or put them in TV4
        isMatchForChannel = channelId.startswith(self.__channelId)
        isMatchForChannel |= self.channelCode == "tv4se" and not channelId.startswith("sjuan") and not channelId.startswith("tv12")
        if not isMatchForChannel:
            Logger.Debug("Channel mismatch for '%s': %s vs %s", title, channelId, self.channelCode)
            return None

        item = mediaitem.MediaItem(title, url)
        # item.description = description
        item.icon = self.icon
        item.thumb = resultSet.get("program_image", self.noImage)
        item.isPaid = resultSet.get("is_premium", False)
        return item

    def AddCategoriesAndSpecials(self, data):
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

        # if self.channelCode != "tv4se":
        #     return data, items

        extras = {
            "\a.: S&ouml;k :.": (
                "searchSite", None, False
            )}

        # Channel 4 specific items
        if self.channelCode == "tv4se":
            extras.update({
                "\a.: Kategorier :.": (
                    "http://webapi.tv4play.se/play/categories.json", None, False
                ),
                "\a.: Mest sedda programmen just nu :.": (
                    "http://webapi.tv4play.se/play/video_assets/most_viewed?type=episode"
                    "&platform=tablet&is_live=false&per_page=%s&start=0" % (self.maxPageSize,),
                    None, False
                ),
            })
            # if self.loggedOn:
            #     extras.update({
            #         "\a.: Favoriter :.": (
            #             "http://www.tv4play.se/program/favourites",
            #             None, True
            #         ),
            #     })

            today = datetime.datetime.now()
            days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
            for i in range(0, 7, 1):
                startDate = today - datetime.timedelta(i)
                endDate = startDate + datetime.timedelta(1)

                day = days[startDate.weekday()]
                if i == 0:
                    day = "Idag"
                elif i == 1:
                    day = "Igår"

                Logger.Trace("Adding item for: %s - %s", startDate, endDate)
                # url = "http://webapi.tv4play.se/play/video_assets?exclude_node_nids=" \
                #       "nyheterna,v%C3%A4der,ekonomi,lotto,sporten,nyheterna-blekinge,nyheterna-bor%C3%A5s," \
                #       "nyheterna-dalarna,nyheterna-g%C3%A4vle,nyheterna-g%C3%B6teborg,nyheterna-halland," \
                #       "nyheterna-helsingborg,nyheterna-j%C3%B6nk%C3%B6ping,nyheterna-kalmar,nyheterna-link%C3%B6ping," \
                #       "nyheterna-lule%C3%A5,nyheterna-malm%C3%B6,nyheterna-norrk%C3%B6ping,nyheterna-skaraborg," \
                #       "nyheterna-skellefte%C3%A5,nyheterna-stockholm,nyheterna-sundsvall,nyheterna-ume%C3%A5," \
                #       "nyheterna-uppsala,nyheterna-v%C3%A4rmland,nyheterna-v%C3%A4st,nyheterna-v%C3%A4ster%C3%A5s," \
                #       "nyheterna-v%C3%A4xj%C3%B6,nyheterna-%C3%B6rebro,nyheterna-%C3%B6stersund,tv4-tolken," \
                #       "fotbollskanalen-europa" \
                #       "&platform=tablet&per_page=32&is_live=false&product_groups=2&type=episode&per_page=100"
                url = "http://webapi.tv4play.se/play/video_assets?exclude_node_nids=" \
                      "&platform=tablet&per_page=32&is_live=false&product_groups=2&type=episode&per_page=100"
                url = "%s&broadcast_from=%s&broadcast_to=%s&" % (url, startDate.strftime("%Y%m%d"), endDate.strftime("%Y%m%d"))
                dayName = "\a.: %s :." % (day, )
                extras[dayName] = (url, startDate, False)

        extras["\a.: Lives&#xE4;ndningar :."] = (
            "http://webapi.tv4play.se/play/video_assets?exclude_node_nids=&platform=tablet&"
            "per_page=32&is_live=true&product_groups=2&type=episode&per_page=100", None, False)

        for name in extras:
            url, date, isLive = extras[name]
            item = mediaitem.MediaItem(name, url)
            item.dontGroup = True
            item.complete = True
            item.thumb = self.noImage
            item.HttpHeaders = self.httpHeaders
            item.isLive = isLive

            if date is not None:
                item.SetDate(date.year, date.month, date.day, 0, 0, 0, text=date.strftime("%Y-%m-%d"))
            else:
                item.SetDate(1901, 1, 1, 0, 0, 0, text="")
            items.append(item)

        if not self.channelCode == "tv4se":
            return data, items

        # live = mediaitem.MediaItem("\a.: Live-TV :.",
        #                            "http://tv4events1-lh.akamaihd.net/i/EXTRAEVENT5_1@324055/master.m3u8",
        #                            type="video")
        # live.dontGroup = True
        # # live.isDrmProtected = True
        # live.isGeoLocked = True
        # live.isLive = True
        # items.append(live)

        Logger.Debug("Pre-Processing finished")
        return data, items

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
        url = "http://webapi.tv4play.se/play/video_assets?platform=tablet&per_page=%s&page=1" \
              "&sort_order=desc&type=episode&q=%%s&start=0" % (self.maxPageSize, )
        return chn_class.Channel.SearchSite(self, url)

    # def FetchWithToken(self, data):
    #     items = []
    #     additionalHeaders = {}
    #     for token in self.token:
    #
    #
    #     data = UriHandler.Open("https://personalization.services.tv4play.se/favorites", proxy=self.proxy,
    #                            additionalHeaders=additionalHeaders)
    #     return data, items

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

        # Add a klip folder only on the first page and only if it is not already a clip page
        if "type=clip" not in self.parentItem.url \
                and "&page=1&" in self.parentItem.url \
                and "node_nids=" in self.parentItem.url:
            # get the category ID
            catStart = self.parentItem.url.rfind("node_nids=")
            # catEnd = self.parentItem.url.rfind("&start")
            catId = self.parentItem.url[catStart + 10:]
            Logger.Debug("Currently doing CatId: '%s'", catId)

            url = "http://webapi.tv4play.se/play/video_assets?platform=tablet&per_page=%s&" \
                  "type=clip&page=1&node_nids=%s&start=0" % (self.maxPageSize, catId,)
            clipsTitle = LanguageHelper.GetLocalizedString(LanguageHelper.Clips)
            clips = mediaitem.MediaItem(clipsTitle, url)
            clips.icon = self.icon
            clips.thumb = self.noImage
            clips.complete = True
            items.append(clips)

        # find the max number of items ("total_hits":2724)
        totalItems = int(Regexer.DoRegex('total_hits\W+(\d+)', data)[-1])
        Logger.Debug("Found total of %s items. Only showing %s.", totalItems, self.maxPageSize)
        if totalItems > self.maxPageSize and "&page=1&" in self.parentItem.url:
            # create a group item
            moreTitle = LanguageHelper.GetLocalizedString(LanguageHelper.MorePages)
            more = mediaitem.MediaItem(moreTitle, "")
            more.icon = self.icon
            more.thumb = self.noImage
            more.complete = True
            items.append(more)

            # what are the total number of pages?
            currentPage = 1
            totalPages = int(math.ceil(1.0 * totalItems / self.maxPageSize))

            currentUrl = self.parentItem.url
            needle = "&page="
            while currentPage < totalPages:
                # what is the current page
                currentPage += 1

                url = currentUrl.replace("%s1" % (needle, ), "%s%s" % (needle, currentPage))
                Logger.Debug("Adding next page: %s\n%s", currentPage, url)
                page = mediaitem.MediaItem(str(currentPage), url)
                page.icon = self.icon
                page.thumb = self.noImage
                page.type = "page"
                page.complete = True

                if totalPages == 2:
                    items = [page]
                    break
                else:
                    more.items.append(page)

        Logger.Debug("Pre-Processing finished")
        return data, items

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

        Logger.Trace('starting FormatVideoItem for %s', self.channelName)
        # Logger.Trace(resultSet)

        # the vmanProgramId (like 1019976) leads to http://anytime.tv4.se/webtv/metafileFlash.smil?p=1019976&bw=1000&emulate=true&sl=true
        programId = resultSet["id"]
        # Logger.Debug("ProgId = %s", programId)

        url = "https://playback-api.b17g.net/media/%s?service=tv4&device=browser&protocol=hls" % (programId,)
        name = resultSet["title"]

        item = mediaitem.MediaItem(name, url)
        item.description = resultSet["description"]
        if item.description is None:
            item.description = item.name

        # premium_expire_date_time=2099-12-31T00:00:00+01:00
        date = resultSet["published_date_time"]
        (datePart, timePart) = date.split("T")
        (year, month, day) = datePart.split("-")
        (hour, minutes, rest1, zone) = timePart.split(":")
        item.SetDate(year, month, day, hour, minutes, 00)
        broadcastDate = datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))

        thumbUrl = resultSet["image"]
        item.thumb = thumbUrl

        # premium = json["premium"] == "true"
        availability = resultSet["availability"]
        freePeriod = availability["availability_group_free"]
        premiumPeriod = availability["availability_group_premium"]

        now = datetime.datetime.now()
        if False and not premiumPeriod == "0":
            # always premium
            freeExpired = now - datetime.timedelta(days=99 * 365)
        elif freePeriod == "30+" or freePeriod is None:
            freeExpired = broadcastDate + datetime.timedelta(days=99 * 365)
        else:
            freeExpired = broadcastDate + datetime.timedelta(days=int(freePeriod))
        Logger.Trace("Premium info for: %s\nPremium state: %s\nFree State:    %s\nBroadcast %s vs Expired %s",
                     name, premiumPeriod, freePeriod, broadcastDate, freeExpired)

        if now > freeExpired:
            # item.name = "%s [Premium-innehåll]" % (item.name,)
            item.isPaid = True

        item.type = "video"
        item.complete = False
        item.icon = self.icon
        item.isGeoLocked = resultSet["is_geo_restricted"]
        item.isDrmProtected = resultSet["is_drm_protected"]
        item.isLive = resultSet.get("is_live", False)
        if item.isLive:
            item.url = "{0}&is_live=true".format(item.url)

        return item

    def CreateCategoryItem(self, resultSet):
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

        cat = HtmlEntityHelper.UrlEncode(resultSet['nid'])
        url = "http://webapi.tv4play.se/play/programs?platform=tablet&category=%s" \
              "&fl=nid,name,program_image,category,logo,is_premium" \
              "&per_page=1000&is_active=true&start=0" % (cat, )
        item = mediaitem.MediaItem(resultSet['name'], url)
        item.thumb = self.noImage
        item.type = 'folder'
        item.complete = True
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

        # noinspection PyStatementEffect
        """
                C:\temp\rtmpdump-2.3>rtmpdump.exe -z -o test.flv -n "cp70051.edgefcs.net" -a "tv
                4ondemand" -y "mp4:/mp4root/2010-06-02/pid2780626_1019976_T3MP48_.mp4?token=c3Rh
                cnRfdGltZT0yMDEwMDcyNjE2NDYyNiZlbmRfdGltZT0yMDEwMDcyNjE2NDgyNiZkaWdlc3Q9ZjFjN2U1
                NTRiY2U5ODMxMDMwYWQxZWEwNzNhZmUxNjI=" -l 2

                C:\temp\rtmpdump-2.3>rtmpdump.exe -z -o test.flv -r rtmpe://cp70051.edgefcs.net/
                tv4ondemand/mp4root/2010-06-02/pid2780626_1019976_T3MP48_.mp4?token=c3RhcnRfdGlt
                ZT0yMDEwMDcyNjE2NDYyNiZlbmRfdGltZT0yMDEwMDcyNjE2NDgyNiZkaWdlc3Q9ZjFjN2U1NTRiY2U5
                ODMxMDMwYWQxZWEwNzNhZmUxNjI=
                """

        # retrieve the mediaurl
        data = UriHandler.Open(item.url, proxy=self.proxy, additionalHeaders=self.localIP)
        streamInfo = JsonHelper(data)
        m3u8Url = streamInfo.GetValue("playbackItem", "manifestUrl")

        part = item.CreateNewEmptyMediaPart()

        if AddonSettings.UseAdaptiveStreamAddOn():
            stream = part.AppendMediaStream(m3u8Url, 0)
            M3u8.SetInputStreamAddonInput(stream, self.proxy)
            item.complete = True
        else:
            m3u8Data = UriHandler.Open(m3u8Url, proxy=self.proxy, additionalHeaders=self.localIP)
            for s, b, a in M3u8.GetStreamsFromM3u8(m3u8Url, self.proxy, playListData=m3u8Data, mapAudio=True):
                item.complete = True
                if not item.isLive and "-video" not in s:
                    continue

                if a and "-audio" not in s:
                    videoPart = s.rsplit("-", 1)[-1]
                    videoPart = "-%s" % (videoPart,)
                    s = a.replace(".m3u8", videoPart)
                part.AppendMediaStream(s, b)

        # subtitle = M3u8.GetSubtitle(m3u8Url, playListData=m3u8Data)
        # Not working due to VTT format.
        # if subtitle:
        #     part.Subtitle = SubtitleHelper.DownloadSubtitle(subtitle,
        #                                                     format="m3u8srt",
        #                                                     proxy=self.proxy)
        return item

    def UpdateLiveItem(self, item):
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

        Logger.Debug('Starting UpdateLiveItem for %s (%s)', item.name, self.channelName)

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()

        spoofIp = self._GetSetting("spoof_ip", "0.0.0.0")
        if spoofIp:
            for s, b in M3u8.GetStreamsFromM3u8(item.url, self.proxy, headers={"X-Forwarded-For": spoofIp}):
                part.AppendMediaStream(s, b)
        else:
            for s, b in M3u8.GetStreamsFromM3u8(item.url, self.proxy):
                part.AppendMediaStream(s, b)

        item.complete = True
        return item
