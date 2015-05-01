# coding:Cp1252
import re

import chn_class
import mediaitem
from helpers import jsonhelper

from logger import Logger
from streams.m3u8 import M3u8
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
        self.noImage = "canvasimage.png"

        # setup the urls
        self.mainListUri = "http://www.canvas.be/video_overzicht"
        self.baseUrl = "http://www.canvas.be"
        self.swfUrl = "http://www.canvas.be/sites/all/libraries/player/PolymediaShowFX16.swf"

        # setup the main parsing data
        self.episodeItemRegex = '<option value="([^"]{15,100})">([^<]+)</option>'  # used for the ParseMainList
        self._AddDataParser(self.mainListUri, preprocessor=self.AddCategories,
                            parser=self.episodeItemRegex, creator=self.CreateEpisodeItem)

        self.videoItemRegex = '\{"item":([\w\W]{0,3000})categoryBrandId'
        self._AddDataParser("*", json=True, parser=("channel", "items"), preprocessor=self.FixCrappyJson,
                            creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        # ====================================== Actual channel setup STOPS here =======================================
        return

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
        for url in ("http://mp.vrt.be/api/playlist/most_viewed_canvas.json",
                    "http://mp.vrt.be/api/playlist/most_rated_canvas.json",
                    "http://mp.vrt.be/api/playlist/most_recent_canvas.json",
                    "http://mp.vrt.be/api/playlist/now_available_brand_canvas_recent.json"):
            if "most_viewed_canvas" in url:
                name = "Meest bekeken"
            elif "most_rated_canvas" in url:
                name = "Meest gewaardeerd"
            elif "most_recent_canvas" in url:
                name = "Meest recent"
            else:
                name = "Nieuw"
            name = "\aCanvas: %s" % (name,)
            item = mediaitem.MediaItem(name, url)
            item.thumb = self.noImage
            item.icon = self.icon
            item.complete = True
            item.dontGroup = True
            items.append(item)
        
        return data, items
    
    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item. 
        """
        
        code = resultSet[0].replace(":", "\:")
        url = "http://vrt-mp.polymedia.it/search/select/?q=brand:Canvas%20AND%20programme_code:" + code + \
              "&sort=date%20desc&rows=160&wt=xslt&tr=json.xsl"
        
        item = mediaitem.MediaItem(resultSet[1], url)
        item.icon = self.icon
        item.type = "folder"
        item.complete = True
        return item
    
    def CreateVideoItem(self, resultSet):
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

        Logger.Trace(jsonhelper.JsonHelper.DictionaryToString(resultSet["item"]))

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
    
    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL 
        and the Thumb! It should return a completed item. 
        """
        Logger.Debug('Starting UpdateVideoItem for %s', item)
        
        # rtmpt://vrt.flash.streampower.be/een//2011/07/1000_110723_getipt_neefs_wiels_Website_EEN.flv
        # http://www.een.be/sites/een.be/modules/custom/vrt_video/player/player_4.3.swf
        
        data = UriHandler.Open(item.url, proxy=self.proxy)
        json = jsonhelper.JsonHelper(data)

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