# coding=utf-8
import base64
import time
import re
import datetime
import uuid

import chn_class
from logger import Logger
from mediaitem import MediaItem
from streams.mpd import Mpd
from vault import Vault
from urihandler import UriHandler
from addonsettings import AddonSettings
from streams.m3u8 import M3u8
from regexer import Regexer
from xbmcwrapper import XbmcWrapper
from parserdata import ParserData

from helpers.jsonhelper import JsonHelper
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.datehelper import DateHelper
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

        # setup the urls
        self.__api = None
        self.__sso = None
        if self.channelCode == "vtm":
            self.noImage = "vtmbeimage.jpg"
            self.mainListUri = "https://vtm.be/feed/programs?format=json&type=all&only_with_video=true"
            # Uncomment the line below for full JSON listing, but it will contain many empty shows!
            self.mainListUri = "https://vtm.be/video?f%5B0%5D=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen"
            self.baseUrl = "https://vtm.be"
            self.__app = "vtm_watch"
            self.__sso = "vtm-sso"
            self.__apiKey = "vtm-b7sJGrKwMJj0VhdZvqLDFvgkJF5NLjNY"

            # setup the main parsing data in case of HTML
            htmlVideoRegex = '<img[^>]+class="media-object"[^>]+src="(?<thumburl>[^"]+)[^>]*>[\w\W]{0,1000}?<a[^>]+href="/(?<url>[^"]+)"[^>]*>(?<title>[^<]+)'
            htmlVideoRegex = Regexer.FromExpresso(htmlVideoRegex)
            self._AddDataParser(
                "https://vtm.be/video/?f%5B0%5D=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&",
                name="HTML Page Video Parser for VTM",
                # preprocessor=self.AddMoreRecentVideos,
                parser=htmlVideoRegex, creator=self.CreateVideoItemHtml)

            recentRegex = '<a href="/(?<url>[^"]+)"[^>]*>\W+(?:<div[^>]+>\W+)+<img[^>]+src="(?<thumburl>[^"]+)"[^>]+>\W*<span[^>]*>\W*(?<subtitle>[^<]+)[\w\W]{0,300}?(?:<div[^>]+class="item-caption-program"[^>]*>(?<title>[^<]+)</div>\W*)</div>\W*</div>\W*</div>\W*</a'
            # recentRegex = 'data-video-id="(?<url>\d+)"[^>]*>\W+<[^>]+>\W+<img[^>]*src="(?<thumburl>[^"]+)[^>]*>[\W\w]{0,1000}?class="item-caption-title"[^>]*>(?<subtitle>[^<]+)<[^>]+>\W*<[^>]+>\W*<a[^>]+>(?<title>[^<]+)'
            recentRegex = Regexer.FromExpresso(recentRegex)
            self._AddDataParser(
                "https://vtm.be/video/volledige-afleveringen/id",
                matchType=ParserData.MatchExact,
                name="Recent Items HTML Video Parser",
                parser=recentRegex,
                creator=self.CreateVideoItemHtml
            )

        elif self.channelCode == "q2":
            self.noImage = "q2beimage.jpg"
            self.mainListUri = "https://www.q2.be/feed/programs?format=json&type=all&only_with_video=true"
            # Uncomment the line below for full JSON listing, but it will contain many empty shows!
            self.mainListUri = "https://www.q2.be/video?f%5B0%5D=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen"
            self.baseUrl = "https://www.q2.be"
            self.__app = "q2"
            self.__sso = "q2-sso"
            self.__apiKey = "q2-html5-NNSMRSQSwGMDAjWKexV4e5Vm6eSPtupk"

            htmlVideoRegex = '<a[^>]+class="cta-full[^>]+href="/(?<url>[^"]+)"[^>]*>[^<]*</a>\W*<span[^>]*>[^<]*</[^>]*\W*<div[^>]*>\W*<img[^>]+src="(?<thumburl>[^"]+)[\w\W]{0,1000}?<h3[^>]*>(?<title>[^<]+)'
            htmlVideoRegex = Regexer.FromExpresso(htmlVideoRegex)
            self._AddDataParser(
                "https://www.q2.be/video/?f%5B0%5D=sm_field_video_origin_cms_longform%3AVolledige%20afleveringen&",
                name="HTML Page Video Parser for Q2",
                parser=htmlVideoRegex, creator=self.CreateVideoItemHtml)

        elif self.channelCode == "stievie":
            self.__app = "stievie"
            self.__sso = "stievie-sso"
            self.__apiKey = "stievie-web-2.8-yz4DSTPshescHUytkWwU9jDxQ28PKTGn"
            self.noImage = "stievieimage.jpg"
            self.httpHeaders["Authorization"] = "apikey=%s" % (self.__apiKey, )

            # self.mainListUri = "https://vod.medialaan.io/vod/v2/programs?offset=0&limit=0"
            self.mainListUri = "https://channels.medialaan.io/channels/v1/channels?preview=false"
            self._AddDataParser(self.mainListUri,
                                json=True,
                                preprocessor=self.StievieMenu,
                                name="JSON Channel overview",
                                parser=("response", "channels"),
                                creator=self.StievieCreateChannelItem)

            self._AddDataParser("#channel", name="Channel menu parser",
                                preprocessor=self.StievieChannelMenu)

            # main list parsing
            self._AddDataParser("https://vod.medialaan.io/vod/v2/programs?offset=0&limit=0",
                                json=True,
                                name="Main program list parsing for Stievie",
                                # preprocessor=self.AddLiveChannel,
                                creator=self.StievieCreateEpisode,
                                parser=("response", "videos"))

            self._AddDataParser("https://epg.medialaan.io/epg/v2/", json=True,
                                name="EPG Stievie parser",
                                creator=self.StievieCreateEpgItems,
                                parser=("channels", ))

            self._AddDataParser("https://vod.medialaan.io/vod/v2/programs?query=",
                                name="Stievie Search Parser", json=True,
                                creator=self.StievieCreateEpisode,
                                parser=("response", "videos"))

        else:
            raise NotImplementedError("%s not supported yet" % (self.channelCode, ))

        # generic to all channels
        htmlEpisodeRegex = '<a[^>]+href="(?<url>[^"]+im_field_program[^"]+)"[^>]+>(?<title>[^(<]+)'
        htmlEpisodeRegex = Regexer.FromExpresso(htmlEpisodeRegex)
        self._AddDataParser("sm_field_video_origin_cms_longform%3AVolledige%20afleveringen",
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

        self._AddDataParser("https://vtm.be/video/volledige-afleveringen/id/",
                            name="HTML Page Video Updater New Style (AddMoreRecentVideos)",
                            updater=self.UpdateVideoItem, requiresLogon=True)

        # setup the main parsing data in case of JSON of the V2 API
        self._AddDataParser("/feed/programs?format=json&type=all&only_with_video=true",
                            matchType=ParserData.MatchEnd,
                            name="JSON Feed Show Parser for Medialaan",
                            json=True, preprocessor=self.AddLiveChannelAndFetchAllData,
                            creator=self.CreateEpisodeItemJson, parser=("response", "items"))

        self._AddDataParser("https://vod.medialaan.io/vod/v2/videos/",
                            matchType=ParserData.MatchRegex,
                            name="JSON Video Updater for Medialaan",
                            updater=self.UpdateVideoItemJson, requiresLogon=True)

        self._AddDataParser("https://vod.medialaan.io/vod/v2/videos?", json=True,
                            preprocessor=self.AddVideoPageItemsJson,
                            parser=("response", "videos"), creator=self.CreateVideoItemJson,
                            name="JSON Video Listing for Medialaan with programOID")

        self._AddDataParser("https://vod.medialaan.io/vod/v2/videos?", json=True,
                            name="JSON Video Updater for Medialaan with programOID",
                            updater=self.UpdateVideoEpgItemJson, requiresLogon=True)

        self._AddDataParser("#livestream", name="Live Stream Updater for Q2, VTM and Stievie",
                            requiresLogon=True, updater=self.UpdateLiveStream)

        # ===============================================================================================================
        # non standard items
        self.__signature = None
        self.__signatureTimeStamp = None
        self.__userId = None
        self.__cleanRegex = re.compile("<[^>]+>")
        self.__adaptiveStreamingAvailable = \
            AddonSettings.UseAdaptiveStreamAddOn(withEncryption=True)

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
        # VTM: https://vtm.be/feed/programs?format=json&type=all&only_with_video=true
        # Q2: https://www.q2.be/feed/programs?format=json&type=all&only_with_video=true

        self.__mappings = {
            "q2": {
                "Grimm": "256511352168527", "Grounded for Life": "256575957717527",
                "Crimi Clowns": "256403636905527", "At The Festivals": "257152544383527",
                "Sleepy Hollow": "256576898469527", "Taken": "256676853145527",
                "The Nanny": "256577036328527", "Life in Pieces": "256651006814527",
                "Absurdistan": "256688131946527", "Scream Queens": "256650984248527",
                "Modern Family": "256467031756527", "Game of Thrones": "256588988771527",
                "The Big Bang Theory": "256467024031527", "Foute Vrienden": "256403630232527",
                "The Last Man on Earth": "256596883888527", "That '70s Show": "256467039034527",
                "Prison Break": "257042962946527", "The X-Files": "256676844763527",
                "APB": "257060802802527", "The Graham Norton Show": "256943055386527",
                "Superstaar": "256577029073527", "Top Gear": "256528438369527",
                "American Horror Story": "256466896013527", "New Girl": "256467032228527",
                "Tricked": "256573688559527", "Community": "256973035121527",
                "UEFA Champions League": "256584896142527", "Bones": "256404132799527",
                "Married with Children": "256576831734527", "Peking Express": "257101660737527"
            },
            "vtm": {
                "Chicago Fire": "256496104767527", "Aspe": "256382495645527",
                "De Kavijaks": "256468337539527", "Alloo bij ...": "256943106645527",
                "De Zonen van Van As": "256407562265527", "De Uitverkorenen": "257117740269527",
                "Coppers": "256685693714527", "Chicago Med": "256722572301527",
                "Altijd Prijs": "256544288119527", "De Vetste Vakantie": "256676855101527",
                "Alloo en de Liefde": "257343320135527", "EHBL": "256588155275527",
                "Familie": "256383171504527", "F-16": "257462716033527",
                "Binnenstebuiten": "256575685561527",
                "Boer zkt Vrouw - De Wereld Rond": "256402065620527",
                "Code 37": "256407560206527", "De Bunker": "256587035116527",
                "De Drone School": "256850916997527", "Connie & Clyde": "256575756117527",
                "Films": "257521255357751", "Axel Opgelicht": "256544304920527",
                "Boxing Stars": "257360331594527",
                "America's Funniest Home Videos": "256547897482527",
                "De Laatste 24 Uur": "257286190319527", "Cordon": "256407560819527",
                "Alloo in de Buitenlandse Gevangenis": "256454773025527",
                "De Wensboom": "256725880042527", "FAROEK": "256575897637527",
                "Cath\u00e9rine": "256856277380527", "De Avonturen van K3": "256595788573527",
                "Ella": "256588631982527", "De Funnie Show": "256587019478527",
                "Cycling Cup": "256778013268527", "Dubbelspel": "256920728612527",
                "Expeditie Paira Daiza": "256574614075527", "Allemaal Chris": "256936077540527",
                "Baas in Huis": "256463013040527", "De Keuken van Sofie": "256382503977527",
                "Dossier X": "257353252590527", "De Gouden Schoen": "257093076727000",
                "Brandweerman Sam": "256475467798527", "Blind Getrouwd": "256589828137527",
                "Clan": "256407588081527", "De Waarzeggers": "256431811242527",
                "Alloo bij de Lokale Politie ": "256544207094527",
                "All Saints ": "256468326509527",
                "Dynamo: Magician Impossible": "256676855209527",
                "Alloo bij de Wegpolitie": "256676855317527",
                "De Buurtpolitie": "256403648640527", "Amigo's": "256544290999527",
                "David": "256586890385527", "De Kroongetuigen": "256407561421527",
                "Alloo in de Nacht": "257124109905527", "Border Security": "256472727848527",
                "Alloo in de Psychiatrie": "256544231522527",
                "Danni Lowinski": "256404119004527", "Dansdate": "256365178468527",
                "De Disco Dans Show": "256798376480527",
                "2 Meisjes op het Strand": "256899660339527", "De 25": "256454876662527",
                "2 Sterren Restaurant": "257381262541527",
                "Belgium's Got Talent": "256462951774527", "De Kotmadam": "256403656559527",
                "BK Sumo 2016": "256577054292527", "Beat da Bompaz": "256433651880527",
                "Cr\u00e8me de la Cr\u00e8me": "256407561270527",
                "Beste Kijkers": "256407593035527", "Benidorm Bastards USA": "256472726922527",
                "Benidorm Bastards": "256575677508527", "De Kliniek": "256547901203527",
                "De Rodenburgs": "256407561643527", "Deze Is Voor Jou": "256728833164527",
                "De Parenclub": "256106233009527", "Alloo bij Jambers": "256595573889527",
                "Bones": "256404132799527", "Echte Mensen: Nieuw Leven": "257111624211527",
                "De Infiltrant": "257357594695527", "Amateurs": "256403567370527",
                "Comedy Toppers": "256403657663527"
            }
        }

        self.SetCookie()

        # ===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def SetCookie(self):
        # Cookie: pwv=1; pws=functional|analytics|content_recommendation|targeted_advertising|social_media
        domain = self.mainListUri.replace("https://", "").split("/", 1)[0]
        UriHandler.SetCookie(name="pwv", value="1", domain=domain)
        UriHandler.SetCookie(name="pws", value="functional|analytics|content_recommendation|targeted_advertising|social_media", domain=domain)

    def LogOn(self):
        signatureSettings = "mediaan_signature"
        signatureSetting = AddonSettings.GetSetting(signatureSettings)
        # apiKey = "3_HZ0FtkMW_gOyKlqQzW5_0FHRC7Nd5XpXJZcDdXY4pk5eES2ZWmejRW5egwVm4ug-"  # from VTM
        apiKey = "3_OEz9nzakKMkhPdUnz41EqSRfhJg5z9JXvS4wUORkqNf2M2c1wS81ilBgCewkot97"  # from Stievie
        if signatureSetting and "|" not in signatureSetting:
            url = "https://accounts.eu1.gigya.com/accounts.getAccountInfo"
            data = "APIKey=%s" \
                   "&sdk=js_7.4.30" \
                   "&login_token=%s" % (apiKey, signatureSetting, )
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
               "&APIKey=%s" \
               "&includeSSOToken=true" \
               "&authMode=cookie" % \
               (HtmlEntityHelper.UrlEncode(username), HtmlEntityHelper.UrlEncode(password), apiKey)

        logonData = UriHandler.Open(url, params=data, proxy=self.proxy, noCache=True)
        return self.__ExtractSessionData(logonData, signatureSettings)

    def StievieMenu(self, data):
        """ Creates the main Stievie menu """

        items = []
        if not self.__adaptiveStreamingAvailable:
            return data, items

        programs = MediaItem("\b.: Programma's :.", "https://vod.medialaan.io/vod/v2/programs?offset=0&limit=0")
        programs.dontGroup = True
        items.append(programs)

        search = MediaItem("Zoeken", "searchSite")
        search.complete = True
        search.icon = self.icon
        search.thumb = self.noImage
        search.dontGroup = True
        search.SetDate(2200, 1, 1, text="")
        items.append(search)
        return data, items

    def StievieChannelMenu(self, data):
        items = []
        live = MediaItem("Live %s" % (self.parentItem.name, ), "#livestream")
        live.isLive = True
        live.type = "video"
        live.description = self.parentItem.description
        live.metaData = self.parentItem.metaData
        live.thumb = self.parentItem.thumb
        items.append(live)

        if not self.__adaptiveStreamingAvailable:
            # Only list the channel content if DASH is supported
            return data, items

        # https://epg.medialaan.io/epg/v2/schedule?date=2017-04-25&channels%5B%5D=vtm&channels%5B%5D=2be&channels%5B%5D=vitaya&channels%5B%5D=caz&channels%5B%5D=kzoom&channels%5B%5D=kadet&channels%5B%5D=qmusic
        # https://epg.medialaan.io/epg/v2/schedule?date=2017-04-25&channels[]=vtm&channels[]=2be&channels[]=vitaya&channels[]=caz&channels[]=kzoom&channels[]=kadet&channels[]=qmusic
        # https://epg.medialaan.io/epg/v2/schedule?date=2017-05-04&channels[]=vtm&channels[]=2be&channels[]=vitaya&channels[]=caz&channels[]=kzoom&channels[]=kadet&channels[]=qmusic
        channelId = self.parentItem.metaData["channelId"]
        channels = (channelId, )
        query = "&channels%%5B%%5D=%s" % ("&channels%5B%5D=".join(channels), )

        today = datetime.datetime.now()
        days = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        for i in range(0, 7, 1):
            airDate = today - datetime.timedelta(i)
            Logger.Trace("Adding item for: %s", airDate)

            day = days[airDate.weekday()]
            if i == 0:
                day = "Vandaag"
            elif i == 1:
                day = "Gisteren"
            elif i == 2:
                day = "Eergisteren"
            title = "%04d-%02d-%02d - %s" % (airDate.year, airDate.month, airDate.day, day)
            url = "https://epg.medialaan.io/epg/v2/schedule?date=%d-%02d-%02d%s" % (airDate.year, airDate.month, airDate.day, query)

            extra = MediaItem(title, url)
            extra.complete = True
            extra.icon = self.icon
            extra.thumb = self.noImage
            extra.dontGroup = True
            extra.SetDate(airDate.year, airDate.month, airDate.day, text="")
            extra.metaData["airDate"] = airDate
            items.append(extra)

        return data, items

    def StievieCreateChannelItem(self, resultSet):
        Logger.Trace(resultSet)

        if resultSet['premium']:
            return None

        item = MediaItem(resultSet["name"], "#channel")
        item.description = resultSet.get("slogan", None)
        item.metaData["channelId"] = resultSet["id"]

        if "icons" in resultSet:
            item.thumb = resultSet["icons"]["default"]
            if not item.thumb:
                item.thumb = resultSet["icons"]["white"]
        return item

    def StievieCreateEpgItems(self, epg):
        Logger.Trace(epg)
        Logger.Debug("Processing EPG for channel %s", epg["id"])

        items = []
        summerTime = time.localtime().tm_isdst
        now = datetime.datetime.now()

        for resultSet in epg["items"]:
            # if not resultSet["parentSeriesOID"]:
            #     continue

            # Does not always work
            # videoId = resultSet["epgId"].replace("-", "_")
            # url = "https://vod.medialaan.io/vod/v2/videos/%s_Stievie_free" % (videoId, )
            videoId = resultSet["programOID"]
            url = "https://vod.medialaan.io/vod/v2/videos?episodeIds=%s&limit=10&offset=0&sort=broadcastDate&sortDirection=asc" % (videoId, )
            title = resultSet["title"]
            if resultSet["episode"] and resultSet["season"]:
                title = "%s - s%02de%02d" % (title, resultSet["season"], resultSet["episode"])

            if "startTime" in resultSet and resultSet["startTime"]:
                dateTime = resultSet["startTime"]
                dateValue = DateHelper.GetDateFromString(dateTime, dateFormat="%Y-%m-%dT%H:%M:%S.000Z")
                # Convert to Belgium posix time stamp
                dateValue2 = time.mktime(dateValue) + (1 + summerTime) * 60 * 60
                # Conver the posix to a time stamp
                startTime = DateHelper.GetDateFromPosix(dateValue2)

                title = "%02d:%02d - %s" % (startTime.hour, startTime.minute, title)

                # Check for items in their black-out period
                if "blackout" in resultSet and resultSet["blackout"]["enabled"]:
                    blackoutDuration = resultSet["blackout"]["duration"]
                    blackoutStart = startTime + datetime.timedelta(seconds=blackoutDuration)
                    if blackoutStart < now:
                        Logger.Debug("Found item in Black-out period: %s (started at %s)", title, blackoutStart)
                        continue

            # else:
            #     startTime = self.parentItem.metaData["airDate"]

            item = MediaItem(title, url)
            item.type = "video"
            item.isGeoLocked = resultSet["geoblock"]
            item.description = resultSet["shortDescription"]
            # item.SetDate(startTime.year, startTime.month, startTime.day)

            if "images" in resultSet and resultSet["images"] and "styles" in resultSet["images"][0]:
                images = resultSet["images"][0]["styles"]
                # if "1520x855" in images:
                #     item.fanart = images["1520x855"]
                if "400x225" in images:
                    item.thumb = images["400x225"]

            items.append(item)

        return items

    def StievieCreateEpisode(self, resultSet):
        Logger.Trace(resultSet)
        title = resultSet['title']
        url = "https://vod.medialaan.io/vod/v2/videos?limit=18" \
              "&apikey=%s" \
              "&sort=broadcastDate&sortDirection=desc" \
              "&programIds=%s" % (self.__apiKey, resultSet['id'],)
        item = MediaItem(title, url)
        item.fanart = self.fanart
        item.thumb = self.__FindImage(resultSet,  self.noImage)
        return item

    def SearchSite(self, url=None):  # @UnusedVariable
        """Creates an list of items by searching the site

        Returns:
        A list of MediaItems that should be displayed.

        This method is called when the URL of an item is "searchSite". The channel
        calling this should implement the search functionality. This could also include
        showing of an input keyboard and following actions.

        """

        # nieuws
        url = "https://vod.medialaan.io/vod/v2/programs?query=%s"
        return chn_class.Channel.SearchSite(self, url)

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

        url = "https://vod.medialaan.io/vod/v2/videos?limit=18" \
              "&apikey=%s" \
              "&sort=broadcastDate&sortDirection=desc" \
              "&programIds=%s" % (self.__apiKey, resultSet['parent_series_oid'],)

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
        itemsOnThisPage = len(json.GetValue("response", "videos") or [])
        totalItems = json.GetValue("response", "total")

        if totalItems > currentOffset + itemsOnThisPage:
            # add next page items
            newOffset = currentOffset + itemsOnThisPage
            seriesId = json.GetValue("request", "programIds")[0]

            url = "https://vod.medialaan.io/vod/v2/videos?limit=18" \
                  "&offset=%s" \
                  "&apikey=%s" \
                  "&sort=broadcastDate&sortDirection=desc" \
                  "&programIds=%s" % (newOffset, self.__apiKey, seriesId,)

            # url = "https://vod.medialaan.io/api/1.0/list?app_id=%s&parentSeriesOID=%s&offset=%s" % (self.__app, seriesId, newOffset)
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

        if 'episode' in resultSet:
            title = resultSet['episode']['title']
        else:
            title = resultSet['title']

        url = "https://vod.medialaan.io/vod/v2/videos/%(id)s" % resultSet
        item = MediaItem(title, url, type="video")
        item.description = resultSet.get('text')
        item.thumb = self.__FindImage(resultSet.get('episode', {}), self.parentItem.thumb)

        # broadcastDate=2018-05-31T18:39:36.840Z
        created = DateHelper.GetDateFromString(resultSet['broadcastDate'].split(".")[0], "%Y-%m-%dT%H:%M:%S")
        item.SetDate(*created[0:6])

        return item

    def UpdateVideoItemJson(self, item):
        videoId = item.url.rsplit("/", 1)[-1]
        return self.__UpdateVideoItem(item, videoId)

    def UpdateVideoEpgItemJson(self, item):
        data = UriHandler.Open(item.url, proxy=self.proxy, additionalHeaders=self.httpHeaders)
        jsonData = JsonHelper(data)
        videoId = jsonData.GetValue("response", "videos", 0, "id")
        return self.__UpdateVideoItem(item, videoId)

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

        if self.channelCode == "vtm":
            recent = MediaItem("\a.: Recent :.", "https://vtm.be/video/volledige-afleveringen/id")
            item.fanart = self.fanart
            item.thumb = self.noImage
            item.dontGroup = True
            items.append(recent)

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
        if programId in self.__mappings.get(self.channelCode, {}):
            seriesId = self.__mappings[self.channelCode][programId]
            Logger.Debug("Using JSON SeriesID '%s' for '%s' (%s)", seriesId, title, programId)
            url = "https://vod.medialaan.io/vod/v2/videos?limit=18" \
                  "&apikey=%s" \
                  "&sort=broadcastDate&sortDirection=desc" \
                  "&programIds=%s" % (self.__apiKey, seriesId, )
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
        if title:
            title = title.strip()

        if 'subtitle' in resultSet and title:
            title = "%s - %s" % (title, resultSet['subtitle'].strip())
        elif 'subtitle' in resultSet:
            title = resultSet['subtitle'].strip()

        if not title:
            Logger.Warning("Item without title found: %s", resultSet)
            return None

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
        videoIdRegex = '"vodId":"([^"]+)"'
        videoId = Regexer.DoRegex(videoIdRegex, data)[0]
        return self.__UpdateVideoItem(item, videoId)

    def UpdateLiveStream(self, item):
        Logger.Debug("Updating Live stream")
        # let's request a token
        token = self.__GetToken()

        # What is the channel name to play
        channel = self.channelCode
        if self.channelCode == "q2":
            channel = "2be"
        elif self.channelCode == "stievie":
            channel = item.metaData["channelId"]

        url = "https://stream-live.medialaan.io/stream-live/v1/channels/%s/broadcasts/current/video/?deviceId=%s" % (
            channel,
            uuid.uuid4()  # Could be a random int
        )

        auth = {"Authorization": "apikey=%s&access_token=%s" % (self.__apiKey, token)}
        if self.localIP:
            auth.update(self.localIP)

        data = UriHandler.Open(url, proxy=self.proxy, noCache=True, additionalHeaders=auth)
        jsonData = JsonHelper(data)
        hls = jsonData.GetValue("response", "url", "hls-aes-linear")
        if not hls:
            return item

        # We can do this without DRM apparently.
        if AddonSettings.UseAdaptiveStreamAddOn(withEncryption=False) or True:
            # get the cookies
            licenseServerUrl = jsonData.GetValue("response", "drm", "format", "hls-aes", "licenseServerUrl")
            UriHandler.Open(licenseServerUrl, proxy=self.proxy, noCache=True)
            domain = ".license.medialaan.io"
            channelPath = jsonData.GetValue("response", "broadcast", "channel")

            # we need to fetch the specific cookies to pass on to the Adaptive add-on
            if channelPath == "2be":
                channelPath = "q2"
            path = '/keys/{0}/aes'.format(channelPath)
            cookies = ["CloudFront-Key-Pair-Id", "CloudFront-Policy", "CloudFront-Signature"]
            licenseKey = ""
            for c in cookies:
                cookie = UriHandler.GetCookie(c, domain, path=path)
                if cookie is None:
                    Logger.Error("Missing cookie: %s", c)
                    return item

                value = cookie.value
                licenseKey = "{0}; {1}={2}".format(licenseKey, c, value)

            licenseKey = licenseKey[2:]
            licenseKey = "|Cookie={0}|R{{SSM}}|".format(HtmlEntityHelper.UrlEncode(licenseKey))
            part = item.CreateNewEmptyMediaPart()
            stream = part.AppendMediaStream(hls, 0)
            M3u8.SetInputStreamAddonInput(stream, licenseKey=licenseKey)
            item.complete = True
        else:
            Logger.Error("Cannot play live-stream without encryption support.")
        return item

    def __FindImage(self, resultSet, fallback=None):
        if "images" in resultSet and resultSet["images"]:
            firstKey = resultSet["images"].keys()[0]
            images = resultSet["images"][firstKey]
            images = images.get("16_9_Landscape", images.get("default", {}))
            if "styles" in images and "large" in images["styles"]:
                return images["styles"]["large"]
        return fallback

    def __UpdateVideoItem(self, item, videoId):
        # we need a token:
        token = self.__GetToken()

        # deviceId = AddonSettings.GetClientId()
        mediaUrl = "https://vod.medialaan.io/vod/v2/videos/" \
                   "%s" \
                   "/watch?deviceId=%s" % (
                       videoId,
                       uuid.uuid4()
                   )

        auth = "apikey=%s&access_token=%s" % (self.__apiKey, token)
        headers = {"Authorization": auth}
        data = UriHandler.Open(mediaUrl, proxy=self.proxy, additionalHeaders=headers)

        jsonData = JsonHelper(data)
        dashInfo = jsonData.GetValue("response", "dash-cenc")
        if self.__adaptiveStreamingAvailable and dashInfo:
            Logger.Debug("Using Dash streams to playback")
            dashInfo = jsonData.GetValue("response", "dash-cenc")
            licenseUrl = dashInfo["widevineLicenseServerURL"]
            streamUrl = dashInfo["url"]
            sessionId = jsonData.GetValue("request", "access_token")

            licenseHeader = {
                "merchant": "medialaan",
                "userId": self.__userId,
                "sessionId": sessionId
            }
            licenseHeader = JsonHelper.Dump(licenseHeader, False)
            licenseHeaders = "x-dt-custom-data={0}&Content-Type=application/octstream".format(base64.b64encode(licenseHeader))
            licenseKey = "{0}?specConform=true|{1}|R{{SSM}}|".format(licenseUrl, licenseHeaders or "")

            part = item.CreateNewEmptyMediaPart()
            stream = part.AppendMediaStream(streamUrl, 0)
            Mpd.SetInputStreamAddonInput(stream, self.proxy, licenseKey=licenseKey, licenseType="com.widevine.alpha")
            item.complete = True
        else:
            Logger.Debug("No Dash streams supported or no Dash streams available. Using M3u8 streams")

            m3u8Url = jsonData.GetValue("response", "hls-encrypted", "url")
            if not m3u8Url:
                m3u8Url = jsonData.GetValue("response", "uri")
                # m3u8Url = jsonData.GetValue("response", "hls-drm-uri")  # not supported by Kodi

            part = item.CreateNewEmptyMediaPart()
            # Set the Range header to a proper value to make all streams start at the beginning. Make
            # sure that a complete TS part comes in a single call otherwise we get stuttering.
            byteRange = 10 * 1024 * 1024
            Logger.Debug("Setting an 'Range' http header of bytes=0-%d to force playback at the start "
                         "of a stream and to include a full .ts part.", byteRange)
            part.HttpHeaders["Range"] = 'bytes=0-%d' % (byteRange, )

            for s, b in M3u8.GetStreamsFromM3u8(m3u8Url, self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)

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
