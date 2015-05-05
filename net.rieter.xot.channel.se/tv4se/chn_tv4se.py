# coding:UTF-8
import string
import math
import datetime

import mediaitem
import chn_class

from parserdata import ParserData
from regexer import Regexer
from helpers import subtitlehelper
from helpers import htmlentityhelper
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
        self.noImage = "tv4image.png"

        # setup the urls
        # self.mainListUri = "http://webapi.tv4play.se/play/programs?is_active=true&platform=tablet&per_page=1000" \
        #                    "&fl=nid,name,program_image&start=0"

        self.mainListUri = "http://webapi.tv4play.se/play/programs?is_active=true&platform=tablet&per_page=1000" \
                           "&fl=nid,name,program_image,is_premium,updated_at&start=0"

        self.baseUrl = "http://www.tv4play.se"
        self.swfUrl = "http://www.tv4play.se/flash/tv4playflashlets.swf"

        self.episodeItemJson = ("results",)
        self._AddDataParser(self.mainListUri,
                            preprocessor=self.AddCategoriesAndSpecials, json=True, matchType=ParserData.MatchExact,
                            parser=self.episodeItemJson, creator=self.CreateEpisodeItem)

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
        #

        # ====================================== Actual channel setup STOPS here =======================================
        return

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

        # http://api.tv4play.se/video/tv4play/tablet/programs/search.json?livepublished=false&video_types=programs&categoryids=1.2729892&sorttype=date&start=0

        # json = JsonHelper(resultSet)
        json = resultSet
        title = json["name"]

        programId = json["nid"]
        programId = HtmlEntityHelper.UrlEncode(programId)
        url = "http://webapi.tv4play.se/play/video_assets?platform=tablet&per_page=%s&is_live=false&type=episode&" \
              "page=1&node_nids=%s&start=0" % (self.maxPageSize, programId, )

        item = mediaitem.MediaItem(title, url)
        # item.description = description
        item.icon = self.icon
        item.thumb = resultSet.get("program_image", self.noImage)
        item.isDrmProtected = resultSet.get("is_premium", False)
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

        extras = {
            # "Categories": "",
            "\a.: Mest sedda programmen just nu :.": (
                "http://webapi.tv4play.se/play/video_assets/most_viewed?type=episode&platform=tablet&is_live=false&"
                "per_page=%s&start=0" % (self.maxPageSize,),
                None
            )
        }

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
            extras[dayName] = (url, startDate)

        for name in extras:
            url, date = extras[name]
            item = mediaitem.MediaItem(name, url)
            item.dontGroup = True
            item.complete = True
            item.thumb = self.noImage

            if date is not None:
                item.SetDate(date.year, date.month, date.day, 0, 0, 0, text=date.strftime("%Y-%m-%d"))
            else:
                item.SetDate(1901, 1, 1, 0, 0, 0, text="")
            items.append(item)

        Logger.Debug("Pre-Processing finished")
        return data, items

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
        if "type=clip" not in self.parentItem.url and "&page=1&" in self.parentItem.url:
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

        # let's use the mobile streams, as they are still m3u8.
        url = "https://prima.tv4play.se/api/web/asset/%s/play?protocol=hls" % (programId,)
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
        elif freePeriod == "30+":
            freeExpired = broadcastDate + datetime.timedelta(days=99 * 365)
        else:
            freeExpired = broadcastDate + datetime.timedelta(days=int(freePeriod))
        Logger.Trace("Premium info for: %s\nPremium state: %s\nFree State:    %s\nBroadcast %s vs Expired %s",
                     name, premiumPeriod, freePeriod, broadcastDate, freeExpired)

        if now > freeExpired:
            item.name = "%s [Premium-innehåll]" % (item.name,)

        item.type = "video"
        item.complete = False
        item.icon = self.icon
        item.isGeoLocked = resultSet["is_geo_restricted"]
        item.isDrmProtected = resultSet["is_drm_protected"]
        return item

    def CreateFolderItem(self, resultSet):
        """Creates a MediaItem of type 'folder' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(strig) - the resultSet of the self.folderItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        folderResults = Regexer.DoRegex('<a href="/search\?(categoryids=\d+.\d{7}&[^"]+)"[^<]*>Visa fler', resultSet[0])
        if len(folderResults) == 0:
            return None
        else:
            queryString = folderResults[0]

        # http://www.tv4play.se/search?categoryids=1.1854778&amp;order=desc&amp;rows=8&amp;sorttype=date&amp;start=<value>

        # http://www.tv4play.se/search?partial=true&rows=5&keyword=&sorttype=date&order=desc&video_types=programs&categoryids=1.1820998&start=5
        # /search?categoryids=1.1820998&amp;keyword=&amp;order=desc&amp;rows=5&amp;sorttype=date&amp;video_types=programs

        # url = "%s/search?partial=true&rows=%s&%s" % (self.baseUrl, 200, htmlentityhelper.HtmlEntityHelper.StripAmp(resultSet[2]))
        # keyword=&sorttype=date&order=desc&video_types=programs&categoryids=%s&start=0" % (self.baseUrl, 200, resultSet[2])

        url = "%s/search?partial=true&%s&start=0&rows=%s" % (self.baseUrl, htmlentityhelper.HtmlEntityHelper.StripAmp(queryString), 200)
        name = resultSet[1]

        item = mediaitem.MediaItem(name, url)
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
        # data = UriHandler.Open(item.url, proxy=self.proxy)
        spoofIp = self._GetSetting("spoof_ip", "0.0.0.0")
        if spoofIp:
            data = UriHandler.Open(item.url, proxy=self.proxy, additionalHeaders={"X-Forwarded-For": spoofIp})
        else:
            data = UriHandler.Open(item.url, proxy=self.proxy)

        urlRegex = "<bitrate>(\d+)</bitrate>\W+<mediaFormat>([^<]+)</mediaFormat>\W+(?:<scheme>([^<]+)</scheme>\W+<server>([^<]+)</server>\W+){0,1}<base>([^<]+)</base>\W+<url>([^<]+)</url>"
        # urlRegex = "<bitrate>(\d+)</bitrate>\W+<mediaFormat>([^<]+)</mediaFormat>\W+<scheme>([^<]+)</scheme>\W+<server>([^<]+)</server>\W+<base>([^<]+)</base>\W+<url>([^<]+)</url>"

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()

        for result in Regexer.DoRegex(urlRegex, data):
            Logger.Trace(result)

            if "smi" in result[1]:
                subTitleUrl = result[5]
                part.Subtitle = subtitlehelper.SubtitleHelper.DownloadSubtitle(subTitleUrl, proxy=self.proxy)
            else:
                if "rtmp" in result[-1]:
                    Logger.Trace("RTMP Stream found")
                    bitrate = result[0]
                    # get the actual path
                    pos = string.find(result[5], '/')
                    path = result[5][pos:]

                    url = "%s%s" % (result[4], path)
                    url = self.GetVerifiableVideoUrl(url)
                    part.AppendMediaStream(url, bitrate)

                elif result[-1].endswith("master.m3u8"):
                    Logger.Trace("M3U8 Stream found")
                    for s, b in M3u8.GetStreamsFromM3u8(result[-1], self.proxy):
                        part.AppendMediaStream(s, b)

                else:
                    Logger.Trace("Other Stream found")
                    bitrate = result[0]
                    url = result[5]
                    part.AppendMediaStream(url, bitrate)

                item.complete = True

        return item
