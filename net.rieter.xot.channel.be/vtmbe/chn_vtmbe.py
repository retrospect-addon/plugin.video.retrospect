import time
import re

import chn_class
from logger import Logger
from mediaitem import MediaItem
from vault import Vault
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper
from addonsettings import AddonSettings
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.datehelper import DateHelper
from streams.m3u8 import M3u8
from regexer import Regexer
from xbmcwrapper import XbmcWrapper
from helpers.languagehelper import LanguageHelper
from parserdata import ParserData


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

        # setup the urls
        self.__api = None
        self.__sso = None
        if self.channelCode == "vtm":
            self.noImage = "vtmbeimage.jpg"
            # self.mainListUri = "http://vtm.be/feed/programs?format=json&type=all&only_with_video=true"
            self.mainListUri = "http://vtm.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen"
            self.baseUrl = "http://vtm.be"
            self.__app = "vtm_watch"
            self.__sso = "vtm-sso"
            self.__apiKey = "vtm-b7sJGrKwMJj0VhdZvqLDFvgkJF5NLjNY"

            # self._AddDataParser("http://vtm.be/feed/articles?program=", json=True,
            #                     name="JSON Parser for Video Only results",
            #                     creator=self.CreateVideoItem, parser=("response", "items"))

            # setup the main parsing data in case of HTML
            htmlVideoRegex = '<img[^>]+class="media-object"[^>]+src="(?<thumburl>[^"]+)[^>]*>[\w\W]{0,1000}?<a[^>]+href="/(?<url>[^"]+)"[^>]*>(?<title>[^<]+)'
            htmlVideoRegex = Regexer.FromExpresso(htmlVideoRegex)
            self._AddDataParser(
                "http://vtm.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&",
                name="HTML Page Video Parser for VTM",
                parser=htmlVideoRegex, creator=self.CreateVideoItemHtml)

        elif self.channelCode == "q2":
            self.noImage = "q2beimage.jpg"
            # self.mainListUri = "http://www.q2.be/feed/programs?format=json&type=all&only_with_video=true"
            self.mainListUri = "http://www.q2.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen"
            self.baseUrl = "http://www.q2.be"
            self.__app = "q2"
            self.__sso = "q2-sso"
            self.__apiKey = "q2-html5-NNSMRSQSwGMDAjWKexV4e5Vm6eSPtupk"

            htmlVideoRegex = '<a[^>]+class="cta-full[^>]+href="/(?<url>[^"]+)"[^>]*>[^<]*</a>\W*<span[^>]*>[^<]*</[^>]*\W*<div[^>]*>\W*<img[^>]+src="(?<thumburl>[^"]+)[\w\W]{0,1000}?<h3[^>]*>(?<title>[^<]+)'
            htmlVideoRegex = Regexer.FromExpresso(htmlVideoRegex)
            self._AddDataParser(
                "http://www.q2.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&",
                name="HTML Page Video Parser for Q2",
                parser=htmlVideoRegex, creator=self.CreateVideoItemHtml)
        else:
            raise NotImplementedError("%s not supported yet" % (self.channelCode, ))

        # generic to all channels
        htmlEpisodeRegex = '<a[^>]+href="(?<url>http[^"]+im_field_program[^"]+)"[^>]*>(?<title>[^(<]+)'
        htmlEpisodeRegex = Regexer.FromExpresso(htmlEpisodeRegex)
        self._AddDataParser(
            "sm_field_video_origin_cms_longform%3AVolledige%20afleveringen",
            matchType=ParserData.MatchEnd,
            name="HTML Page Show Parser",
            preprocessor=self.AddLiveChannel,
            parser=htmlEpisodeRegex,
            creator=self.CreateEpisodeItemHtml)

        self._AddDataParser(
            "http://(?:vtm.be|www.q2.be)/video/?.+=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&.+id=\d+",
            matchType=ParserData.MatchRegex,
            name="HTML Page Video Updater",
            updater=self.UpdateVideoItem, requiresLogon=True)

        # setup the main parsing data in case of JSON
        self._AddDataParser("/feed/programs?format=json&type=all&only_with_video=true",
                            matchType=ParserData.MatchEnd,
                            name="JSON Feed Show Parser for Medialaan",
                            json=True, preprocessor=self.AddLiveChannelAndFetchAllData,
                            creator=self.CreateEpisodeItemJson, parser=("response", "items"))

        self._AddDataParser("http://vod.medialaan.io/api/1.0/list", json=True,
                            name="JSON Video Parser for Medialaan",
                            parser=("response", "items"), creator=self.CreateVideoItemJson)

        self._AddDataParser("http://vod.medialaan.io/vod/v2/videos/",
                            matchType=ParserData.MatchRegex,
                            name="JSON Video Updater for Medialaan",
                            updater=self.UpdateVideoItemJson, requiresLogon=True)

        self._AddDataParser("#livestream", name="Live Stream Updater", requiresLogon=True,
                            updater=self.UpdateLiveStream)

        # ===============================================================================================================
        # non standard items
        self.__signature = None
        self.__signatureTimeStamp = None
        self.__userId = None
        self.__cleanRegex = re.compile("<[^>]+>")

        # ===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def LogOn(self):
        signatureSettings = "mediaan_signature"
        signatureSetting = AddonSettings.GetSetting(signatureSettings)
        if signatureSetting and "|" not in signatureSetting:
            url = "https://accounts.eu1.gigya.com/accounts.getAccountInfo"
            data = "APIKey=3_HZ0FtkMW_gOyKlqQzW5_0FHRC7Nd5XpXJZcDdXY4pk5eES2ZWmejRW5egwVm4ug-" \
                   "&sdk=js_6.5.23" \
                   "&login_token=%s" % (signatureSetting, )
            logonData = UriHandler.Open(url, params=data, proxy=self.proxy, noCache=True)
            if self.__ExtractSessionData(logonData, signatureSettings):
                return True
            Logger.Warning("Failed to extend the VTM.be session.")

        Logger.Info("Logging onto VTM.be")
        v = Vault()
        password = v.GetSetting("mediaan_password")
        username = AddonSettings.GetSetting("mediaan_username")
        if not username or not password:
            XbmcWrapper.ShowDialog(
                title=None,
                lines=LanguageHelper.GetLocalizedString(LanguageHelper.MissingCredentials),
                # notificationType=XbmcWrapper.Error,
                # displayTime=5000
            )
            return False

        Logger.Debug("Using: %s / %s", username, "*" * len(password))
        url = "https://accounts.eu1.gigya.com/accounts.login"
        data = "loginID=%s" \
               "&password=%s" \
               "&targetEnv=jssdk" \
               "&APIKey=3_HZ0FtkMW_gOyKlqQzW5_0FHRC7Nd5XpXJZcDdXY4pk5eES2ZWmejRW5egwVm4ug-" \
               "&includeSSOToken=true" \
               "&authMode=cookie" % \
               (HtmlEntityHelper.UrlEncode(username), HtmlEntityHelper.UrlEncode(password))

        logonData = UriHandler.Open(url, params=data, proxy=self.proxy, noCache=True)
        return self.__ExtractSessionData(logonData, signatureSettings)

    def AddLiveChannelAndFetchAllData(self, data):
        data, items = self.AddLiveChannel(data)

        # The current issue with this is that the API is providing only the videos and not
        # the full episodes.

        json = JsonHelper(data)
        jsonItems = json.GetValue("response", "items")
        count = json.GetValue("response", "total")
        for i in range(100, count, 100):
            url = "%s&from=%s" % (self.mainListUri, i)
            Logger.Debug("Retrieving more items from: %s", url)
            moreData = UriHandler.Open(url, proxy=self.proxy)
            moreJson = JsonHelper(moreData)
            moreItems = moreJson.GetValue("response", "items")
            if moreItems:
                jsonItems += moreItems

        return json, items

    def CreateEpisodeItemJson(self, resultSet):
        """Creates a new MediaItem for an episode

       Arguments:
       resultSet : list[string] - the resultSet of the self.episodeItemRegex

       Returns:
       A new MediaItem of type 'folder'

       This method creates a new MediaItem from the Regular Expression or Json
       results <resultSet>. The method should be implemented by derived classes
       and are specific to the channel.

       """

        Logger.Trace(resultSet)

        title = resultSet['title']

        if resultSet["parent_series_oid"] is None:
            return None
        # if not resultSet["is_featured"]:
        #     # most of them are empty anyways
        #     return None

        url = "http://vod.medialaan.io/api/1.0/list?" \
              "app_id=%s&parentSeriesOID=%s" % (self.__app, resultSet['parent_series_oid'])
        item = MediaItem(title, url)
        item.fanart = self.fanart
        item.thumb = self.noImage
        item.description = resultSet.get('body', None)
        if item.description:
            # Clean HTML
            item.description = item.description.replace("<br />", "\n\n")
            item.description = self.__cleanRegex.sub("", item.description)

        if 'images' in resultSet and 'image' in resultSet['images']:
            item.thumb = resultSet['images']['image'].get('full', self.noImage)
        return item

    def CreateVideoItemJson(self, resultSet):
        Logger.Trace(resultSet)

        title = resultSet['title']
        url = "http://vod.medialaan.io/vod/v2/videos/%(id)s" % resultSet
        item = MediaItem(title, url, type="video")
        item.description = resultSet.get('text')

        if 'image' in resultSet:
            item.thumb = resultSet['image'].get("full", None)

        created = DateHelper.GetDateFromPosix(resultSet['created'])
        item.SetDate(created.year, created.month, created.day, created.hour, created.minute,
                     created.second)

        return item

    def UpdateVideoItemJson(self, item):
        videoId = item.url.rsplit("/", 1)[-1]
        return self.__UpdateVideoItem(item, videoId)

    # Used for video's only
    # def CreateVideoItem(self, resultSet):
    #     """Creates a MediaItem of type 'video' using the resultSet from the regex.
    #
    #     Arguments:
    #     resultSet : tuple (string) - the resultSet of the self.videoItemRegex
    #
    #     Returns:
    #     A new MediaItem of type 'video' or 'audio' (despite the method's name)
    #
    #     This method creates a new MediaItem from the Regular Expression or Json
    #     results <resultSet>. The method should be implemented by derived classes
    #     and are specific to the channel.
    #
    #     If the item is completely processed an no further data needs to be fetched
    #     the self.complete property should be set to True. If not set to True, the
    #     self.UpdateVideoItem method is called if the item is focussed or selected
    #     for playback.
    #
    #     """
    #
    #     Logger.Trace(resultSet)
    #
    #     title = resultSet['title']
    #     item = MediaItem(title, "", type="video")
    #     item.description = resultSet.get('text')
    #
    #     if 'image' in resultSet:
    #         item.thumb = resultSet['image'].get("full", None)
    #
    #     created = Channel.GetDateFromPosix(resultSet['created']['timestamp'])
    #     item.SetDate(created.year, created.month, created.day, created.hour, created.minute,
    #                  created.second)
    #
    #     if 'video' not in resultSet:
    #         Logger.Warning("Found item without video: %s", item)
    #         return None
    #
    #     item.AppendSingleStream(resultSet['video']['url']['default'], 0)
    #     item.complete = True
    #     return item

    def AddLiveChannel(self, data):
        Logger.Info("Performing Pre-Processing")
        # if self.channelCode != "vtm":
        #     return data, []

        username = AddonSettings.GetSetting("mediaan_username")
        if not username:
            return data, []

        items = []

        if self.channelCode == "vtm":
            item = MediaItem("Live VTM", "#livestream")
        else:
            item = MediaItem("Live Q2", "#livestream")
        item.type = "video"
        item.isLive = True
        item.fanart = self.fanart
        item.thumb = self.noImage
        items.append(item)

        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateEpisodeItemHtml(self, resultSet):
        """Creates a new MediaItem for an episode

       Arguments:
       resultSet : list[string] - the resultSet of the self.episodeItemRegex

       Returns:
       A new MediaItem of type 'folder'

       This method creates a new MediaItem from the Regular Expression or Json
       results <resultSet>. The method should be implemented by derived classes
       and are specific to the channel.

       """

        Logger.Trace(resultSet)

        title = resultSet['title']
        url = resultSet['url']
        # Try to mix the Medialaan API with HTML is not working
        # programId = resultSet['url'].split('%3A')[-1]
        # url = "http://vod.medialaan.io/api/1.0/list?" \
        #       "app_id=%s&parentSeriesOID=%s" % (self.__app, programId)

        url = HtmlEntityHelper.StripAmp(url)
        # We need to convert the URL
        # http://vtm.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&amp;f[1]=sm_field_program_active%3AAlloo%20bij%20de%20Wegpolitie
        # http://vtm.be/video/?amp%3Bf[1]=sm_field_program_active%3AAlloo%20bij%20de%20Wegpolitie&f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&f[1]=sm_field_program_active%3AAlloo%20bij%20de%20Wegpolitie

        item = MediaItem(title, url)
        item.fanart = self.fanart
        item.thumb = self.noImage
        return item

    def CreateVideoItemHtml(self, resultSet):
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

        title = resultSet['title']
        url = resultSet["url"]
        if not resultSet["url"].startswith("http"):
            url = "%s/%s" % (self.baseUrl, resultSet["url"])
        item = MediaItem(title, url, type="video")
        item.thumb = resultSet['thumburl']
        item.complete = False
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

        if not self.loggedOn:
            Logger.Warning("Cannot log on")
            return None

        data = UriHandler.Open(item.url, proxy=self.proxy)
        dataRegex = "JSON\.parse\('([\w\W]+?)'\);\W+window\.media"
        videoData = Regexer.DoRegex(dataRegex, data)[0]
        # VTM has some strange escapes
        videoData = videoData.replace("\\\"", "\"")
        videoData = videoData.replace("\\\\", "\\")
        videoData = videoData.replace("\\'", "'")
        videoJson = JsonHelper(videoData, logger=Logger.Instance())

        # duration is not calculated correctly
        duration = videoJson.GetValue("videoConfig", "duration")
        item.SetInfoLabel("Duration", duration)

        return self.__UpdateVideoItem(item, videoJson.json["vodId"])

    def UpdateLiveStream(self, item):
        Logger.Debug("Updating Live stream")
        # let's request a token
        token = self.__GetToken()

        # What is the channel name to play
        channel = self.channelCode
        if self.channelCode == "q2":
            channel = "2be"

        url = "http://stream-live.medialaan.io/stream-live/v1/channels/%s/episodes/current/video?access_token=%s&_=%s" % (
            channel,
            HtmlEntityHelper.UrlEncode(token),
            int(time.time())  # Could be a random int
        )
        data = UriHandler.Open(url, proxy=self.proxy, noCache=True)
        jsonData = JsonHelper(data)
        hls = jsonData.GetValue("response", "url", "hls")
        if not hls:
            return item

        part = item.CreateNewEmptyMediaPart()
        for s, b in M3u8.GetStreamsFromM3u8(hls, self.proxy):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)
        return item

    def __UpdateVideoItem(self, item, videoId):
        # https://user.medialaan.io/user/v1/gigya/request_token?uid=897b786c46e3462eac81549453680c0d&signature=Lfz8qNv9oeVst7I%2B8pHytr02QLU%3D&timestamp=1484682292&apikey=q2-html5-NNSMRSQSwGMDAjWKexV4e5Vm6eSPtupk&database=q2-sso&_=1484682287800
        mediaUrl = "http://vod.medialaan.io/api/1.0/item/" \
                   "%s" \
                   "/video?app_id=%s&user_network=%s" \
                   "&UID=%s" \
                   "&UIDSignature=%s" \
                   "&signatureTimestamp=%s" % (
                       videoId,
                       self.__app,
                       self.__sso,
                       self.__userId,
                       HtmlEntityHelper.UrlEncode(self.__signature),
                       self.__signatureTimeStamp
                   )

        data = UriHandler.Open(mediaUrl, proxy=self.proxy)
        jsonData = JsonHelper(data)
        m3u8Url = jsonData.GetValue("response", "uri")
        # m3u8Url = jsonData.GetValue("response", "hls-drm-uri")  # not supported by Kodi

        part = item.CreateNewEmptyMediaPart()
        # Remove the Range header to make all streams start at the beginning.
        Logger.Debug("Setting an empty 'Range' http header to force playback at the start of a stream")
        part.HttpHeaders["Range"] = ''

        for s, b in M3u8.GetStreamsFromM3u8(m3u8Url, self.proxy):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)

        # http://vod.medialaan.io/api/1.0/item/
        # vtm_20161124_VM0677613_vtmwatch
        # /video?app_id=vtm_watch&user_network=vtm-sso
        # &UID=897b786c46e3462eac81549453680c0d
        # &UIDSignature=Hf4TrZ7TFwH5cjeJ8pqVwjFp25I%3D
        # &signatureTimestamp=1481494782

        return item

    def __GetToken(self):
        """ Requests a playback token """
        if not self.loggedOn:
            self.loggedOn = self.LogOn()
        if not self.loggedOn:
            Logger.Warning("Cannot log on")
            return None

        # Q2:  https://user.medialaan.io/user/v1/gigya/request_token?uid=897b786c46e3462eac81549453680c0d&signature=SM7b5ciP09Z0gbcaCoZ%2B7r4b3uk%3D&timestamp=1484691251&apikey=q2-html5-NNSMRSQSwGMDAjWKexV4e5Vm6eSPtupk&database=q2-sso&_=1484691247493
        # VTM: https://user.medialaan.io/user/v1/gigya/request_token?uid=897b786c46e3462eac81549453680c0d&signature=Ak10FWFpuF2cSXfmGnNIBsJV4ss%3D&timestamp=1481233821&apikey=vtm-b7sJGrKwMJj0VhdZvqLDFvgkJF5NLjNY&database=vtm-sso

        url = "https://user.medialaan.io/user/v1/gigya/request_token?uid=%s&signature=%s&timestamp=%s&apikey=%s&database=%s" % (
            self.__userId,
            HtmlEntityHelper.UrlEncode(self.__signature),
            self.__signatureTimeStamp,
            HtmlEntityHelper.UrlEncode(self.__apiKey),
            self.__sso)
        data = UriHandler.Open(url, proxy=self.proxy, noCache=True)
        jsonData = JsonHelper(data)
        return jsonData.GetValue("response")

    def __ExtractSessionData(self, logonData, signatureSettings):
        logonJson = JsonHelper(logonData)
        resultCode = logonJson.GetValue("statusCode")
        Logger.Trace("Logging in returned: %s", resultCode)
        if resultCode != 200:
            Logger.Error("Error loging in: %s - %s", logonJson.GetValue("errorMessage"),
                         logonJson.GetValue("errorDetails"))
            return False

        signatureSetting = logonJson.GetValue("sessionInfo", "login_token")
        if signatureSetting:
            Logger.Info("Found 'login_token'. Saving it.")
            AddonSettings.SetSetting(signatureSettings, signatureSetting.split("|")[0])

        self.__signature = logonJson.GetValue("UIDSignature")
        self.__userId = logonJson.GetValue("UID")
        self.__signatureTimeStamp = logonJson.GetValue("signatureTimestamp")
        return True
