import chn_class
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.jsonhelper import JsonHelper
from mediaitem import MediaItem
from logger import Logger
from regexer import Regexer
from urihandler import UriHandler
from parserdata import ParserData
from streams.m3u8 import M3u8
from helpers.datehelper import DateHelper
from addonsettings import AddonSettings
from xbmcwrapper import XbmcWrapper
from helpers.languagehelper import LanguageHelper
from awsidp import AwsIdp
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

        # setup the main parsing data
        if self.channelCode == "vijfbe":
            self.noImage = "vijfimage.png"
            self.mainListUri = "https://www.vijf.be/programmas"
            self.baseUrl = "https://www.vijf.be"
        # elif self.channelCode == "zesbe":
        #     self.noImage = "zesimage.png"
        #     self.mainListUri = "https://www.zestv.be/programmas"
        #     self.baseUrl = "https://www.zestv.be"
        else:
            self.noImage = "vierimage.png"
            self.mainListUri = "https://www.vier.be/programmas"
            self.baseUrl = "https://www.vier.be"

        episodeRegex = '<a class="program-overview__link" href="(?<url>[^"]+)">(?<title>[^<]+)</a>'
        episodeRegex = Regexer.FromExpresso(episodeRegex)
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            parser=episodeRegex,
                            creator=self.CreateEpisodeItem)

        videoRegex = '<a[^>]+href="(?<url>/video/[^"]+)"[^<]+<div[^<]+<div class="card-teaser__image"[^>]+url\((?<thumburl>[^)]+)[\w\W]{500,2000}?<div[^>]+data-videoid="(?<videoid>[^"]+)"[\w\W]{0,2000}?<h3[^>]*>(?<title>[^<]+)</h3>\W+<div[^>]*>[^<]*</div>\W+<div[^>]+timestamp="(?<timestamp>\d+)'
        videoRegex = Regexer.FromExpresso(videoRegex)
        self._AddDataParser("*", matchType=ParserData.MatchExact,
                            parser=videoRegex,
                            creator=self.CreateVideoItem)

        pageRegex = '<button class="button button--default js-load-more-button"\W+data-url="(?<url>[^"]+)"\W+data-page="(?<title>\d+)"'
        pageRegex = Regexer.FromExpresso(pageRegex)
        self._AddDataParser("*", matchType=ParserData.MatchExact,
                            parser=pageRegex,
                            creator=self.CreatePageItem)

        self._AddDataParser("/api/program/fixed/", name="API paging",
                            matchType=ParserData.MatchContains,
                            # json=False,
                            preprocessor=self.ExtractPageData,
                            parser=videoRegex,
                            creator=self.CreateVideoItem)

        imageVideoRegex = '<a[^>]+url\((?<thumburl>[^)]+)[^>]+href="(?<url>/video/[^"]+)"[\w\W]{500,2000}<h3[^>]+>(?<title>[^<]+)</h3>\W*<div[^>]*>(?<description>[^<]+)(?:</div>\W*<div[^>]*>\W*)?<div[^>]+data-videoid="(?<videoid>[^"]+)"'
        imageVideoRegex = Regexer.FromExpresso(imageVideoRegex)
        self._AddDataParser("*", matchType=ParserData.MatchExact,
                            parser=imageVideoRegex,
                            creator=self.CreateVideoItem)

        # Generic updater with login
        self._AddDataParser("*",
                            # requiresLogon=True,
                            updater=self.UpdateVideoItem)

        # ==========================================================================================
        # Channel specific stuff
        self.__idToken = None

        # ==========================================================================================
        # Test cases:
        # Documentaire: pages (has http://www.canvas.be/tag/.... url)
        # Not-Geo locked: Kroost

        # ====================================== Actual channel setup STOPS here ===================
        return

    def LogOn(self):
        if self.__idToken:
            return True

        # check if there is a refresh token
        # refresh token: viervijfzes_refresh_token
        refreshToken = AddonSettings.GetSetting("viervijfzes_refresh_token")
        client = AwsIdp("eu-west-1_dViSsKM5Y", "6s1h851s8uplco5h6mqh1jac8m",
                        proxy=self.proxy, logger=Logger.Instance())
        if refreshToken:
            idToken = client.RenewToken(refreshToken)
            if idToken:
                self.__idToken = idToken
                return True
            else:
                Logger.Info("Extending token for VierVijfZes failed.")

        # username: viervijfzes_username
        username = AddonSettings.GetSetting("viervijfzes_username")
        # password: viervijfzes_password
        v = Vault()
        password = v.GetSetting("viervijfzes_password")
        if not username or not password:
            XbmcWrapper.ShowDialog(
                title=None,
                lines=LanguageHelper.GetLocalizedString(LanguageHelper.MissingCredentials),
            )
            return False

        idToken, refreshToken = client.Authenticate(username, password)
        if not idToken or not refreshToken:
            Logger.Error("Error getting a new token. Wrong password?")
            return False

        self.__idToken = idToken
        AddonSettings.SetSetting("viervijfzes_refresh_token", refreshToken)
        return True

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

        item = chn_class.Channel.CreateEpisodeItem(self, resultSet)
        if item is None:
            return item

        # All of vier.be video's seem GEO locked.
        item.isGeoLocked = True
        item.thumb = item.thumb or self.noImage
        return item

    def CreatePageItem(self, resultSet):
        resultSet["url"] = "{0}/{1}".format(resultSet["url"], resultSet["title"])
        resultSet["title"] = str(int(resultSet["title"]) + 1)

        item = self.CreateFolderItem(resultSet)
        item.type = "page"
        return item

    def ExtractPageData(self, data):
        items = []
        json = JsonHelper(data)
        data = json.GetValue("data")
        Logger.Trace(data)

        if json.GetValue("loadMore", fallback=False):
            url, page = self.parentItem.url.rsplit("/", 1)
            url = "{0}/{1}".format(url, int(page) + 1)
            pageItem = MediaItem("{0}".format(int(page) + 2), url)
            pageItem.type = "page"
            items.append(pageItem)
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

        item = chn_class.Channel.CreateVideoItem(self, resultSet)

        if "date" in resultSet:
            day, month, year = resultSet["date"].split("/")
            item.SetDate(year, month, day)

        # All of vier.be video's seem GEO locked.
        item.isGeoLocked = True

        # Set the correct url
        # videoId = resultSet["videoid"]
        # item.url = "https://api.viervijfzes.be/content/%s" % (videoId, )
        if "timestamp" in resultSet:
            dateTime = DateHelper.GetDateFromPosix(int(resultSet["timestamp"]))
            item.SetDate(dateTime.year, dateTime.month, dateTime.day, dateTime.hour,
                         dateTime.minute,
                         dateTime.second)

        if item.thumb and item.thumb != self.noImage:
            item.thumb = HtmlEntityHelper.StripAmp(item.thumb)
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

        # https://api.viervijfzes.be/content/c58996a6-9e3d-4195-9ecf-9931194c00bf
        # videoId = item.url.split("/")[-1]
        # url = "%s/video/v3/embed/%s" % (self.baseUrl, videoId,)
        url = item.url
        data = UriHandler.Open(url, proxy=self.proxy)
        return self.__UpdateVideo(item, data)

    def __UpdateVideo(self, item, data):
        regex = 'data-file="([^"]+)'
        m3u8Url = Regexer.DoRegex(regex, data)[-1]

        if ".m3u8" not in m3u8Url:
            Logger.Info("Not a direct M3u8 file. Need to log in")
            url = "https://api.viervijfzes.be/content/%s" % (m3u8Url, )

            # We need to log in
            if not self.loggedOn:
                self.LogOn()

            # add authorization header
            authenticationHeader = {
                "authorization": self.__idToken,
                "content-type": "application/json"
            }
            data = UriHandler.Open(url, proxy=self.proxy, additionalHeaders=authenticationHeader)
            jsonData = JsonHelper(data)
            m3u8Url = jsonData.GetValue("video", "S")

        # Geo Locked?
        if "geo" in m3u8Url.lower():
            # set it for the error statistics
            item.isGeoLocked = True

        part = item.CreateNewEmptyMediaPart()
        for s, b in M3u8.GetStreamsFromM3u8(m3u8Url, self.proxy):
            if int(b) < 200:
                Logger.Info("Skipping stream of quality '%s' kbps", b)
                continue

            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)

        item.complete = True
        return item
