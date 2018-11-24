import datetime
import time
from xml.dom.minidom import parseString

import mediaitem
import chn_class

from logger import Logger
from helpers.jsonhelper import JsonHelper
from helpers.datehelper import DateHelper
from urihandler import UriHandler
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
            self.__authenticationHeaders = {
                "Authorization": "Bearer f422ea7226fff7f2e734a746a57e004f8ba6d65b50c80ee1f2d19df70d0503e9"
            }
            self.__liveUrl = "https://content.talparad.io/spaces/uf8zxj1wm72o/entries?content_type=brand&fields.slug=radio-538&limit=1&include=3"
            self.__liveData = {}

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.AddLiveStreams)
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact, json=True,
                              preprocessor=self.AddDays)

        self._add_data_parser("https://api.538.nl/api/v1/schedule/station/", json=True,
                              parser=["data",], creator=self.CreateShowItem)

        self._add_data_parser(self.__liveUrl, json=True,
                              preprocessor=self.AddMissingLiveStreams,
                              parser=["includes", "Entry"], creator=self.CreateLiveChannel)

        # updater for live streams
        self._add_data_parsers(["https://talparadiohls-i.akamaihd.net/hls/live/",
                                "http://538hls.lswcdn.triple-it.nl/content/slamwebcam/",
                                "https://hls.slam.nl/streaming/hls/"],
                               updater=self.UpdateLiveStreamM3u8)
        self._add_data_parser("https://playerservices.streamtheworld.com/api/livestream",
                              updater=self.UpdateLiveStreamXml)

        #===============================================================================================================
        # non standard items

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


        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """
        items = []

        now = datetime.datetime.now()
        fromDate = now - datetime.timedelta(6)
        Logger.debug("Showing dates starting from %02d%02d%02d to %02d%02d%02d", fromDate.year, fromDate.month, fromDate.day, now.year, now.month, now.day)
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


        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """

        # add live stuff
        live = mediaitem.MediaItem("\bLive streams", self.__liveUrl)
        live.icon = self.icon
        live.thumb = self.noImage
        live.complete = True
        live.HttpHeaders = self.__authenticationHeaders
        items = [live]
        return data, items

    def AddMissingLiveStreams(self, data):
        """Performs pre-process actions for data processing

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """
        items = []

        # tv538 = mediaitem.MediaItem("TV 538", "http://538hls.lswcdn.triple-it.nl/content/538tv/538tv.m3u8")
        # tv538.icon = self.icon
        # tv538.thumb = self.noImage
        # tv538.type = "video"
        # tv538.complete = False
        # tv538.isLive = True
        # items.append(tv538)
        #
        # slam = mediaitem.MediaItem("Slam! FM Webcam", "http://538hls.lswcdn.triple-it.nl/content/slamwebcam/slamwebcam.m3u8")
        # slam.icon = self.icon
        # slam.thumb = self.noImage
        # slam.type = "video"
        # slam.isLive = True
        # items.append(slam)
#
        slam = mediaitem.MediaItem("Slam! TV", "https://hls.slam.nl/streaming/hls/SLAM!/playlist.m3u8")
        slam.icon = self.icon
        slam.thumb = self.noImage
        slam.type = "video"
        slam.isLive = True
        items.append(slam)

        slamFm = mediaitem.MediaItem("Slam! FM", "https://18973.live.streamtheworld.com/SLAM_AAC.aac?ttag=PLAYER%3ANOPREROLL&tdsdk=js-2.9&pname=TDSdk&pversion=2.9&banners=none")
        slamFm.icon = self.icon
        slamFm.thumb = self.noImage
        slamFm.type = "audio"
        slamFm.isLive = True
        slamFm.append_single_stream(slamFm.url)
        slamFm.complete = True
        items.append(slamFm)

        data = JsonHelper(data)
        for e in data.get_value("includes", "Entry"):
            self.__liveData[e["sys"]["id"]] = e
        for e in data.get_value("includes", "Asset"):
            self.__liveData[e["sys"]["id"]] = e
        return data, items

    def CreateLiveChannel(self, resultSet):
        itemType = resultSet["sys"]["contentType"]["sys"]["id"]
        if itemType.lower() != "station":
            return None

        Logger.trace(resultSet)
        fields = resultSet["fields"]
        # title = fields["title"]
        streamTypes = fields["streamType"]

        # We need to do some fuzzy looking-up
        thumbId = fields["backgroundGallery"][0]["sys"]["id"]
        if "file" not in self.__liveData[thumbId]["fields"]:
            thumbId = self.__liveData[thumbId]["fields"]["media"]["sys"]["id"]
        thumb = self.__liveData[thumbId]["fields"]["file"]["url"]
        if thumb.startswith("//"):
            thumb = "https:{0}".format(thumb)

        items = []
        for streamType in streamTypes:
            if streamType == "video":
                streamId = fields["videoStream"]["sys"]["id"]
                streamFields = self.__liveData[streamId]["fields"]
                url = streamFields["source"]
                title = streamFields["title"]
            else:
                streamId = fields["tritonStream"]["sys"]["id"]
                streamFields = self.__liveData[streamId]["fields"]
                streamId = streamFields["mountPoint"]
                title = streamFields["title"]
                rnd = int(time.time())
                url = "https://playerservices.streamtheworld.com/api/livestream?station={0}&" \
                      "transports=http%2Chls%2Chlsts&version=1.9&request.preventCache={1}"\
                    .format(streamId, rnd)

            item = mediaitem.MediaItem(title, url)
            item.type = 'video'
            item.isLive = True
            item.thumb = thumb
            item.metaData["streamType"] = streamType
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

        Logger.trace(resultSet)

        startDate = resultSet['start']  # 2017-01-01T00:00:00+01:00
        startTimeStamp = DateHelper.get_date_from_string(startDate.split("+")[0], "%Y-%m-%dT%H:%M:%S")
        endDate = resultSet['end']
        endTimeStamp = DateHelper.get_date_from_string(endDate.split("+")[0], "%Y-%m-%dT%H:%M:%S")
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
        item.set_date(*startTimeStamp[0:6])
        item.description = resultSet.get('description')
        if "playbackUrls" in resultSet and resultSet["playbackUrls"]:
            titleFormat = "%%02d:%%02d - %s" % (resultSet['title'],)
            item.complete = True
            hour = startTimeStamp.tm_hour
            for stream in resultSet["playbackUrls"]:
                if stream.startswith("//"):
                    stream = "https:%s" % (stream, )
                part = item.create_new_empty_media_part()
                part.Name = titleFormat % (hour, startTimeStamp.tm_min)
                part.append_media_stream(stream, 0)
                hour += 1
        elif "showUrl" in resultSet and resultSet["showUrl"]:
            titleFormat = "%%02d:%%02d - %s" % (resultSet['title'],)
            stream = resultSet["showUrl"]
            item.complete = True
            hour = startTimeStamp.tm_hour
            if stream.startswith("//"):
                stream = "https:%s" % (stream,)
            part = item.create_new_empty_media_part()
            part.Name = titleFormat % (hour, startTimeStamp.tm_min)
            part.append_media_stream(stream, 0)
            hour += 1
        else:
            Logger.warning("Found item without streams: %s", item)
            return None
        return item

    def UpdateLiveStreamXml(self, item):
        data = UriHandler.open(item.url, proxy=self.proxy)
        xml = parseString(data)
        streamXmls = xml.getElementsByTagName("mountpoint")
        Logger.debug("Found %d streams", len(streamXmls))
        part = item.create_new_empty_media_part()
        for streamXml in streamXmls:
            serverXml = streamXml.getElementsByTagName("server")[0]
            server = serverXml.getElementsByTagName("ip")[0].firstChild.nodeValue
            portNode = serverXml.getElementsByTagName("port")[0]
            port = portNode.firstChild.nodeValue
            protocol = portNode.attributes["type"].firstChild.nodeValue
            entry = streamXml.getElementsByTagName("mount")[0].firstChild.nodeValue
            bitrate = int(streamXml.getElementsByTagName("bitrate")[0].firstChild.nodeValue)

            transports = streamXml.getElementsByTagName("transport")
            for transport in transports:
                transportType = transport.firstChild.nodeValue
                if transportType == "http":
                    url = "{0}://{1}:{2}/{3}".format(protocol, server, port, entry)
                elif transportType == "hls":
                    suffix = transport.attributes["mountSuffix"].firstChild.nodeValue
                    url = "{0}://{1}:{2}/{3}{4}".format(protocol, server, port, entry, suffix)
                else:
                    Logger.debug("Ignoring transport type: %s", transportType)
                    continue

                part.append_media_stream(url, bitrate)
                item.complete = True
        return item

    def UpdateLiveStreamM3u8(self, item):
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

        part = item.create_new_empty_media_part()
        for s, b in M3u8.get_streams_from_m3u8(item.url, self.proxy):
            item.complete = True
            # s = self.get_verifiable_video_url(s)
            part.append_media_stream(s, b)

        item.complete = True
        return item
