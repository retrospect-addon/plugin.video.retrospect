import datetime
import mediaitem
import chn_class

from logger import Logger
from helpers.datehelper import DateHelper
# from urihandler import UriHandler
# from helpers.jsonhelper import JsonHelper
from parserdata import ParserData
from streams.m3u8 import M3u8


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
        self.noImage = ""

        # setup the urls
        if self.channelCode == '538':
            self.noImage = "radio538image.png"
            self.mainListUri = "https://api.538.nl/api/v1/tags"
            self.baseUrl = "http://www.538.nl"
            self.swfUrl = "http://www.538.nl/jwplayer/player.swf"

        # setup the main parsing data
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
                            preprocessor=self.AddLiveStreams)
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
                            preprocessor=self.AddDays)

        self._AddDataParser("https://api.538.nl/api/v1/schedule/station/", json=True,
                            parser=("data",), creator=self.CreateShowItem)

        self._AddDataParser("http://scripts.538.nl/app/jsonChannelData.json", json=True,
                            preprocessor=self.AddMissingLiveStreams,
                            parser=(), creator=self.CreateLiveChannel)

        # self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
        #                     preprocessor=self.AddLiveStreams,
        #                     parser=("data",), creator=self.CreateTagItem)

        # self._AddDataParser("*", json=True,
        #                     preprocessor=self.FetchSearchData)

        # updater for live streams
        self._AddDataParsers(("^http://538-?hls.lswcdn.triple-it.nl/content.+", "^http://hls2.slamfm.nl/content.+"),
                             matchType=ParserData.MatchRegex, updater=self.UpdateLiveStream)

        self.mediaUrlRegex = '<media:content url="([^"]+)"'

        #===============================================================================================================
        # non standard items
        self.EndOfProgramsFound = True  # should be done in the pre-processor

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddDays(self, data):
        """Performs pre-process actions for data processing

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

        now = datetime.datetime.now()
        fromDate = now - datetime.timedelta(6)
        Logger.Debug("Showing dates starting from %02d%02d%02d to %02d%02d%02d", fromDate.year, fromDate.month, fromDate.day, now.year, now.month, now.day)
        current = fromDate
        while current <= now:
            url = "https://api.538.nl/api/v1/schedule/station/radio-538" \
                  "?since=%s-%s-%sT00%%3A00%%3A00%%2B01%%3A00" \
                  "&until=%s-%s-%sT23%%3A59%%3A59%%2B01%%3A00" % (current.year, current.month, current.day, current.year, current.month, current.day)
            # "&_=1483280915489%%02d%%02d%%02d"
            title = "Afleveringen van %02d-%02d-%02d" % (current.year, current.month, current.day)
            dateItem = mediaitem.MediaItem(title, url)
            dateItem.icon = self.icon
            dateItem.thumb = self.noImage
            dateItem.complete = True
            items.append(dateItem)
            current = current + datetime.timedelta(1)

        return data, items

    def AddLiveStreams(self, data):
        """Performs pre-process actions for data processing

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

        # add live stuff
        live = mediaitem.MediaItem("\bLive streams", "http://scripts.538.nl/app/jsonChannelData.json")
        live.icon = self.icon
        live.thumb = self.noImage
        live.complete = True
        items = [live]
        return data, items

    def AddMissingLiveStreams(self, data):
        """Performs pre-process actions for data processing

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

        tv538 = mediaitem.MediaItem("TV 538", "http://538hls.lswcdn.triple-it.nl/content/538tv/538tv.m3u8")
        tv538.icon = self.icon
        tv538.thumb = self.noImage
        tv538.type = "video"
        tv538.complete = False
        tv538.isLive = True
        items.append(tv538)

        # cam538 = mediaitem.MediaItem("Radio 538 - Webcam", "http://538hls.lswcdn.triple-it.nl/content/538webcam/538webcam.m3u8")
        # cam538.icon = self.icon
        # cam538.thumb = self.noImage
        # cam538.type = "video"
        # cam538.isLive = True
        # items.append(cam538)

        # radio538 = mediaitem.MediaItem("Radio 538", "http://vip-icecast.538.lw.triple-it.nl/RADIO538_MP3")
        # radio538.icon = self.icon
        # radio538.thumb = self.noImage
        # radio538.type = "audio"
        # radio538.isLive = True
        # radio538.complete = True
        # radio538.AppendSingleStream(radio538.url)
        # live.items.append(radio538)

        slam = mediaitem.MediaItem("Slam! FM Webcam", "http://538hls.lswcdn.triple-it.nl/content/slamwebcam/slamwebcam.m3u8")
        slam.icon = self.icon
        slam.thumb = self.noImage
        slam.type = "video"
        slam.isLive = True
        items.append(slam)

        slam = mediaitem.MediaItem("Slam! TV", "http://hls2.slamfm.nl/content/slamtv/slamtv.m3u8")
        slam.icon = self.icon
        slam.thumb = self.noImage
        slam.type = "video"
        slam.isLive = True
        items.append(slam)

        slamFm = mediaitem.MediaItem("Slam! FM", "http://edge2-icecast.538.lw.triple-it.nl/SLAMFM_MP3")
        slamFm.icon = self.icon
        slamFm.thumb = self.noImage
        slamFm.type = "audio"
        slamFm.isLive = True
        slamFm.AppendSingleStream(slamFm.url)
        slamFm.complete = True
        items.append(slamFm)

        return data, items

    def CreateLiveChannel(self, resultSet):
        Logger.Trace(resultSet)
        streams = {}

        if "audio" in resultSet and resultSet["audio"]["hls"]:
            streams["Radio"] = resultSet["audio"]["hls"]
        if "video" in resultSet and resultSet["video"]["hls"]:
            streams["WebCam"] = resultSet["video"]["hls"]

        items = []
        for titlePart, stream in streams.iteritems():
            item = mediaitem.MediaItem("%s - %s" % (resultSet['title'], titlePart), stream)
            item.type = 'video'
            item.isLive = True
            # streamThumb=http://538prodvinson.lswcdn.triple-it.nl/thumbnails1/<timestamp>.jpg
            # timestamp=1467788048000
            # item.thumb = resultSet["appImage"]
            # if resultSet["streamThumb"]:
            #     item.thumb = resultSet['streamThumb'].replace("<timestamp>", str(resultSet["timestamp"]))
            items.append(item)
        return items

    def CreateShowItem(self, resultSet):
        """Creates a new MediaItem for a tag

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.Trace(resultSet)

        startDate = resultSet['start']  # 2017-01-01T00:00:00+01:00
        startTimeStamp = DateHelper.GetDateFromString(startDate.split("+")[0], "%Y-%m-%dT%H:%M:%S")
        endDate = resultSet['end']
        endTimeStamp = DateHelper.GetDateFromString(endDate.split("+")[0], "%Y-%m-%dT%H:%M:%S")
        title = "%02d:%02d - %02d:%02d: %s" % (startTimeStamp.tm_hour, startTimeStamp.tm_min,
                                               endTimeStamp.tm_hour, endTimeStamp.tm_min,
                                               resultSet['title'])
        item = mediaitem.MediaItem(title, "", type="video")
        item.description = resultSet.get("description")

        item.thumb = self.noImage
        if "image" in resultSet:
            if not item.description:
                item.description = resultSet["image"].get("alt", None)
            item.thumb = "https://static.538.nl/%s" % (resultSet["image"]['src'], )

        item.icon = self.icon
        item.SetDate(*startTimeStamp[0:6])
        item.description = resultSet.get('description')
        if "playbackUrls" in resultSet and resultSet["playbackUrls"]:
            titleFormat = "%%02d:%%02d - %s" % (resultSet['title'],)
            item.complete = True
            hour = startTimeStamp.tm_hour
            for stream in resultSet["playbackUrls"]:
                if stream.startswith("//"):
                    stream = "https:%s" % (stream, )
                part = item.CreateNewEmptyMediaPart()
                part.Name = titleFormat % (hour, startTimeStamp.tm_min)
                part.AppendMediaStream(stream, 0)
                hour += 1
        else:
            Logger.Warning("Found item without streams: %s", item)
            return None
        return item

    # def CreateTagItem(self, resultSet):
    #     """Creates a new MediaItem for a tag
    #
    #     Arguments:
    #     resultSet : list[string] - the resultSet of the self.episodeItemRegex
    #
    #     Returns:
    #     A new MediaItem of type 'folder'
    #
    #     This method creates a new MediaItem from the Regular Expression or Json
    #     results <resultSet>. The method should be implemented by derived classes
    #     and are specific to the channel.
    #
    #     """
    #
    #     if not resultSet['type'] in ('HeroTag', ):
    #         return None
    #     Logger.Trace(resultSet)
    #
    #     item = mediaitem.MediaItem(resultSet['title'], "#tags.id=%s" % (resultSet['id'], ))
    #     item.icon = self.icon
    #     item.thumb = self.noImage
    #     if resultSet['meta']['image']:
    #         item.thumb = "https://static.538.nl/%s" % (resultSet['meta']['image']['src'], )
    #     item.description = resultSet['meta'].get('description')
    #     return item
    #
    # def FetchSearchData(self, data):
    #     items = []
    #     data = ""
    #
    #     # We need to do a POST to get the search data for a tag:
    #     # https://80a2048bfc45a3cad426e335b9a70490.eu-west-1.aws.found.io/538_prod_main/_search
    #     # {"query":{"bool":{"must":[{"term":{"tags.id":26}}]}},"from":0,"size":1000,"sort":{"onlineDate":"desc"}}
    #     # Authorization: Basic cmVhZG9ubHk6aDRscTJscjU0NTE2ZDdtdjU2
    #
    #     params = '{"query":{"bool":{"must":[{"term":{"tags.id": %s}}]}},' \
    #              '"from":0,"size":1000, "sort":{"onlineDate":"desc"}}' \
    #              % (self.parentItem.url.replace("#tags.id=", ""), )
    #     headers = {"Authorization": "Basic cmVhZG9ubHk6aDRscTJscjU0NTE2ZDdtdjU2"}
    #     data = UriHandler.Open("https://80a2048bfc45a3cad426e335b9a70490.eu-west-1.aws.found.io/538_prod_main/_search",
    #                            proxy=self.proxy, params=params, additionalHeaders=headers)
    #
    #     json = JsonHelper(data)
    #     hits = json.GetValue("hits", "hits", fallback=[])
    #     for hit in hits:
    #         Logger.Trace(hit['_source'])
    #     return data, items

    def UpdateLiveStream(self, item):
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

        part = item.CreateNewEmptyMediaPart()
        for s, b in M3u8.GetStreamsFromM3u8(item.url, self.proxy):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)

        item.complete = True
        return item
