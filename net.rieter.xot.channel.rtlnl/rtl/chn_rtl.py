import datetime

import mediaitem
import chn_class

from regexer import Regexer
from logger import Logger
from urihandler import UriHandler
from helpers.jsonhelper import JsonHelper
from streams.m3u8 import M3u8
from parserdata import ParserData
from helpers.datehelper import DateHelper


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
        self.noImage = "rtlimage.png"

        # setup the urls
        self.mainListUri = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/fun=az/fmt=smooth"
        self.baseUrl = "http://www.rtl.nl"

        # setup the main parsing data
        self.episodeItemJson = ("abstracts",)
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
                            preprocessor=self.AddLiveStreams,
                            parser=self.episodeItemJson, creator=self.CreateEpisodeItem)

        self.videoItemJson = ("material",)
        self.folderItemJson = ("seasons",)
        self._AddDataParser("*", preprocessor=self.PreProcessFolderList)
        self._AddDataParser("*", json=True,
                            parser=self.videoItemJson, creator=self.CreateVideoItem, updater=self.UpdateVideoItem)
        self._AddDataParser("*", parser=self.folderItemJson, creator=self.CreateFolderItem, json=True)

        #===============================================================================================================
        # non standard items
        self.largeIconSet = dict()

        for channel in ["rtl4", "rtl5", "rtl7", "rtl8"]:
            self.largeIconSet[channel] = self.GetImageLocation("%slarge.png" % (channel,))

        self.__IgnoreCookieLaw()

        # setup some props for later use
        self.currentJson = None
        self.abstracts = None
        self.episodes = None
        self.posterBase = None
        self.thumbBase = None

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddLiveStreams(self, data):
        """ Adds the live streams to the main listing using a preprocessor

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.

        """

        items = []

        # let's add the RTL-Z live stream
        rtlzLive = mediaitem.MediaItem("RTL Z Live Stream", "")
        rtlzLive.icon = self.icon
        rtlzLive.thumb = self.noImage
        rtlzLive.complete = True
        rtlzLive.isLive = True
        rtlzLive.dontGroup = True

        streamItem = mediaitem.MediaItem("RTL Z: Live Stream", "http://www.rtl.nl/(config=RTLXLV2,channel=rtlxl,progid=rtlz,zone=inlineplayer.rtl.nl/rtlz,ord=0)/system/video/wvx/components/financien/rtlz/miMedia/livestream/rtlz_livestream.xml/1500.wvx")
        streamItem.icon = self.icon
        streamItem.thumb = self.noImage
        streamItem.complete = True
        streamItem.type = "video"
        streamItem.dontGroup = True
        streamItem.AppendSingleStream("http://mss6.rtl7.nl/rtlzbroad", 1200)
        streamItem.AppendSingleStream("http://mss26.rtl7.nl/rtlzbroad", 1200)
        streamItem.AppendSingleStream("http://mss4.rtl7.nl/rtlzbroad", 1200)
        streamItem.AppendSingleStream("http://mss5.rtl7.nl/rtlzbroad", 1200)
        streamItem.AppendSingleStream("http://mss3.rtl7.nl/rtlzbroad", 1200)

        rtlzLive.items.append(streamItem)
        items.append(rtlzLive)

        return data, items

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

        title = resultSet["name"]
        key = resultSet["key"]
        url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/fun=getseasons/ak=%s" % (key,)
        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.fanart = self.fanart
        item.complete = True

        desc = resultSet.get("synopsis", "")
        item.description = desc

        channel = resultSet.get("station", "folder").lower()
        if channel in self.largeIconSet:
            item.icon = self.largeIconSet[channel]
            item.thumb = self.largeIconSet[channel]

        progLogo = resultSet.get("proglogo", None)
        if progLogo:
            item.thumb = "http://data.rtl.nl/service/programma_logos/%s" % (progLogo,)

        return item

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

        items = []

        # We need to keep the JSON data, in order to refer to it from the create methods.
        self.currentJson = JsonHelper(data, Logger.Instance())

        # Extract season (called abstracts) information
        self.abstracts = dict()  # : the season
        Logger.Debug("Storing abstract information")
        for abstract in self.currentJson.GetValue("abstracts"):
            self.abstracts[abstract["key"]] = abstract

        # If we have episodes available, list them
        self.episodes = dict()
        if "episodes" in self.currentJson.GetValue():
            Logger.Debug("Storing episode information")
            for episode in self.currentJson.GetValue("episodes"):
                self.episodes[episode["key"]] = episode

        # extract some meta data
        self.posterBase = self.currentJson.GetValue("meta", "poster_base_url")
        self.thumbBase = self.currentJson.GetValue("meta", "thumb_base_url")

        # And create page items
        itemsOnPage = int(self.currentJson.GetValue("meta", "nr_of_videos_onpage"))
        totalItems = int(self.currentJson.GetValue("meta", "nr_of_videos_total"))
        currentPage = self.currentJson.GetValue("meta", "pg")
        if currentPage == "all":
            currentPage = 1
        else:
            currentPage = int(currentPage)
        Logger.Debug("Found a total of %s items (%s items per page), we are on page %s", totalItems, itemsOnPage, currentPage)

        # But don't show them if not episodes were found
        if self.episodes:
            if itemsOnPage < 50:
                Logger.Debug("No more pages to show.")
            else:
                nextPage = currentPage + 1
                url = self.parentItem.url[:self.parentItem.url.rindex("=")]
                url = "%s=%s" % (url, nextPage)
                Logger.Trace(url)
                pageItem = mediaitem.MediaItem(str(nextPage), url)
                pageItem.type = "page"
                pageItem.complete = True
                items.append(pageItem)

        return data, items

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
        Logger.Trace(resultSet)

        if "/sk=" in self.parentItem.url:
            return None

        abstractKey = resultSet["abstract_key"]
        abstractData = self.abstracts.get(abstractKey, None)
        if not abstractData:
            Logger.Warning("Could not find abstract data for key: %s", abstractKey)
            return None

        Logger.Debug("Found Abstract Data: %s", abstractData)

        abstractName = abstractData.get("name", "")
        title = resultSet["name"]
        if abstractName:
            title = "%s - %s" % (abstractName, title)

        description = resultSet.get("synopsis", None)
        keyValue = resultSet["key"]
        url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/ak=%s/sk=%s/pg=1" % (abstractKey, keyValue)

        item = mediaitem.MediaItem(title.title(), url)
        item.description = description
        item.thumb = "%s/%s.png" % (self.posterBase, keyValue,)
        item.complete = True
        return item

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

        Logger.Trace(resultSet)

        episodeKey = resultSet["episode_key"]
        if episodeKey:
            episodeData = self.episodes.get(episodeKey, None)
            if not episodeData:
                Logger.Warning("Could not find episodes data for key: %s", episodeKey)
                return None
            Logger.Debug("Found Episode Data: %s", episodeData)
        else:
            Logger.Debug("No Episode Data Found")
            episodeData = None

        title = resultSet["title"]
        description = None
        if episodeData:
            if title:
                title = "%s - %s" % (episodeData["name"], title)
            else:
                title = episodeData["name"]
            description = episodeData.get("synopsis", None)

        # tarifs have datetimes
        # noinspection PyStatementEffect
        # """
        #             "ddr_timeframes": [{
        #                     "start": 1382119200,
        #                     "stop": 1382378399,
        #                     "tariff": 149
        #                 },
        #                 {
        #                     "start": 1382378400,
        #                     "tariff": 0
        #                 }],
        #
        #         """

        tariffs = resultSet.get("ddr_timeframes")
        premiumItem = False
        if tariffs:
            Logger.Trace(tariffs)
            for tariff in tariffs:
                if tariff["tariff"] > 0:
                    start = tariff.get("start", 0)
                    end = tariff.get("stop", 2147483647)
                    start = DateHelper.GetDateFromPosix(start)
                    end = DateHelper.GetDateFromPosix(end)
                    now = datetime.datetime.now()
                    if start < now < end:
                        premiumItem = True
                        Logger.Debug("Found a tariff for this episode: %s - %s: %s", start, end, tariff["tariff"])
                        break

        uuid = resultSet["uuid"]
        url = "http://www.rtl.nl/system/s4m/xldata/ux/%s?context=rtlxl&d=pc&fmt=adaptive&version=3" % (uuid,)
        # The JSON urls do not yet work
        # url = "http://www.rtl.nl/system/s4m/vfd/version=1/d=pc/output=json/fun=abstract/uuid=%s/fmt=smooth" % (uuid,)

        item = mediaitem.MediaItem(title.title(), url)
        item.type = "video"
        item.isPaid = premiumItem
        item.description = description
        item.thumb = "%s%s" % (self.posterBase, uuid,)

        station = resultSet.get("station", None)
        if station:
            icon = self.largeIconSet.get(station.lower(), None)
            if icon:
                Logger.Trace("Setting icon to: %s", icon)
                item.icon = icon

        dateTime = resultSet.get("display_date", None)
        if dateTime:
            dateTime = DateHelper.GetDateFromPosix(int(dateTime))
            item.SetDate(dateTime.year, dateTime.month, dateTime.day, dateTime.hour, dateTime.minute, dateTime.second)

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

        xmlData = UriHandler.Open(item.url, proxy=self.proxy)
        # <ref type='adaptive' device='pc' host='http://manifest.us.rtl.nl' href='/rtlxl/network/pc/adaptive/components/videorecorder/27/278629/278630/d009c025-6e8c-3d11-8aba-dc8579373134.ssm/d009c025-6e8c-3d11-8aba-dc8579373134.m3u8' />
        m3u8Urls = Regexer.DoRegex("<ref type='adaptive' device='pc' host='([^']+)' href='/([^']+)' />", xmlData)
        if not m3u8Urls:
            Logger.Warning("No m3u8 data found for: %s", item)
            return item
        m3u8Url = "%s/%s" % (m3u8Urls[0][0], m3u8Urls[0][1])

        part = item.CreateNewEmptyMediaPart()
        # prevent the "418 I'm a teapot" error
        part.HttpHeaders["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0"
        # Remove the Range header to make all streams start at the beginning.
        Logger.Debug("Setting an empty 'Range' http header to force playback at the start of a stream")
        part.HttpHeaders["Range"] = ''

        for s, b in M3u8.GetStreamsFromM3u8(m3u8Url, self.proxy):
            item.complete = True
            part.AppendMediaStream(s, b)

        return item

    def __IgnoreCookieLaw(self):
        """ Accepts the cookies from RTL channel in order to have the site available """

        Logger.Info("Setting the Cookie-Consent cookie for www.uitzendinggemist.nl")

        # the rfc2109 parameters is not valid in Python 2.4 (Xbox), so we ommit it.
        UriHandler.SetCookie(name='rtlcookieconsent', value='yes', domain='.www.rtl.nl')
        return
