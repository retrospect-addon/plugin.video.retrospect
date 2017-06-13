import mediaitem
import chn_class

from streams.m3u8 import M3u8
from regexer import Regexer
from helpers.jsonhelper import JsonHelper
from helpers.datehelper import DateHelper
from logger import Logger
from urihandler import UriHandler


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
        self.baseUrl = "http://www.kijk.nl"
        # Just retrieve a single page with 500 items (should be all)
        self.mainListUri = "http://api.kijk.nl/v1/default/sections/programs-abc-0123456789abcdefghijklmnopqrstuvwxyz?limit=350&offset=0"

        self.__channelId = self.channelCode
        if self.channelCode == 'veronica':
            self.noImage = "veronicaimage.png"
            self.__channelId = "veronicatv"

        elif self.channelCode == 'sbs':
            self.noImage = "sbs6image.png"
            self.__channelId = "sbs6"

        elif self.channelCode == 'sbs9':
            self.noImage = "sbs9image.png"

        elif self.channelCode == 'net5':
            self.noImage = "net5image.png"

        # setup the main parsing data
        self._AddDataParser("http://api.kijk.nl/v1/default/sections/programs-abc",
                            name="Mainlist Json", json=True,
                            preprocessor=self.AddOthers,
                            parser=("items", ), creator=self.CreateJsonEpisodeItem)

        self._AddDataParser("http://api.kijk.nl/v1/default/sections/series",
                            name="VideoItems Json", json=True,
                            parser=("items", ), creator=self.CreateJsonVideoItem)

        self._AddDataParser("http://api.kijk.nl/v2/default/sections/popular",
                            name="Popular items Json", json=True,
                            parser=("items", ), creator=self.CreateJsonPopularItem)

        self._AddDataParser("https://embed.kijk.nl/",
                            updater=self.UpdateJsonVideoItem)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:
        #  Piets Weer: no clips
        #  Achter gesloten deuren: seizoenen
        #  Wegmisbruikers: episodes and clips and both pages
        #  Utopia: no clips

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddOthers(self, data):
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

        others = mediaitem.MediaItem("\b.: Populair :.", "http://api.kijk.nl/v2/default/sections/popular_PopularVODs?offset=0")
        items.append(others)
        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateJsonEpisodeItem(self, resultSet):
        Logger.Trace(resultSet)

        channelId = resultSet["channel"]
        if channelId != self.__channelId:
            return None

        title = resultSet["title"]
        url = "http://api.kijk.nl/v1/default/sections/series-%(id)s_Episodes-season-0?limit=100&offset=0" % resultSet
        item = mediaitem.MediaItem(title, url)
        item.description = resultSet.get("synopsis", None)

        if "retina_image_pdp_header" in resultSet["images"]:
            item.fanart = resultSet["images"]["retina_image_pdp_header"]
        if "retina_image" in resultSet["images"]:
            item.thumb = resultSet["images"]["retina_image"]

        return item

    def CreateJsonPopularItem(self, resultSet):
        item = self.CreateJsonVideoItem(resultSet)
        if item is None:
            return None

        item.name = "%s - %s" % (resultSet["seriesTitle"], item.name)
        return item

    def CreateJsonVideoItem(self, resultSet):
        Logger.Trace(resultSet)

        if not resultSet["available"]:
            Logger.Warning("Item not available: %s", resultSet)
            return None

        item = self.CreateJsonEpisodeItem(resultSet)
        if item is None:
            return None

        item.type = "video"
        item.url = "https://embed.kijk.nl/api/video/%(id)s?id=kijkapp" % resultSet

        if "date" in resultSet:
            date = resultSet["date"].split("+")[0]
            # 2016-12-25T17:58:00+01:00
            timeStamp = DateHelper.GetDateFromString(date, "%Y-%m-%dT%H:%M:%S")
            item.SetDate(*timeStamp[0:6])

        return item

    def UpdateJsonVideoItem(self, item):
        data = UriHandler.Open(item.url, proxy=self.proxy)
        json = JsonHelper(data)
        m3u8Url = json.GetValue("playlist")

        if m3u8Url != "https://embed.kijk.nl/api/playlist/.m3u8":
            part = item.CreateNewEmptyMediaPart()
            for s, b in M3u8.GetStreamsFromM3u8(m3u8Url, self.proxy, appendQueryString=True):
                if "_enc_" in s:
                    Logger.Warning("Found encrypted stream. Skipping %s", s)
                    continue

                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)
            return item

        Logger.Warning("No M3u8 data found. Falling back to BrightCove")
        videoId = json.GetValue("vpakey")
        # videoId = json.GetValue("videoId") -> Not all items have a videoId
        url = "https://embed.kijk.nl/video/%s?width=868&height=491" % (videoId,)
        referer = "https://embed.kijk.nl/video/%s" % (videoId,)
        part = item.CreateNewEmptyMediaPart()

        # First try the new BrightCove JSON
        data = UriHandler.Open(url, proxy=self.proxy, referer=referer)
        brightCoveRegex = '<video[^>]+data-video-id="(?<videoId>[^"]+)[^>]+data-account="(?<videoAccount>[^"]+)'
        brightCoveData = Regexer.DoRegex(Regexer.FromExpresso(brightCoveRegex), data)
        if brightCoveData:
            Logger.Info("Found new BrightCove JSON data")
            brightCoveUrl = 'https://edge.api.brightcove.com/playback/v1/accounts/%(videoAccount)s/videos/%(videoId)s' % \
                            brightCoveData[0]
            headers = {
                "Accept": "application/json;pk=BCpkADawqM3ve1c3k3HcmzaxBvD8lXCl89K7XEHiKutxZArg2c5RhwJHJANOwPwS_4o7UsC4RhIzXG8Y69mrwKCPlRkIxNgPQVY9qG78SJ1TJop4JoDDcgdsNrg"}
            brightCoveData = UriHandler.Open(brightCoveUrl, proxy=self.proxy,
                                             additionalHeaders=headers)
            brightCoveJson = JsonHelper(brightCoveData)
            streams = filter(lambda d: d["container"] == "M2TS", brightCoveJson.GetValue("sources"))
            if streams:
                # noinspection PyTypeChecker
                streamUrl = streams[0]["src"]
                for s, b in M3u8.GetStreamsFromM3u8(streamUrl, self.proxy):
                    item.complete = True
                    part.AppendMediaStream(s, b)
                return item
