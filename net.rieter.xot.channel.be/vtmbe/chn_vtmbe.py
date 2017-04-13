# coding=utf-8
import time
import re
import datetime

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
            self.mainListUri = "https://vtm.be/feed/programs?format=json&type=all&only_with_video=true"
            self.mainListUri = "https://vtm.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen"
            self.baseUrl = "https://vtm.be"
            self.__app = "vtm_watch"
            self.__sso = "vtm-sso"
            self.__apiKey = "vtm-b7sJGrKwMJj0VhdZvqLDFvgkJF5NLjNY"

            # setup the main parsing data in case of HTML
            htmlVideoRegex = '<img[^>]+class="media-object"[^>]+src="(?<thumburl>[^"]+)[^>]*>[\w\W]{0,1000}?<a[^>]+href="/(?<url>[^"]+)"[^>]*>(?<title>[^<]+)'
            htmlVideoRegex = Regexer.FromExpresso(htmlVideoRegex)
            self._AddDataParser(
                "https://vtm.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&",
                name="HTML Page Video Parser for VTM",
                # preprocessor=self.AddMoreRecentVideos,
                parser=htmlVideoRegex, creator=self.CreateVideoItemHtml)

            # recentRegex = '<a[^>]+href="/(?<url>video\?aid=\d+)"[^>]*>\W*<div[^>]*>\W+<[^>]+>\W+<img[^>]*src="(?<thumburl>[^"]+)[^>]*>[\W\w]{0,500}?class="item-caption-title"[^>]*>(?<subtitle>[^<]+)<[^>]+>\W*<[^>]+>\W*<a[^>]+>(?<title>[^<]+)'
            # # recentRegex = 'data-video-id="(?<url>\d+)"[^>]*>\W+<[^>]+>\W+<img[^>]*src="(?<thumburl>[^"]+)[^>]*>[\W\w]{0,1000}?class="item-caption-title"[^>]*>(?<subtitle>[^<]+)<[^>]+>\W*<[^>]+>\W*<a[^>]+>(?<title>[^<]+)'
            # recentRegex = Regexer.FromExpresso(recentRegex)
            # self._AddDataParser(
            #     "https://vtm.be/block/responsive/medialaan_vod/vtm_watch_recent_videozone",
            #     name="Recent Items HTML Video Parser",
            #     parser=recentRegex,
            #     creator=self.CreateVideoItemHtml
            # )

        elif self.channelCode == "q2":
            self.noImage = "q2beimage.jpg"
            self.mainListUri = "https://www.q2.be/feed/programs?format=json&type=all&only_with_video=true"
            self.mainListUri = "https://www.q2.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen"
            self.baseUrl = "https://www.q2.be"
            self.__app = "q2"
            self.__sso = "q2-sso"
            self.__apiKey = "q2-html5-NNSMRSQSwGMDAjWKexV4e5Vm6eSPtupk"

            htmlVideoRegex = '<a[^>]+class="cta-full[^>]+href="/(?<url>[^"]+)"[^>]*>[^<]*</a>\W*<span[^>]*>[^<]*</[^>]*\W*<div[^>]*>\W*<img[^>]+src="(?<thumburl>[^"]+)[\w\W]{0,1000}?<h3[^>]*>(?<title>[^<]+)'
            htmlVideoRegex = Regexer.FromExpresso(htmlVideoRegex)
            self._AddDataParser(
                "https://www.q2.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&",
                name="HTML Page Video Parser for Q2",
                parser=htmlVideoRegex, creator=self.CreateVideoItemHtml)
        else:
            raise NotImplementedError("%s not supported yet" % (self.channelCode, ))

        # generic to all channels
        htmlEpisodeRegex = '<a[^>]+href="(?<url>[^"]+im_field_program[^"]+)"[^>]+>(?<title>[^(<]+)'
        htmlEpisodeRegex = Regexer.FromExpresso(htmlEpisodeRegex)
        self._AddDataParser(
            "sm_field_video_origin_cms_longform%3AVolledige%20afleveringen",
            matchType=ParserData.MatchEnd,
            name="HTML Page Show Parser",
            preprocessor=self.AddLiveChannel,
            parser=htmlEpisodeRegex,
            creator=self.CreateEpisodeItemHtml)

        self._AddDataParser(
            "https://(?:vtm.be|www.q2.be)/video/?.+=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&.+id=\d+",
            matchType=ParserData.MatchRegex,
            name="HTML Page Video Updater",
            updater=self.UpdateVideoItem, requiresLogon=True)

        self._AddDataParser(
            "https://vtm.be/video/volledige-afleveringen/id/",
            name="HTML Page Video Updater New Style (AddMoreRecentVideos)",
            updater=self.UpdateVideoItem, requiresLogon=True)

        # setup the main parsing data in case of JSON
        self._AddDataParser("/feed/programs?format=json&type=all&only_with_video=true",
                            matchType=ParserData.MatchEnd,
                            name="JSON Feed Show Parser for Medialaan",
                            json=True, preprocessor=self.AddLiveChannelAndFetchAllData,
                            creator=self.CreateEpisodeItemJson, parser=("response", "items"))

        self._AddDataParser("https://vod.medialaan.io/api/1.0/list", json=True,
                            name="JSON Video Parser for Medialaan",
                            preprocessor=self.AddVideoPageItemsJson,
                            parser=("response", "items"), creator=self.CreateVideoItemJson)

        self._AddDataParser("https://vod.medialaan.io/vod/v2/videos/",
                            matchType=ParserData.MatchRegex,
                            name="JSON Video Updater for Medialaan",
                            updater=self.UpdateVideoItemJson, requiresLogon=True)

        # self._AddDataParser("https://vtm.be/video?aid=", name="HTML Stream Updater",
        #                     requiresLogon=True, updater=self.UpdateVideoItem)

        self._AddDataParser("#livestream", name="Live Stream Updater", requiresLogon=True,
                            updater=self.UpdateLiveStream)

        # ===============================================================================================================
        # non standard items
        self.__signature = None
        self.__signatureTimeStamp = None
        self.__userId = None
        self.__cleanRegex = re.compile("<[^>]+>")

        # Mappings from the normal URL (which has all shows with actual videos and very little
        # video-less shows) to the JSON ids. Loading can be done using:
        #     import json
        #     fp = file("c:\\temp\\ff.json")
        #     data = json.load(fp)
        #     fp.close()
        #     mapping = dict()
        #     for item in data["response"]["items"]:
        #         if not item["parent_series_oid"]:
        #             continue
        #         mapping[item["title"]] = item["parent_series_oid"]
        #     print json.dumps(mapping)
        #
        # TODO: perhap we can do this dynamically?

        self.__mappings = {
            "q2": {
                "Grimm": "256511352168527", "Homeland": "256467029990527",
                "Vikings": "256528439042527", "The Big Bang Theory": "256467024031527",
                "Brooklyn Nine-Nine": "256575703668527",
                "The Graham Norton Show": "256943055386527",
                "Person of Interest": "256467035258527", "Grounded for Life": "256575957717527",
                "Valemont": " 256433841939527", "Advocaat van de Duivel": "256816070531527",
                "Quantico": "256684804053527", "__The Middle": "256577035751527",
                "Life in Pieces": "256651006814527", "My Wife & Kids": "257045563302527",
                "Dawson's Creek": "256575773017527", "Dracula": "256588092015527",
                "__Two and a Half Men": "256490829206527", "Modern Family": "256467031756527",
                "Game of Thrones": "256588988771527", "Marvel's Agent Carter": "256576832916527",
                "Jo": "256576812799527", "Hit The Floor": "256594294622527",
                "Foute Vrienden": "256403630232527", "That '70s Show": "256467039034527",
                "Covert Affairs": "256467028271527", "__Champions League": "256584896142527",
                "24: Live Another Day": "256539021922527",
                "Het Beste van X-Factor Worldwide": "256575966527527",
                "Mr. Robot": "256757142789527", "Graceland": "256528403044527",
                "The Glades": "256467029451527", "Arrested Development": "256467009408527",
                "Dads": "256586859951527", "Marvel's Agents of S.H.I.E.L.D.": "256576835198527",
                "__The Muppets": "256684804375527", "The Voice USA": "256946841840527",
                "__Top Gear": "256528438369527", "Friends With Better Lives": "256588965013527",
                "New Girl": "256467032228527", "Tricked": "256573688559527",
                "Community": "256973035121527", "Salem": "256676854495527",
                "Rude Tube": "256433822255527", "Bones": "256404132799527",
                "Rosewood": "256650982517527", "The Crazy Ones": "256467028697527",
                "Married with Children": "256576831734527", "Crisis": "256511351727527"
            },
            "vtm": {
                "Helden van Hier: Door het Vuur": "256588089798527", "Aspe": "256382495645527",
                "Alloo bij ...": "256943106645527", "De Zonen van Van As": "256407562265527",
                "Heidi": "256463008600527", "Coppers": "256685693714527",
                "Chicago Med": "256722572301527", "Altijd Prijs": "256544288119527",
                "De Vetste Vakantie": "256676855101527", "Familie": "256383171504527",
                "Binnenstebuiten": "256575685561527", "Code 37": "256407560206527",
                "De Bunker": "256587035116527", "De Drone School": "256850916997527",
                "De 25": "256454876662527", "Het Grootste Licht": "256676855233527",
                "Axel Opgelicht": "256436933413527", "Het Lichaam van Coppens": "256402076016527",
                "America's Funniest Home Videos": "256547897482527",
                "Expeditie Paira Daiza": "256574614075527", "Cordon": "256407560819527",
                "Alloo in de Buitenlandse Gevangenis": "256454773025527",
                "De Wensboom": "256725880042527", "FAROEK": "256575897637527",
                "Cathérine": "256856277380527", "De Avonturen van K3": "256595788573527",
                "Ella": "256588631982527", "De Funnie Show": "256587019478527",
                "Cycling Cup": "256778013268527", "Dubbelspel": "256920728612527",
                "Allemaal Chris": "256936077540527", "Baas in Huis": "256463013040527",
                "De Keuken van Sofie": "256575862270527",
                "Helden van Hier: In de Lucht": "256996171054527",
                "Brandweerman Sam": "256475467798527", "Blind Getrouwd": "256589828137527",
                "Clan": "256407588081527", "De Waarzeggers": "256431811242527",
                "Alloo bij de Lokale Politie ": "256544207094527",
                "Het Furchester Hotel": "256831536569527",
                "Dynamo: Magician Impossible": "256676855209527",
                "Alloo bij de Wegpolitie": "256676855317527", "De Buurtpolitie": "256403648640527",
                "Amigo's": "256544290999527", "David": "256586890385527",
                "Amateurs": "256403567370527", "__Border Security": "256472727848527",
                "Alloo in de Psychiatrie": "256544231522527", "Danni Lowinski": "256404119004527",
                "De Disco Dans Show": "256798376480527",
                "Het Geheime Leven van 5-jarigen": "256611388403527",
                "__Belgium's Got Talent": "256462951774527", "De Kotmadam": "256403656559527",
                "Gezond Verstand": "257076990290527", "Beat da Bompaz": "256433651880527",
                "BK Sumo 2016": "256577054292527", "Beste Kijkers": "256407593035527",
                "Geert Hoste": "256573544524527", "Benidorm Bastards USA": "256472726922527",
                "Benidorm Bastards": "256575677508527", "De Kliniek": "256547901203527",
                "De Rodenburgs": "256407561643527", "__Deze Is Voor Jou": "256728833164527",
                "Grote Ster, Kleine Ster": "256575950955527",
                "Alloo bij Jambers": "256595573889527", "De Kroongetuigen": "256407561421527",
                "Groeten uit": "257040505722527", "Comedy Toppers": "256403657663527",
                "Little People": "256597844370527", "Rode Neuzen Dag": "257023165962527",
                "Stadion": "256573559156527", "Spitsbroers": "256471098273527",
                "Wat Als?": "256407582304527", "Til Death": "256676850133527",
                "Pac-Man en de Spook Avonturen": "256475476997527", "The Team": "256676855137527",
                "Vlaamse Streken": "256486551290527", "VTM Telefoneert": "256168188259527",
                "Sofie in de Keuken van": "256939967974527",
                "Patrouille Linkeroever": "256676854375527",
                "So You Think You Can Dance": "256464798482527", "Odd Squad": "256710652408527",
                "Vind Mijn Familie": "256384038011527", "Nicholas": "256454884349527",
                "Little Big Shots": "256897888122527",
                "Liefde voor Sterren tegen de Muziek op": "256597815326527",
                "LouisLouise": "256598003727527", "Jonas & Van Geel": "256595778045527",
                "Project K": "256611396531527", "Hollywood in 't echt": "256594308987527",
                "Maya de Bij": "256547919980527", "Zone Stad ": "15777992529",
                "Jill": "256853912126527", "Moerkerke en de mannen": "256676855221527",
                "Met Vier in Bed": "256547903459527", "Vinger Aan De Poot": "256547852448527",
                "Mijn Pop-uprestaurant!": "256477480591527", "Pak Ace": "256729926613527",
                "Vossenstreken": "256433821163527", "The Voice Kids": "256676855365527",
                "Wittekerke": "256403641361527", "Total Loss in het Bos": "256664909485527",
                "Telefacts": "256407577960527", "Royalty": "256407571395527",
                "Lang Leve...": "256403648386527", "Valkuil": "256676854981527",
                "Moerkerke en de Vrouwen": "257108815284527", "__Lotgenoten": "256586980503527",
                "Safety First": "256402022747527", "The Voice van Vlaanderen": "256577041480527",
                "Zuidflank": "256404868560527", "Rijker dan je Denkt?": "256403651256527",
                "Special Forces": "257001201929527", "Uit de Kast": "256611410411527",
                "VTM NIEUWS": "256547855317527", "Wild van Dieren": "256084514960527",
                "Shades of Blue": "256757101999527", "Het Weer": "256547857195527",
                "Tegen de Sterren op": "256407581965527", "K3 zoekt K3": "256576815747527",
                "Turbo FAST": "256676855125527", "The Band": "256996808958527",
                "Ligt er Flan op de Mont Blanc?": "257007717785527",
                "Zijn er nog Kroketten?": "256403645293527",
                "Liefde voor Muziek": "256480753274527",
                "Tom Boonen: My Ride, My Fight, My Life": "256797352477527",
                "McLeod's Daughters": "256472731081527", "Is er Wifi in Tahiti?": "256547902518527",
                "Moordvrouw": "256496106525527", "The Amazing Spiez!": "256882084522527",
                "Wij zijn K3": "256725887906527"
            }
        }

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
        # if resultSet.get("archived", False):
        #     return None

        url = "https://vod.medialaan.io/api/1.0/list?" \
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

    def AddVideoPageItemsJson(self, data):
        items = []
        json = JsonHelper(data)
        currentOffset = json.GetValue("request", "offset") or 0
        itemsOnThisPage = len(json.GetValue("response", "items") or [])
        totalItems = json.GetValue("response", "total")

        if totalItems > currentOffset + itemsOnThisPage:
            # add next page items
            newOffset = currentOffset + itemsOnThisPage
            seriesId = json.GetValue("request", "parentSeriesOID")[0]
            url = "https://vod.medialaan.io/api/1.0/list?app_id=%s&parentSeriesOID=%s&offset=%s" % (self.__app, seriesId, newOffset)
            more = LanguageHelper.GetLocalizedString(LanguageHelper.MorePages)
            item = MediaItem(more, url)
            item.thumb = self.noImage
            item.icon = self.icon
            item.fanart = self.parentItem.fanart
            item.complete = True
            items.append(item)

        return json, items

    def CreateVideoItemJson(self, resultSet):
        Logger.Trace(resultSet)

        title = resultSet['title']
        url = "https://vod.medialaan.io/vod/v2/videos/%(id)s" % resultSet
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
        now = datetime.datetime.now()
        item.SetDate(now.year, now.month, now.day, now.hour, now.minute, now.second)
        items.append(item)

        # if self.channelCode == "vtm":
        #     recent = MediaItem("\a.: Recent :.", "https://vtm.be/block/responsive/medialaan_vod/vtm_watch_recent_videozone?offset=0&limit=100")
        #     item.fanart = self.fanart
        #     item.thumb = self.noImage
        #     item.dontGroup = True
        #     items.append(recent)

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
        if not url.startswith("http"):
            url = "%s%s" % (self.baseUrl, url)
        # Try to mix the Medialaan API with HTML is not working
        # programId = resultSet['url'].split('%3A')[-1]
        programId = title.rstrip()
        if programId in self.__mappings[self.channelCode]:
            seriesId = self.__mappings[self.channelCode][programId]
            Logger.Debug("Using JSON SeriesID '%s' for '%s' (%s)", seriesId, title, programId)
            url = "https://vod.medialaan.io/api/1.0/list?" \
                  "app_id=%s&parentSeriesOID=%s" % (self.__app, seriesId)
        else:
            url = HtmlEntityHelper.StripAmp(url)
        # We need to convert the URL
        # http://vtm.be/video/?f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&amp;f[1]=sm_field_program_active%3AAlloo%20bij%20de%20Wegpolitie
        # http://vtm.be/video/?amp%3Bf[1]=sm_field_program_active%3AAlloo%20bij%20de%20Wegpolitie&f[0]=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&f[1]=sm_field_program_active%3AAlloo%20bij%20de%20Wegpolitie

        item = MediaItem(title, url)
        item.fanart = self.fanart
        item.thumb = self.noImage
        return item

    def AddMoreRecentVideos(self, data):
        items = []

        videoId = self.parentItem.url.rsplit("%3A", 1)[-1]
        recentUrl = "https://vtm.be/block/responsive/medialaan_vod/program?offset=0&limit=10&program=%s" % (videoId, )
        recentData = UriHandler.Open(recentUrl, proxy=self.proxy)

        # https://vtm.be/video/volledige-afleveringen/id/257124125192000
        regex = '<a href="/(?<url>[^"]+)"[^>]*>\W+<img[^>]+src="(?<thumburl>[^"]+)"[\w\W]{0,1000}?' \
                '<div class="item-date">(?<day>\d+)/(?<month>\d+)/(?<year>\d+)</div>\W+<[^>]+>\W+' \
                '<div[^>]+class="item-caption-title">(?<title>[^<]+)'
        regex = Regexer.FromExpresso(regex)
        results = Regexer.DoRegex(regex, recentData)
        for result in results:
            Logger.Trace(result)
            item = self.CreateVideoItemHtml(result)
            items.append(item)

        return data, items

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
        url = resultSet["url"].replace('  ', ' ')
        if not resultSet["url"].startswith("http"):
            url = "%s/%s" % (self.baseUrl, resultSet["url"])
        item = MediaItem(title, url, type="video")
        item.thumb = resultSet['thumburl']
        item.complete = False

        if "year" in resultSet and resultSet["year"]:
            item.SetDate(resultSet["year"], resultSet["month"], resultSet["day"])
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

        url = "https://stream-live.medialaan.io/stream-live/v1/channels/%s/episodes/current/video?access_token=%s&_=%s" % (
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
        mediaUrl = "https://vod.medialaan.io/api/1.0/item/" \
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
