import datetime

import chn_class
import mediaitem
from addonsettings import AddonSettings
from helpers.htmlhelper import HtmlHelper
from regexer import Regexer
from parserdata import ParserData
from logger import Logger
from urihandler import UriHandler
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.jsonhelper import JsonHelper
from streams.m3u8 import M3u8
from streams.mpd import Mpd
from vault import Vault
from helpers.datehelper import DateHelper
from helpers.languagehelper import LanguageHelper
from textures import TextureHandler
from helpers.subtitlehelper import SubtitleHelper


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

        # first regex is a bit tighter than the second one.
        # episodeRegex = '<a[^>]+href="(?<url>/vrtnu[^"]+)"[^>]*>(?:\W*<div[^>]*>\W*)<picture[^>]*>' \
        #                '\W+(?:<[^>]+>\W*){3}<source[^>]+srcset="[^"]*(?<thumburl>//[^ ]+) \d+x"' \
        #                '[\w\W]{0,1000}?(?:<div[^>]*data-brand="(?<channel>[^"]+)">[^>]*>\s*' \
        #                '<div[^>]*>\s*(?:<div[^>]*>[^>]+>\s*)?)?' \
        #                '<h3[^>]*>(?<title>[^<]+)</h3>\s*(?:<p>)?' \
        #                '(?<description>[^<]*)(?:<br[^>]*>)?(?<descriptionMore>[^<]*)?' \
        #                '(?:</p>)?\W*</div>'
        episodeRegex = '<a[^>]+href="(?<url>/vrtnu[^"]+)"[^>]*>(?:\W*<div[^>]*>\W*)<picture[^>]*>' \
                       '\W+(?:<[^>]+>\W*){3}<source[^>]+srcset="[^"]*(?<thumburl>//[^ ]+) \d+x"' \
                       '[\w\W]{0,1000}?(?:<div[^>]*data-brand="(?<channel>[^"]+)">' \
                       '[\w\W]{0,200}?)?' \
                       '<h3[^>]*>(?<title>[^<]+)</h3>\s*(?:<p>)?' \
                       '(?<description>[^<]*)(?:<br[^>]*>)?(?<descriptionMore>[^<]*)?' \
                       '(?:</p>)?\W*</div>'
        episodeRegex = Regexer.FromExpresso(episodeRegex)
        self._AddDataParser(self.mainListUri, name="Main A-Z listing",
                            preprocessor=self.AddCategories,
                            matchType=ParserData.MatchExact,
                            parser=episodeRegex, creator=self.CreateEpisodeItem)

        self._AddDataParser("#channels", name="Main channel name listing",
                            preprocessor=self.ListChannels)

        self._AddDataParser("https://search.vrt.be/suggest?facets[categories]",
                            name="JSON Show Parser", json=True,
                            parser=(), creator=self.CreateShowItem)

        self._AddDataParser("https://services.vrt.be/videoplayer/r/live.json", json=True,
                            name="Live streams parser",
                            parser=(), creator=self.CreateLiveStream)
        self._AddDataParsers(["http://live.stream.vrt.be/", "https://live-vrt.akamaized.net"],
                             name="Live streams updater",
                             updater=self.UpdateLiveVideo)
        self._AddDataParser("https://live-[^/]+\.vrtcdn\.be",
                            matchType=ParserData.MatchRegex,
                            name="Live streams updater",
                            updater=self.UpdateLiveVideo)

        catregex = '<a[^>]+href="(?<url>/vrtnu/categorieen/(?<catid>[^"]+)/)"[^>]*>(?:\W*<div[^>]' \
                   '*>\W*){2}<picture[^>]*>\W+(?:<[^>]+>\W*){3}<source[^>]+srcset="' \
                   '(?<thumburl>[^ ]+)[\w\W]{0,2000}?<h\d[^>]+title"[^>]*>(?<title>[^<]+)'
        catregex = Regexer.FromExpresso(catregex)
        self._AddDataParser("https://www.vrt.be/vrtnu/categorieen/", name="Category parser",
                            matchType=ParserData.MatchExact,
                            parser=catregex,
                            creator=self.CreateCategory)

        folderRegex = '<li class="vrt-labelnav--item "[^>]*>\s*<h2[^<]*>\s*<a[^>]*href="' \
                      '(?<url>[^"]+)"[^>]*>(?<title>[^<]+)</a>'
        folderRegex = Regexer.FromExpresso(folderRegex)
        self._AddDataParser("*", name="Folder/Season parser",
                            parser=folderRegex, creator=self.CreateFolderItem)

        videoRegex = '<a[^>]+href="(?<url>/vrtnu/(?:[^/]+/){2}[^/]*?(?<year>\d*)/[^"]+)"[^>]*>\W*' \
                     '<div[^>]*>\W*<h[23][^>]*>\s*(?<title>[^<]+)\s*(?:<br />\s*)*</h[23]>\W*' \
                     '<p[^>]*>\W*(?:<span[^>]*class="vrtnu-list--item-meta[^>]*>\W*(?<day>\d+)/' \
                     '(?<month>\d+)[^<]*</span>\W*<span[^>]+>[^<]*</span>|)[^<]*<abbr' \
                     '[\w\W]{0,1000}?<source srcset="[^"]+(?<thumburl>//[^ ]+)'

        # No need for a subtitle for now as it only includes the textual date
        videoRegex = Regexer.FromExpresso(videoRegex)
        self._AddDataParser("*", name="Video item parser",
                            parser=videoRegex, creator=self.CreateVideoItem)

        # needs to be after the standard video item regex
        singleVideoRegex = '<script type="application/ld\+json">\W+({[\w\W]+?})\s*</script'
        # singleVideoRegex = '<picture[^>]*>\W+(?:<[^>]+>\W*){3}<source[^>]+srcset="(?<thumburl>' \
        #                    '[^ ]+)[\w\W]{0,4000}<span[^>]+id="title"[^>]*>(?<title>[^<]+)</span>' \
        #                    '\W*<span[^>]+>(?<description>[^<]+)'
        singleVideoRegex = Regexer.FromExpresso(singleVideoRegex)
        self._AddDataParser("*", name="Single video item parser",
                            parser=singleVideoRegex, creator=self.CreateSingleVideoItem)

        self._AddDataParser("*", updater=self.UpdateVideoItem, requiresLogon=True)

        # ===============================================================================================================
        # non standard items
        self.__hasAlreadyVideoItems = False
        self.__currentChannel = None

        # The key is the channel live stream key
        self.__channelData = {
            "vualto_mnm": {
                "title": "MNM",
                "metaCode": "mnm",
                "fanart": TextureHandler.Instance().GetTextureUri(self, "mnmfanart.jpg"),
                "thumb": TextureHandler.Instance().GetTextureUri(self, "mnmimage.jpg"),
                "icon": TextureHandler.Instance().GetTextureUri(self, "mnmicon.png")
            },
            "vualto_stubru": {
                "title": "Studio Brussel",
                "metaCode": "stubru",
                "fanart": TextureHandler.Instance().GetTextureUri(self, "stubrufanart.jpg"),
                "thumb": TextureHandler.Instance().GetTextureUri(self, "stubruimage.jpg"),
                "icon": TextureHandler.Instance().GetTextureUri(self, "stubruicon.png")
            },
            "vualto_een": {
                "title": "E&eacute;n",
                "metaCode": "een",
                "fanart": TextureHandler.Instance().GetTextureUri(self, "eenfanart.jpg"),
                "thumb": TextureHandler.Instance().GetTextureUri(self, "eenimage.png"),
                "icon": TextureHandler.Instance().GetTextureUri(self, "eenlarge.png"),
                "url": "https://live-vrt.akamaized.net/groupc/live/8edf3bdf-7db3-41c3-a318-72cb7f82de66/live_aes.isml/.m3u8"
            },
            "vualto_canvas": {
                "title": "Canvas",
                "metaCode": "canvas",
                "fanart": TextureHandler.Instance().GetTextureUri(self, "canvasfanart.png"),
                "thumb": TextureHandler.Instance().GetTextureUri(self, "canvasimage.png"),
                "icon": TextureHandler.Instance().GetTextureUri(self, "canvaslarge.png"),
                "url": "https://live-vrt.akamaized.net/groupc/live/14a2c0f6-3043-4850-88a5-7fb062fe7f05/live_aes.isml/.m3u8"
            },
            "vualto_ketnet": {
                "title": "KetNet",
                "metaCode": "ketnet",
                "fanart": TextureHandler.Instance().GetTextureUri(self, "ketnetfanart.jpg"),
                "thumb": TextureHandler.Instance().GetTextureUri(self, "ketnetimage.jpg"),
                "icon": TextureHandler.Instance().GetTextureUri(self, "ketnetlarge.png"),
                "url": "https://live-vrt.akamaized.net/groupc/live/f132f1b8-d04d-404e-90e0-6da1abb4f4fc/live_aes.isml/.m3u8"
            },
            "vualto_sporza": {  # not in the channel filter maps, so no metaCode
                "title": "Sporza",
                "fanart": TextureHandler.Instance().GetTextureUri(self, "sporzafanart.jpg"),
                "thumb": TextureHandler.Instance().GetTextureUri(self, "sporzaimage.jpg"),
                "icon": TextureHandler.Instance().GetTextureUri(self, "sporzalarge.png"),
                "url": "https://live-vrt.akamaized.net/groupa/live/7d5f0e4a-3429-4861-91d4-aa3229d7ad7b/live_aes.isml/.m3u8"
            },
            "ketnet-jr": {  # Not in the live channels
                "title": "KetNet Junior",
                "metaCode": "ketnet-jr",
                "fanart": TextureHandler.Instance().GetTextureUri(self, "ketnetfanart.jpg"),
                "thumb": TextureHandler.Instance().GetTextureUri(self, "ketnetimage.png"),
                "icon": TextureHandler.Instance().GetTextureUri(self, "ketnetlarge.png")
            }
        }

        # To get the tokens:
        # POST
        # Content-Type:application/json
        # https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/tokens

        # ===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def LogOn(self):
        apiKey = "3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG"

        # Do we still have a valid short living token (1 hour)? If so, we have an active session.
        shortLoginCookie = UriHandler.GetCookie("X-VRT-Token", ".vrt.be")
        if shortLoginCookie is not None:
            # The old X-VRT-Token expired after 1 year. We don't want that old cookie
            shortLoginCookieCanLiveTooLong = DateHelper.GetDateFromPosix(shortLoginCookie.expires) > datetime.datetime.now() + datetime.timedelta(hours=4)
            if not shortLoginCookieCanLiveTooLong:
                Logger.Debug("Using existing VRT.be session.")
                return True

        # Do we still have a valid long living token? If so, try to extend the session. We need the
        # original UIDSignature value for that. The 'vrtlogin-rt' and all other related cookies
        # are valid for a same period (1 year).
        longLoginCookie = UriHandler.GetCookie("vrtlogin-rt", ".vrt.be")
        if longLoginCookie is not None:
            # if we stored a valid user signature, we can use it, together with the 'gmid' and
            # 'ucid' cookies to extend the session and get new token data
            data = UriHandler.Open("https://token.vrt.be/refreshtoken", proxy=self.proxy, noCache=True)
            if "vrtnutoken" in data:
                Logger.Debug("Refreshed the VRT.be session.")
                return True

        Logger.Warning("Failed to extend the VRT.be session.")
        username = self._GetSetting("username")
        if not username:
            return None

        v = Vault()
        password = v.GetChannelSetting(self.guid, "password")
        if not password:
            Logger.Warning("Found empty password for VRT user")

        # Get a 'gmid' and 'ucid' cookie by logging in. Valid for 10 years
        Logger.Debug("Using: %s / %s", username, "*" * len(password))
        url = "https://accounts.vrt.be/accounts.login"
        data = {
            "loginID": username,
            "password": password,
            "sessionExpiration": "-1",
            "targetEnv": "jssdk",
            "include": "profile,data,emails,subscriptions,preferences,",
            "includeUserInfo": "true",
            "loginMode": "standard",
            "lang": "nl-inf",
            "APIKey": apiKey,
            "source": "showScreenSet",
            "sdk": "js_latest",
            "authMode": "cookie",
            "format": "json"
        }
        logonData = UriHandler.Open(url, data=data, proxy=self.proxy, noCache=True)
        userId, signature, signatureTimeStamp = self.__ExtractSessionData(logonData)
        if userId is None or signature is None or signatureTimeStamp is None:
            return False

        # We need to initialize the token retrieval which will redirect to the actual token
        UriHandler.Open("https://token.vrt.be/vrtnuinitlogin?provider=site&destination=https://www.vrt.be/vrtnu/",
                        proxy=self.proxy, noCache=True)

        # Now get the actual VRT tokens (X-VRT-Token....). Valid for 1 hour. So we call the actual
        # perform_login url which will redirect and get cookies.
        tokenData = {
            "UID": userId,
            "UIDSignature": signature,
            "signatureTimestamp": signatureTimeStamp,
            "client_id": "vrtnu-site",
            "submit": "submit"
        }
        UriHandler.Open("https://login.vrt.be/perform_login", proxy=self.proxy, data=tokenData, noCache=True)
        return True

    def AddCategories(self, data):
        Logger.Info("Performing Pre-Processing")
        items = []

        if self.parentItem and "code" in self.parentItem.metaData:
            self.__currentChannel = self.parentItem.metaData["code"]
            Logger.Info("Only showing items for channel: '%s'", self.__currentChannel)
            return data, items

        cat = mediaitem.MediaItem("\a.: Categori&euml;n :.", "https://www.vrt.be/vrtnu/categorieen/")
        cat.fanart = self.fanart
        cat.thumb = self.noImage
        cat.icon = self.icon
        cat.dontGroup = True
        items.append(cat)

        live = mediaitem.MediaItem("\a.: Live Streams :.", "https://services.vrt.be/videoplayer/r/live.json")
        live.fanart = self.fanart
        live.thumb = self.noImage
        live.icon = self.icon
        live.dontGroup = True
        live.isLive = True
        items.append(live)

        channelText = LanguageHelper.GetLocalizedString(30010)
        channels = mediaitem.MediaItem(".: %s :." % (channelText, ), "#channels")
        channels.fanart = self.fanart
        channels.thumb = self.noImage
        channels.icon = self.icon
        channels.dontGroup = True
        items.append(channels)

        Logger.Debug("Pre-Processing finished")
        return data, items

    def ListChannels(self, data):
        items = []

        for name, meta in self.__channelData.iteritems():
            if "metaCode" not in meta:
                continue

            channel = mediaitem.MediaItem(meta["title"], self.mainListUri)
            # noinspection PyArgumentList
            channel.fanart = meta.get("fanart", self.fanart)
            # noinspection PyArgumentList
            channel.thumb = meta.get("icon", self.icon)
            # noinspection PyArgumentList
            channel.icon = meta.get("icon", self.icon)
            channel.dontGroup = True
            channel.metaData["code"] = meta["metaCode"]
            items.append(channel)
        return data, items

    def CreateCategory(self, resultSet):
        # https://search.vrt.be/suggest?facets[categories]=met-audiodescriptie
        resultSet["url"] = "https://search.vrt.be/suggest?facets[categories]=%(catid)s" % resultSet
        item = chn_class.Channel.CreateFolderItem(self, resultSet)
        if item is not None and item.thumb and item.thumb.startswith("//"):
            item.thumb = "https:%s" % (item.thumb, )

        return item

    def CreateLiveStream(self, resultSet):
        items = []
        for keyValue, streamValue in resultSet.iteritems():
            Logger.Trace(streamValue)
            # noinspection PyArgumentList
            channelData = self.__channelData.get(keyValue, None)
            if not channelData:
                continue

            url = channelData["url"] if "url" in channelData else streamValue["hls"]
            liveItem = mediaitem.MediaItem(channelData["title"], url)
            liveItem.isLive = True
            liveItem.type = 'video'
            liveItem.fanart = channelData.get("fanart", self.fanart)
            liveItem.thumb = channelData.get("icon", self.icon)
            liveItem.icon = channelData.get("icon", self.icon)
            items.append(liveItem)
        return items

    def CreateShowItem(self, resultSet):
        Logger.Trace(resultSet)
        if resultSet["targetUrl"].startswith("//"):
            resultSet["url"] = "https:%(targetUrl)s" % resultSet
        else:
            resultSet["url"] = resultSet["targetUrl"]
        resultSet["thumburl"] = resultSet["thumbnail"]

        return chn_class.Channel.CreateEpisodeItem(self, resultSet)

    def CreateEpisodeItem(self, resultSet):
        if self.__currentChannel is not None and resultSet["channel"] != self.__currentChannel:
            Logger.Debug("Skipping items due to channel mismatch: %s", resultSet)
            return None

        item = chn_class.Channel.CreateEpisodeItem(self, resultSet)
        if item is None:
            return None

        if resultSet["descriptionMore"]:
            item.description += resultSet["descriptionMore"]

        # update artswork
        if item.thumb and item.thumb.startswith("//"):
            item.thumb = "https:%s" % (item.thumb, )
        else:
            item.thumb = self.noImage
        item.fanart = self.fanart
        return item

    def CreateFolderItem(self, resultSet):
        item = chn_class.Channel.CreateFolderItem(self, resultSet)
        if item is None:
            return None

        item.name = item.name.title()
        return item

    def CreateSingleVideoItem(self, resultSet):
        if self.__hasAlreadyVideoItems:
            # we already have items, so don't show this one, it will be a duplicate
            return None

        jsonData = JsonHelper(resultSet)
        url = self.parentItem.url
        title = jsonData.GetValue("name")
        description = HtmlHelper.ToText(jsonData.GetValue("description"))
        item = mediaitem.MediaItem(title, url, type="video")
        item.description = description
        item.thumb = self.parentItem.thumb
        item.fanart = self.parentItem.fanart
        return item

    def CreateVideoItem(self, resultSet):
        if "title" not in resultSet or resultSet["title"] is None:
            resultSet["title"] = resultSet.pop("subtitle")

        resultSet["title"] = resultSet["title"].strip()
        item = chn_class.Channel.CreateVideoItem(self, resultSet)
        if item is None:
            return None

        if "day" in resultSet and resultSet["day"] and len(resultSet.get("year", "")) == 4:
            item.SetDate(resultSet["year"] or DateHelper.this_year(), resultSet["month"], resultSet["day"])

        if item.thumb.startswith("//"):
            item.thumb = "https:%s" % (item.thumb, )

        self.__hasAlreadyVideoItems = True
        item.fanart = self.parentItem.fanart
        return item

    def UpdateLiveVideo(self, item):
        if "m3u8" not in item.url:
            Logger.Error("Cannot update live stream that is not an M3u8: %s", item.url)

        part = item.CreateNewEmptyMediaPart()
        adaptiveAvailable = AddonSettings.UseAdaptiveStreamAddOn(withEncryption=False)
        if adaptiveAvailable:
            stream = part.AppendMediaStream(item.url, 0)
            M3u8.SetInputStreamAddonInput(stream, self.proxy)
            return item

        for s, b in M3u8.GetStreamsFromM3u8(item.url, self.proxy):
            item.complete = True
            # apparently they split up M3u8 streams and audio streams, so we need to fix that here
            # this is an ugly fix, but it will work!
            if "-audio_" not in s:
                s = s.replace(".m3u8", "-audio_track=96000.m3u8")
            part.AppendMediaStream(s, b)
        return item

    def UpdateVideoItem(self, item):
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        # we need to fetch the actual url as it might differ for single video items
        data, secureUrl = UriHandler.Header(item.url, proxy=self.proxy)

        # Get the MZID
        secureUrl = secureUrl.rstrip("/")
        secureUrl = "%s.mssecurevideo.json" % (secureUrl, )
        data = UriHandler.Open(secureUrl, proxy=self.proxy, additionalHeaders=item.HttpHeaders)
        secureData = JsonHelper(data, logger=Logger.Instance())
        mzid = secureData.GetValue(secureData.json.keys()[0], "videoid")

        # region New URL retrieval with DRM protection
        # We need a player token
        tokenData = UriHandler.Open("https://media-services-public.vrt.be/"
                                    "vualto-video-aggregator-web/rest/external/v1/tokens", data="",
                                    additionalHeaders={"Content-Type": "application/json"})

        token = JsonHelper(tokenData).GetValue("vrtPlayerToken")

        assetUrl = "https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/" \
                   "external/v1/videos/{0}?vrtPlayerToken={1}&client=vrtvideo"\
            .format(HtmlEntityHelper.UrlEncode(mzid), HtmlEntityHelper.UrlEncode(token))
        assetData = UriHandler.Open(assetUrl, proxy=self.proxy, noCache=True)
        assetData = JsonHelper(assetData)

        drmKey = assetData.GetValue("drm")
        drmProtected = drmKey is not None
        adaptiveAvailable = AddonSettings.UseAdaptiveStreamAddOn(withEncryption=drmProtected)
        part = item.CreateNewEmptyMediaPart()
        srt = None
        for targetUrl in assetData.GetValue("targetUrls"):
            videoType = targetUrl["type"]
            videoUrl = targetUrl["url"]

            if videoType == "hls_aes" and drmProtected and adaptiveAvailable:
                # no difference in encrypted or not.
                Logger.Debug("Found HLS AES encrypted stream and a DRM key")
                stream = part.AppendMediaStream(videoUrl, 0)
                M3u8.SetInputStreamAddonInput(stream, self.proxy)

            elif videoType == "hls" and not drmProtected:
                # no difference in encrypted or not.
                if adaptiveAvailable:
                    Logger.Debug("Found standard HLS stream and without DRM protection")
                    stream = part.AppendMediaStream(videoUrl, 0)
                    M3u8.SetInputStreamAddonInput(stream, self.proxy)
                else:
                    m3u8Data = UriHandler.Open(videoUrl, self.proxy)
                    for s, b, a in M3u8.GetStreamsFromM3u8(videoUrl, self.proxy,
                                                           playListData=m3u8Data, mapAudio=True):
                        item.complete = True
                        if a:
                            audioPart = a.rsplit("-", 1)[-1]
                            audioPart = "-%s" % (audioPart, )
                            s = s.replace(".m3u8", audioPart)
                        part.AppendMediaStream(s, b)

                    srt = M3u8.GetSubtitle(videoUrl, playListData=m3u8Data, proxy=self.proxy)
                    if not srt:
                        continue

                    srt = srt.replace(".m3u8", ".vtt")
                    part.Subtitle = SubtitleHelper.DownloadSubtitle(srt, format="webvtt")

            elif videoType == "mpeg_dash" and adaptiveAvailable:
                if not drmProtected:
                    Logger.Debug("Found standard MPD stream and without DRM protection")
                    stream = part.AppendMediaStream(videoUrl, 1)
                    Mpd.SetInputStreamAddonInput(stream, self.proxy)
                else:
                    stream = part.AppendMediaStream(videoUrl, 1)
                    encryptionJson = '{{"token":"{0}","drm_info":[D{{SSM}}],"kid":"{{KID}}"}}'\
                        .format(drmKey)
                    encryptionKey = Mpd.GetLicenseKey(
                        keyUrl="https://widevine-proxy.drm.technology/proxy",
                        keyType="D",
                        keyValue=encryptionJson,
                        keyHeaders={"Content-Type": "text/plain;charset=UTF-8"}
                    )
                    Mpd.SetInputStreamAddonInput(stream, self.proxy, licenseKey=encryptionKey)

            if videoType.startswith("hls") and srt is None:
                srt = M3u8.GetSubtitle(videoUrl, proxy=self.proxy)
                if srt:
                    srt = srt.replace(".m3u8", ".vtt")
                    part.Subtitle = SubtitleHelper.DownloadSubtitle(srt, format="webvtt")

            item.complete = True
        # endregion
        return item

    def __ExtractSessionData(self, logonData):
        logonJson = JsonHelper(logonData)
        resultCode = logonJson.GetValue("statusCode")
        if resultCode != 200:
            Logger.Error("Error loging in: %s - %s", logonJson.GetValue("errorMessage"),
                         logonJson.GetValue("errorDetails"))
            return None, None, None

        return logonJson.GetValue("UID"), \
            logonJson.GetValue("UIDSignature"), \
            logonJson.GetValue("signatureTimestamp")
