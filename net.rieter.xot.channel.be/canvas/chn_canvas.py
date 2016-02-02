# coding:Cp1252
import re
import time

import chn_class
import mediaitem

from logger import Logger
from regexer import Regexer
from addonsettings import AddonSettings
from urihandler import UriHandler
from parserdata import ParserData
from helpers.jsonhelper import JsonHelper
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

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = "canvasimage.png"

        # setup the urls
        self.mainListUri = "http://www.canvas.be/video"
        self.baseUrl = "http://www.canvas.be"
        self.swfUrl = "http://www.canvas.be/sites/all/libraries/player/PolymediaShowFX16.swf"

        # setup the main parsing data
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            preprocessor=self.AddCategories,
                            parser='<a class="header[^"]+"[^>]+href="(http://www.canvas.be/video[^"]+)">([^<]+)</a>',
                            creator=self.CreateEpisodeItem)

        # This video regex works with the default CreateVideoItem
        # videoRegex = Regexer.FromExpresso(
        #     '<a class="teaser[^>]+href="(?<url>[^"]+)"[\w\W]{0,1000}?<img[^>]+src="(?<thumburl>'
        #     '[^"]+)[^>]+>\W+</div>\W+</div>\W+</div>\W+<h3[^>]*>\W+<span[^>]*>(?<title>[^<]+)<')
        # self._AddDataParser("*", parser=videoRegex, creator=self.CreateVideoItem)

        self._AddDataParser("http://www.canvas.be/api/video/", json=True,
                            preprocessor=self.CreateVideoItemJsonFeed)

        self._AddDataParser("*", json=True,
                            preprocessor=self.ExtractJsonData,
                            parser=("data", ),
                            creator=self.CreateVideoItemJson)

        self._AddDataParser("*", updater=self.UpdateVideoItem)

        # for the json files
        self._AddDataParser(".json", json=True, matchType=ParserData.MatchEnd,
                            preprocessor=self.FixCrappyJson,
                            parser=("channel", "items"),
                            creator=self.CreateVideoItemFeeds,
                            updater=self.UpdateVideoItemFeeds)

        # ==========================================================================================
        # Test cases:
        # Documentaire: pages (has http://www.canvas.be/tag/.... url)

        # ====================================== Actual channel setup STOPS here ===================
        return

    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """

        Logger.Trace(resultSet)

        item = mediaitem.MediaItem(resultSet[1].title(), resultSet[0])
        item.icon = self.icon
        item.type = "folder"
        item.complete = True
        return item

    def ExtractJsonData(self, data):
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

        Logger.Info("Performing Pre-Processing")

        data = Regexer.DoRegex("<script>var programEpisodes = ({[^<]+})", data)[-1]
        items = []
        Logger.Debug("Pre-Processing finished")
        return data, items

    def CreateVideoItemJsonFeed(self, data):
        """ Adds the items from the recent/last chance/most viewed feeds

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.

        """

        items = []

        json = JsonHelper(data)
        videos = json.GetValue("videos")
        for video in videos:
            data = videos[video]
            Logger.Trace(data)

            title = data["title"]
            category = data.get("category", {}).get("title")
            if title != category:
                title = "%s - %s" % (category, title)
            url = data["link"]
            item = mediaitem.MediaItem(title, url)
            item.type = "video"
            item.description = data.get("description", None)

            if "image" in data:
                item.thumb = data["image"].get("url", None)

            if "date" in data:
                date = data["date"]["date"]
                timeStamp = time.strptime(date, "%Y-%m-%d %H:%M:%S.000000")
                item.SetDate(*timeStamp[0:6])

            items.append(item)

        return data, items

    def CreateVideoItemJson(self, resultSet):
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
        # there are 2 sets of data process both
        title = ""
        url = ""
        image = ""
        description = ""
        dateTime = None
        for data in (resultSet, resultSet.get("episode", None)):
            if data is None:
                continue

            title = data.get("title", title)
            url = data.get("videoUrl", url)
            description = data.get("description", description)
            image = data.get("image", image)
            dateTime = data.get("time", dateTime)

        if not url or url.endswith("-livestream"):
            Logger.Warning("Found unplayable url for '%s': '%s'", title, url)
            return None

        item = mediaitem.MediaItem(title, url)
        item.type = "video"
        item.description = description
        item.thumb = image

        if dateTime:
            # https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
            # 2015-10-20T06:10:00+00:00 -
            timeStamp = time.strptime(dateTime, "%Y-%m-%dT%H:%M:%S+00:00")
            item.SetDate(*timeStamp[0:6])
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
        videoId = Regexer.DoRegex('data-video="([^"]+)"', data)[-1]
        url = "https://mediazone.vrt.be/api/v1/canvas/assets/%s" % (videoId, )
        data = UriHandler.Open(url, proxy=self.proxy, additionalHeaders=item.HttpHeaders)
        json = JsonHelper(data)

        geoLocked = str(json.GetValue("metaInfo", "allowedRegion").lower())
        hideGeoLocked = AddonSettings.HideGeoLockedItemsForLocation(geoLocked)
        if hideGeoLocked:
            geoRegion = AddonSettings.HideGeoLockedItemsForLocation(geoLocked, True)
            Logger.Warning("Found GEO Locked item for region '%s'. Current region is '%s'",
                           geoLocked, geoRegion)
            return item

        part = item.CreateNewEmptyMediaPart()
        for video in json.GetValue("targetUrls"):
            videoType = video["type"].lower()
            url = video["url"]
            if videoType == "progressive_download":
                bitrate = 1000
            elif videoType == "hls":
                for s, b in M3u8.GetStreamsFromM3u8(url, self.proxy):
                    # s = self.GetVerifiableVideoUrl(s)
                    part.AppendMediaStream(s, b)
                continue
            elif videoType == "rtmp":
                # url=rtmp://vod.stream.vrt.be/mediazone_canvas/_definst_/mp4:2015/11/mz-ast-79a551d6-2621-4a0f-9af0-a272fb0954db-1/video_1296.mp4
                url = url.replace("_definst_/mp4:", "?slist=")
                bitrate = 1100
            else:
                Logger.Debug("Found unhandled stream type '%s':%s", videoType, url)
                continue
            part.AppendMediaStream(url, bitrate)

        item.complete = True
        return item

    def FixCrappyJson(self, data):
        """ Fixes description JSON tags

        @param data:
        @return:
        """
        items = []

        data = re.sub("<[^>]+>", (lambda m: ""), data)
        # data = data.replace("\\u0022", "'")
        Logger.Trace(data)
        return data, items

    def AddCategories(self, data):
        """ Adds live streams to the initial list to display

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        The return values should always be instantiated in at least ("", []).

        """

        items = []
        
        # let's add some specials
        #http://mp.vrt.be/api/playlist/collection_91.json
        urls = {
            "Recent": "http://www.canvas.be/api/video/1/0,999999/-date",
            "Laatste kans": "http://www.canvas.be/api/video/1/0,999999/expiring",
            "Enkel online": "http://www.canvas.be/api/video/1/0,999999/-date/vd258"
        }

        for name, url in urls.iteritems():
            name = "\aCanvas: %s" % (name,)
            item = mediaitem.MediaItem(name, url)
            item.thumb = self.noImage
            item.icon = self.icon
            item.complete = True
            item.dontGroup = True
            items.append(item)

        # item = mediaitem.MediaItem("Bevergem", "http://www.canvas.be/video/bevergem")
        # item.thumb = self.noImage
        # item.icon = self.icon
        # item.complete = True
        # items.append(item)

        return data, items
    
    def CreateVideoItemFeeds(self, resultSet):
        """Creates a MediaItem of type 'video' using the resultSet from the regex.

        Arguments:
        resultSet : tuple (string) - the resultSet of the self.videoItemRegex

        Returns:
        A new MediaItem of type 'video' or 'audio' (despite the method's name)

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.UpdateVideoItem method is called if the item is focused or selected
        for playback.

        """

        Logger.Trace(JsonHelper.DictionaryToString(resultSet["item"]))

        json = resultSet["item"]

        title = json["title"]
        description = json.get("description", json["short_description"])

        if "media_thumbnails" in json and len(json['media_thumbnails']) > 0:
            thumbUrl = json['media_thumbnails'][0]["url"]
        else:
            thumbUrl = self.noImage
        guid = json["guid"]
        url = "http://mp.vrt.be/api/playlist/details/%s.json" % (guid,)

        item = mediaitem.MediaItem(title, url)
        item.thumb = thumbUrl
        item.icon = self.icon
        item.description = description

        date = json["broadcast_date_start"]
        time = json["broadcast_time_start"]
        # noinspection PyStatementEffect
        """
                  "broadcast_date_start": "2012/06/07",
                                           0123456789
                  "broadcast_time_start": "21:30",
                                           01234
                """
        year = date[0:4]
        month = date[5:7]
        day = date[8:10]
        hour = time[0:2]
        minutes = time[3:5]
        Logger.Trace("%s-%s-%s %s:%s", year, month, day, hour, minutes)
        item.SetDate(year, month, day, hour, minutes, 0)

        item.type = 'video'
        item.complete = False
        return item
    
    def UpdateVideoItemFeeds(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL 
        and the Thumb! It should return a completed item. 
        """
        Logger.Debug('Starting UpdateVideoItem for %s', item)
        
        # rtmpt://vrt.flash.streampower.be/een//2011/07/1000_110723_getipt_neefs_wiels_Website_EEN.flv
        # http://www.een.be/sites/een.be/modules/custom/vrt_video/player/player_4.3.swf
        
        data = UriHandler.Open(item.url, proxy=self.proxy)
        json = JsonHelper(data)

        if item.MediaItemParts == 1:
            part = item.MediaItemParts[0]
        else:
            part = item.CreateNewEmptyMediaPart()

        streamItems = json.GetValue("channel", "items")
        if not streamItems:
            return item

        mediaUrlMedium = streamItems[0]["item"].get("ipad_url", "")
        mediaUrlLow = streamItems[0]["item"].get("iphone_url", "")

        if mediaUrlLow == mediaUrlMedium and "m3u8" in mediaUrlLow:
            Logger.Debug("Found M3u8 playlists for streams: %s", mediaUrlLow)

            for s, b in M3u8.GetStreamsFromM3u8(mediaUrlLow, self.proxy):
                item.complete = True
                # s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, b)
        else:
            if mediaUrlMedium != "":
                # not all have seperate bitrates, so these are estimates
                part.AppendMediaStream(self.GetVerifiableVideoUrl(mediaUrlMedium.replace("mp4:", "/mp4:")), 960)
            if mediaUrlLow != "":
                # not all have seperate bitrates, so these are estimates
                part.AppendMediaStream(self.GetVerifiableVideoUrl(mediaUrlLow.replace("mp4:", "/mp4:")), 696)
        item.complete = True
        return item
