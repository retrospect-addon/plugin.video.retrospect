# coding:UTF-8
import chn_class
import mediaitem

from logger import Logger
from urihandler import UriHandler
from parserdata import ParserData
from helpers.jsonhelper import JsonHelper
from helpers.datehelper import DateHelper
from streams.m3u8 import M3u8


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
        self.useAtom = False  # : The atom feeds just do not give all videos
        self.noImage = "srfimage.png"

        # setup the urls
        self.mainListUri = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/tv/assetGroup/editorialPlayerAlphabetical.json"

        self.baseUrl = "http://www.srf.ch"
        # self.swfUrl = "%s/public/swf/video/svtplayer-2013.23.swf" % (self.baseUrl,)

        # setup the intial listing
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
                            parser=("AssetGroups", "Show"), creator=self.CreateEpisodeItemNew)

        # self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact, json=True,
        #                     preprocessor=self.GetLiveItems)

        self._AddDataParser("http://il.srgssr.ch/integrationlayer/1.0/ue/srf/video/play",
                            updater=self.UpdateLiveItem)

        self._AddDataParser("http://il.srgssr.ch/integrationlayer/1.0/ue/srf/assetSet/listByAssetGroup", json=True,
                            # preprocessor=self.AddCalendar,
                            parser=('AssetSets', 'AssetSet'),
                            creator=self.CreateVideoItemNew)

        # TODO: folders
        self._AddDataParser("http://www.srf.ch/player/webservice/videodetail/", updater=self.UpdateVideoItem)

        # ===============================================================================================================
        # Test cases:
        #
        # ====================================== Actual channel setup STOPS here =======================================
        return

    def GetLiveItems(self, data):
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

        Logger.Info("Fetching episode items")
        items = []

        liveItems = mediaitem.MediaItem("\a.: Live TV :.", "")
        liveItems.thumb = self.noImage
        liveItems.icon = self.icon
        items.append(liveItems)

        liveBase = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/video/play/%s.json"
        liveChannels = {"SRF 1 live": ("c4927fcf-e1a0-0001-7edd-1ef01d441651", "srf1.png"),
                        "SRF zwei live": ("c49c1d64-9f60-0001-1c36-43c288c01a10", "srf2.png"),
                        "SRF info live": ("c49c1d73-2f70-0001-138a-15e0c4ccd3d0", "srfinfo.png")}
        for liveItem in liveChannels:
            item = mediaitem.MediaItem(liveItem, liveBase % (liveChannels[liveItem][0],))
            item.thumb = self.GetImageLocation(liveChannels[liveItem][1])
            item.icon = self.icon
            item.isGeoLocked = True
            item.type = "video"
            liveItems.items.append(item)

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

        Logger.Trace(resultSet)

        url = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/assetSet/listByAssetGroup/%s.json" % (resultSet["id"],)
        item = mediaitem.MediaItem(resultSet["title"], url)
        item.description = resultSet.get("description", "")
        item.icon = self.icon
        item.httpHeaders = self.httpHeaders

        # the 0005 seems to be a quality thing: 0001, 0003, 0004, 0005
        # http://www.srf.ch/webservice/picture/videogroup/c60026b7-2ed0-0001-b4b1-1f801a6355d0/0005
        # http://www.srfcdn.ch/piccache/vis/videogroup/c6/00/c60026b7-2ed0-0001-b4b1-1f801a6355d0_0005_w_h_m.jpg
        # item.thumb = "http://www.srf.ch/webservice/picture/videogroup/%s/0005" % (resultSet["id"],)
        item.thumb = "http://www.srfcdn.ch/piccache/vis/videogroup/%s/%s/%s_0005_w_h_m.jpg" \
                     % (resultSet["id"][0:2], resultSet["id"][2:4], resultSet["id"],)

        # item.thumb = resultSet.get("thumbUrl", None)
        # item.thumb = "%s/scale/width/288" % (item.thumb, )  # apparently only the 144 return the correct HEAD info
        # item.fanart = resultSet.get("imageUrl", None)  $# the HEAD will not return a size, so Kodi can't handle it
        item.complete = True
        return item

    def CreateEpisodeItemNew(self, resultSet):
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

        url = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/assetSet/listByAssetGroup/%s.json?pageSize=100" % (resultSet["id"],)
        # url = "http://www.srf.ch/player/webservice/videoprogram/index?id=%s" % (resultSet["id"],)
        item = mediaitem.MediaItem(resultSet["title"], url)
        item.description = resultSet.get("description", "")
        item.icon = self.icon
        item.httpHeaders = self.httpHeaders
        item.thumb = self.__GetNestedValue(resultSet, "Image", "ImageRepresentations", "ImageRepresentation", 0, "url")
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

        if "fullengthSegment" in resultSet and "segment" in resultSet["fullengthSegment"]:
            videoId = resultSet["fullengthSegment"]["segment"]["id"]
            geoLocation = resultSet["fullengthSegment"]["segment"]["geolocation"]
            geoBlock = False
            if "flags" in resultSet["fullengthSegment"]["segment"]:
                geoBlock = resultSet["fullengthSegment"]["segment"]["flags"].get("geoblock", None)
            Logger.Trace("Found geoLocation/geoBlock: %s/%s", geoLocation, geoBlock)
        else:
            Logger.Warning("No video information found.")
            return None

        url = "http://www.srf.ch/player/webservice/videodetail/index?id=%s" % (videoId,)
        item = mediaitem.MediaItem(resultSet["titleFull"], url)
        item.type = "video"

        item.thumb = resultSet.get("segmentThumbUrl", None)
        # item.thumb = "%s/scale/width/288" % (item.thumb, )  # apparently only the 144 return the correct HEAD info
        # item.fanart = resultSet.get("imageUrl", None)  $# the HEAD will not return a size, so Kodi can't handle it
        item.description = resultSet.get("description", "")

        dateValue = str(resultSet["time_published"])
        dateTime = DateHelper.GetDateFromString(dateValue, "%Y-%m-%d %H:%M:%S")  # 2015-01-20 22:17:59"
        item.SetDate(*dateTime[0:6])

        item.icon = self.icon
        item.httpHeaders = self.httpHeaders
        item.complete = False
        return item

    def CreateVideoItemNew(self, resultSet):
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

        videos = self.__GetNestedValue(resultSet, "Assets", "Video")
        if not videos:
            Logger.Warning("No video information found.")
            return None

        videoInfos = filter(lambda vi: vi["fullLength"], videos)
        if len(videoInfos) > 0:
            videoInfo = videoInfos[0]
        else:
            Logger.Warning("No full length video found.")
            return None
        videoId = videoInfo["id"]

        url = "http://il.srgssr.ch/integrationlayer/1.0/ue/srf/video/play/%s.json" % (videoId,)
        item = mediaitem.MediaItem(resultSet["title"], url)
        item.type = "video"

        item.thumb = self.__GetNestedValue(videoInfo, "Image", "ImageRepresentations", "ImageRepresentation", 0, "url")
        item.description = self.__GetNestedValue(videoInfo, "AssetMetadatas", "AssetMetadata", 0, "description")

        dateValue = str(resultSet["publishedDate"])
        dateValue = dateValue[0:-6]
        dateTime = DateHelper.GetDateFromString(dateValue, "%Y-%m-%dT%H:%M:%S")  # 2015-01-20T22:17:59"
        item.SetDate(*dateTime[0:6])

        item.icon = self.icon
        item.httpHeaders = self.httpHeaders
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

        data = UriHandler.Open(item.url, proxy=self.proxy, additionalHeaders=item.HttpHeaders)
        json = JsonHelper(data)
        videoInfo = json.GetValue("content", "videoInfos")

        part = item.CreateNewEmptyMediaPart()
        if "HLSurlHD" in videoInfo:
            # HLSurlHD=http://srfvodhd-vh.akamaihd.net/i/vod/potzmusig/2015/03/potzmusig_20150307_184438_v_webcast_h264_,q10,q20,q30,q40,q50,q60,.mp4.csmil/master.m3u8
            for s, b in M3u8.GetStreamsFromM3u8(videoInfo["HLSurlHD"], self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)
        elif "HLSurl" in videoInfo:
            # HLSurl=http://srfvodhd-vh.akamaihd.net/i/vod/potzmusig/2015/03/potzmusig_20150307_184438_v_webcast_h264_,q10,q20,q30,q40,.mp4.csmil/master.m3u8
            for s, b in M3u8.GetStreamsFromM3u8(videoInfo["HLSurl"], self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)

        if "downloadLink" in videoInfo:
            # downloadLink=http://podcastsource.sf.tv/nps/podcast/10vor10/2015/03/10vor10_20150304_215030_v_podcast_h264_q10.mp4
            part.AppendMediaStream(videoInfo["downloadLink"], 1000)

        return item

    def UpdateLiveItem(self, item):
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

        data = UriHandler.Open(item.url, proxy=self.proxy, additionalHeaders=item.HttpHeaders)
        json = JsonHelper(data)
        videoPlayLists = json.GetValue("Video", "Playlists", "Playlist")

        part = item.CreateNewEmptyMediaPart()
        for playList in videoPlayLists:
            streams = playList["url"]
            Logger.Trace("Found %s streams", len(streams))
            for stream in streams:
                streamUrl = stream["text"]
                if ".m3u8" in streamUrl:
                    for s, b in M3u8.GetStreamsFromM3u8(streamUrl, self.proxy):
                        item.complete = True
                        # s = self.GetVerifiableVideoUrl(s)
                        part.AppendMediaStream(s, b)
                else:
                    Logger.Debug("Cannot use stream url: %s", streamUrl)

        # videoInfo = json.GetValue("content", "videoInfos")
        #
        # part = item.CreateNewEmptyMediaPart()
        # if "HLSurlHD" in videoInfo:
        #     # HLSurlHD=http://srfvodhd-vh.akamaihd.net/i/vod/potzmusig/2015/03/potzmusig_20150307_184438_v_webcast_h264_,q10,q20,q30,q40,q50,q60,.mp4.csmil/master.m3u8
        #     for s, b in M3u8.GetStreamsFromM3u8(videoInfo["HLSurlHD"], self.proxy):
        #         item.complete = True
        #         # s = self.GetVerifiableVideoUrl(s)
        #         part.AppendMediaStream(s, b)
        # elif "HLSurl" in videoInfo:
        #     # HLSurl=http://srfvodhd-vh.akamaihd.net/i/vod/potzmusig/2015/03/potzmusig_20150307_184438_v_webcast_h264_,q10,q20,q30,q40,.mp4.csmil/master.m3u8
        #     for s, b in M3u8.GetStreamsFromM3u8(videoInfo["HLSurl"], self.proxy):
        #         item.complete = True
        #         # s = self.GetVerifiableVideoUrl(s)
        #         part.AppendMediaStream(s, b)
        #
        # if "downloadLink" in videoInfo:
        #     # downloadLink=http://podcastsource.sf.tv/nps/podcast/10vor10/2015/03/10vor10_20150304_215030_v_podcast_h264_q10.mp4
        #     part.AppendMediaStream(videoInfo["downloadLink"], 1000)

        return item

    def __GetNestedValue(self, dic, *args, **kwargs):
        currentNode = dic
        for a in args:
            try:
                currentNode = currentNode[a]
            except:
                Logger.Debug("Value '%s' is not found in '%s'", a, currentNode)
                if "fallback" in kwargs:
                    return kwargs["fallback"]
                else:
                    return None
        return currentNode
