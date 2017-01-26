import chn_class
from regexer import Regexer
from parserdata import ParserData
from logger import Logger
from urihandler import UriHandler
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.jsonhelper import JsonHelper
from streams.m3u8 import M3u8
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
        self.noImage = "vrtnuimage.png"
        self.mainListUri = "https://www.vrt.be/vrtnu/a-z/"
        self.baseUrl = "https://www.vrt.be"

        episodeRegex = '<a[^>]+href="(?<url>/vrtnu[^"]+)"[^>]*>(?:\W*<div[^>]*>\W*){2}' \
                       '<picture[^>]*>\W+<source[^>]+srcset="(?<thumburl>[^ ]+)[\w\W]{0,2000}?' \
                       '<h3[^>]+>(?<title>[^<]+)<span[^>]+>&lt;p&gt;(?<description>[^<]+)' \
                       '&lt;/p&gt;<'
        episodeRegex = Regexer.FromExpresso(episodeRegex)
        self._AddDataParser(self.mainListUri, name="Main A-Z listing",
                            matchType=ParserData.MatchExact,
                            parser=episodeRegex, creator=self.CreateEpisodeItem)

        folderRegex = '<option[^>]+data-href="/(?<url>[^"]+)">(?<title>[^<]+)</option>'
        folderRegex = Regexer.FromExpresso(folderRegex)
        self._AddDataParser("*", name="Folder/Season parser",
                            parser=folderRegex, creator=self.CreateFolderItem)

        videoRegex = '<a[^>]+href="(?<url>/vrtnu[^"]+)"[^>]*>(?:\W*<div[^>]*>\W*){2}' \
                     '<picture[^>]*>\W+<source[^>]+srcset="(?<thumburl>[^ ]+)[^>]*>\W*' \
                     '<img[^>]+>\W*(?:</\w+>\W*)+<div[^>]+>\W*<h3[^>]+>(?<title>[^<]+)</h3>' \
                     '[\w\W]{0,1000}?(?:<span[^>]+tile__broadcastdate--other[^>]+>' \
                     '(?<subtitle>[^<]+)</span></div><div>)?<abbr[^>]+title'
        videoRegex = Regexer.FromExpresso(videoRegex)
        self._AddDataParser("*", name="Video item parser",
                            parser=videoRegex, creator=self.CreateVideoItem)

        # needs to be after the standard video item regex
        singleVideoRegex = '<picture[^>]*>\W+<source[^>]+srcset="(?<thumburl>[^ ]+)[\w\W]{0,4000}' \
                           '<span[^>]+id="title"[^>]*>(?<title>[^<]+)</span>\W*<span[^>]+>' \
                           '(?<description>[^<]+)'
        singleVideoRegex = Regexer.FromExpresso(singleVideoRegex)
        self._AddDataParser("*", name="Single video item parser",
                            parser=singleVideoRegex, creator=self.CreateVideoItem)

        self._AddDataParser("*", updater=self.UpdateVideoItem, requiresLogon=True)

        # ===============================================================================================================
        # non standard items
        self.__hasAlreadyVideoItems = False

        # ===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def LogOn(self):
        tokenCookie = UriHandler.GetCookie("X-VRT-Token", ".vrt.be")
        if tokenCookie is not None:
            return True

        username = self._GetSetting("username")
        if not username:
            return None

        v = Vault()
        password = v.GetChannelSetting(self.guid, "password")

        Logger.Debug("Using: %s / %s", username, "*" * len(password))
        url = "https://accounts.eu1.gigya.com/accounts.login"
        data = "loginID=%s" \
               "&password=%s" \
               "&targetEnv=jssdk" \
               "&APIKey=3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG" \
               "&includeSSOToken=true" \
               "&authMode=cookie" % \
               (HtmlEntityHelper.UrlEncode(username), HtmlEntityHelper.UrlEncode(password))

        logonData = UriHandler.Open(url, params=data, proxy=self.proxy, noCache=True)
        sig, uid, timestamp = self.__ExtractSessionData(logonData)
        url = "https://token.vrt.be/"
        tokenData = '{"uid": "%s", ' \
                    '"uidsig": "%s", ' \
                    '"ts": "%s", ' \
                    '"fn": "VRT", "ln": "NU", ' \
                    '"email": "%s"}' % (uid, sig, timestamp, username)

        headers = {"Content-Type": "application/json", "Referer": "https://www.vrt.be/vrtnu/"}
        UriHandler.Open(url, params=tokenData, proxy=self.proxy, additionalHeaders=headers)
        return True

    def CreateEpisodeItem(self, resultSet):
        item = chn_class.Channel.CreateEpisodeItem(self, resultSet)

        if item is not None and item.thumb and item.thumb.startswith("//"):
            item.thumb = "https:%s" % (item.thumb, )

        return item

    def CreateFolderItem(self, resultSet):
        item = chn_class.Channel.CreateFolderItem(self, resultSet)
        if item is None:
            return None

        item.name = item.name.title()
        return item

    def CreateVideoItem(self, resultSet):
        resultSet["title"] = resultSet["title"].strip()
        if "url" not in resultSet:
            if self.__hasAlreadyVideoItems:
                Logger.Debug("Found a 'single' item, but we have more. So this is a duplicate")
                return None

            # this only happens once with single video folders
            resultSet["url"] = self.parentItem.url

        item = chn_class.Channel.CreateVideoItem(self, resultSet)
        if item is None:
            return None

        if "year" in resultSet and resultSet["year"]:
            item.SetDate(resultSet["year"], resultSet["month"], resultSet["day"])
        if item.thumb.startswith("//"):
            item.thumb = "https:%s" % (item.thumb, )

        self.__hasAlreadyVideoItems = True
        return item

    def UpdateVideoItem(self, item):
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        # we need to fetch the actual url as it might differ for single video items
        data, secureUrl = UriHandler.Header(item.url, proxy=self.proxy)

        secureUrl = secureUrl.rstrip("/")
        secureUrl = "%s.securevideo.json" % (secureUrl, )
        data = UriHandler.Open(secureUrl, proxy=self.proxy, additionalHeaders=item.HttpHeaders)
        secureData = JsonHelper(data, logger=Logger.Instance())
        mzid = secureData.GetValue(secureData.json.keys()[0], "mzid")
        assetUrl = "https://mediazone.vrt.be/api/v1/vrtvideo/assets/%s" % (mzid, )
        data = UriHandler.Open(assetUrl, proxy=self.proxy)
        assetData = JsonHelper(data, logger=Logger.Instance())

        for streamData in assetData.GetValue("targetUrls"):
            if streamData["type"] != "HLS":
                continue

            part = item.CreateNewEmptyMediaPart()
            for s, b in M3u8.GetStreamsFromM3u8(streamData["url"], self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)
        return item

    def __ExtractSessionData(self, logonData):
        logonJson = JsonHelper(logonData)
        resultCode = logonJson.GetValue("statusCode")
        if resultCode != 200:
            Logger.Error("Error loging in: %s - %s", logonJson.GetValue("errorMessage"),
                         logonJson.GetValue("errorDetails"))
            return False

        return \
            logonJson.GetValue("UIDSignature"), \
            logonJson.GetValue("UID"), \
            logonJson.GetValue("signatureTimestamp")
