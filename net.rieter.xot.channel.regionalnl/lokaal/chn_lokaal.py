import urlparse

import contextmenu
import mediaitem
import chn_class
from helpers.datehelper import DateHelper
from parserdata import ParserData
from logger import Logger
from helpers.jsonhelper import JsonHelper
from helpers.htmlhelper import HtmlHelper
from streams.m3u8 import M3u8


class Channel(chn_class.Channel):
    """
    THIS CHANNEL IS BASED ON THE PEPERZAKEN APPS FOR ANDROID
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
        # set context menu items
        self.contextMenuItems.append(contextmenu.ContextMenuItem("Download Item", "CtMnDownloadItem", itemTypes="video"))

        # configure login stuff
        # setup the urls
        self.channelBitrate = 850  # : the default bitrate
        self.liveUrl = None        # : the live url if present
        # self.liveSelector = ()     # : what stream keys to use

        if self.channelCode == "rtvutrecht":
            self.noImage = "rtvutrechtimage.png"
            self.mainListUri = "http://app.rtvutrecht.nl/ios-android/v520/gemist_rtvutrecht_programlist.json"
            self.baseUrl = "http://app.rtvutrecht.nl"
            # Uses NPO stream with smshield cookie
            self.liveUrl = "http://app.rtvutrecht.nl/ios-android/v520/live_rtvutrecht.json"
            self.channelBitrate = 780

        elif self.channelCode == "rtvrijnmond":
            self.noImage = "rtvrijnmondimage.png"
            self.mainListUri = "http://rijnmond.api.regiogrid.nl/apps/v520/programs.json"
            self.baseUrl = "http://rijnmond.api.regiogrid.nl"
            self.liveUrl = "http://rijnmond.api.regiogrid.nl/apps/v520/tv.json"
            self.channelBitrate = 900

        elif self.channelCode == "rtvdrenthe":
            self.noImage = "rtvdrentheimage.png"
            self.mainListUri = "http://drenthe.api.regiogrid.nl/apps/v520/programs.json"
            self.baseUrl = "http://drenthe.api.regiogrid.nl"
            self.liveUrl = "http://feeds.rtvdrenthe.nl/app/all/tv.json"
            self.channelBitrate = 1350

        elif self.channelCode == "rtvnoord":
            self.noImage = "rtvnoordimage.png"
            self.mainListUri = "http://noord.storage.regiogrid.nl/apps/v520/programs.json"
            self.baseUrl = "http://noord.storage.regiogrid.nl"
            # Uses NPO stream with smshield cookie
            self.liveUrl = "http://noord.storage.regiogrid.nl/apps/v520/tv-live-kiezer.json"
            self.channelBitrate = 1350

        elif self.channelCode == "rtvoost":
            self.noImage = "rtvoostimage.png"
            self.mainListUri = "http://mobileapp.rtvoost.nl/v520/feeds/programmas.aspx"
            self.baseUrl = "http://mobileapp.rtvoost.nl"
            # self.liveUrl = "http://mobileapp.rtvoost.nl/v500/feeds/tv.aspx"
            self.liveUrl = "http://mobileapp.rtvoost.nl/v520/feeds/tv.aspx"
            # the v500 has http://145.58.83.153:80/tv/live.stream/playlist.m3u8
            # the v520 has rtsp://145.58.83.153:554/tv/live.stream and NPO streams
            self.channelBitrate = 1350

        elif self.channelCode == "rtvnh":
            self.noImage = "rtvnhimage.png"
            # self.mainListUri = "http://www.rtvnh.nl/iphone-app/v500/programmas"
            # self.mainListUri = "http://www.rtvnh.nl/iphone-app/v520/programmas"
            self.baseUrl = "http://www.rtvnh.nl"
            self.liveUrl = "http://www.rtvnh.nl/iphone-app/v520/tvnh"
            self.channelBitrate = 1200

        elif self.channelCode == "omroepwest":
            self.noImage = "omroepwestimage.png"
            self.mainListUri = "http://west.storage.regiogrid.nl/apps/v520/programs.json"
            self.baseUrl = "http://www.omroepwest.nl"
            self.liveUrl = "http://feeds.omroepwest.nl/v520/tv.json"
            self.channelBitrate = 1500

        elif self.channelCode == "omroepgelderland":
            self.noImage = "omroepgelderlandimage.png"
            self.mainListUri = "http://web.omroepgelderland.nl/json/v400/programmas.json"
            self.baseUrl = "http://web.omroepgelderland.nl"
            self.liveUrl = "http://app.gld.nl/data/json/v500/tv_live.json"
            self.channelBitrate = 1500

        elif self.channelCode == "omroepzeeland":
            self.noImage = "omroepzeelandimage.png"
            self.mainListUri = "http://www.omroepzeeland.nl/mobile/v520/ug_programmas.json"
            self.baseUrl = "http://www.omroepzeeland.nl"
            self.liveUrl = "http://www.omroepzeeland.nl/mobile/v520/live-tv.json"
            self.channelBitrate = 1500

        elif self.channelCode == "omroepbrabant":
            self.noImage = "omroepbrabantimage.png"
            self.mainListUri = "http://feed.omroepbrabant.nl/v520/UGSeries.json"
            self.baseUrl = "http://www.omroepbrabant.nl"
            self.liveUrl = "http://feed.omroepbrabant.nl/s520/tv.json"
            self.channelBitrate = 1500

        elif self.channelCode == "omropfryslan":
            self.noImage = "omropfryslanimage.png"
            self.mainListUri = "http://www.omropfryslan.nl/feeds/v520/uitzendinggemist.php"
            self.baseUrl = "http://www.omropfryslan.nl"
            self.liveUrl = "http://www.omropfryslan.nl/feeds/v520/tv.php"
            self.channelBitrate = 1500

        else:
            raise NotImplementedError("Channelcode '%s' not implemented" % (self.channelCode, ))

        # setup the main parsing data
        self.episodeItemJson = ()
        self.videoItemJson = ("items", )

        self._AddDataParser(self.mainListUri, preprocessor=self.AddLiveItems, matchType=ParserData.MatchExact,
                            parser=self.episodeItemJson, creator=self.CreateEpisodeItem,
                            json=True)

        if self.liveUrl:
            self._AddDataParser(self.liveUrl, preprocessor=self.ProcessLiveItems)

        self._AddDataParser("*", parser=self.videoItemJson, creator=self.CreateVideoItem, updater=self.UpdateVideoItem,
                            json=True)

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:
        #   Omroep Zeeland: M3u8 playist
        #   Omroep Brabant: Same M3u8 for al streams
        #   RTV Utrecht: Multiple live channels Type #1
        #   Omrop Fryslan: Multiple live channels Type #2

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddLiveItems(self, data):
        """ Adds the Live entry to the mainlist

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
        if self.liveUrl:
            Logger.Debug("Adding live item")
            liveItem = mediaitem.MediaItem("\aLive TV", self.liveUrl)
            liveItem.icon = self.icon
            liveItem.thumb = self.noImage
            liveItem.dontGroup = True
            items.append(liveItem)

        return data, items

    def ProcessLiveItems(self, data):
        """ Processes the Live Streams items

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

        Logger.Info("Adding Live Streams")

        # we basically will check for live channels
        jsonData = JsonHelper(data, logger=Logger.Instance())
        liveStreams = jsonData.GetValue()

        Logger.Trace(liveStreams)
        if "videos" in liveStreams:
            Logger.Debug("Multiple streams found")
            liveStreams = liveStreams["videos"]
        elif not isinstance(liveStreams, (list, tuple)):
            Logger.Debug("Single streams found")
            liveStreams = (liveStreams, )
        else:
            Logger.Debug("List of stream found")

        liveStreamValue = None
        for streams in liveStreams:
            Logger.Debug("Adding live stream")
            title = streams.get('name') or "%s - Live TV" % (self.channelName, )

            liveItem = mediaitem.MediaItem(title, self.liveUrl)
            liveItem.type = 'video'
            liveItem.complete = True
            liveItem.icon = self.icon
            liveItem.thumb = self.noImage
            liveItem.isLive = True
            part = liveItem.CreateNewEmptyMediaPart()
            for stream in streams:
                Logger.Trace(stream)
                bitrate = None
                # if self.liveSelector and stream not in self.liveSelector:
                #     Logger.Warning("Skipping '%s'", stream)
                #     continue

                # used in Omrop Fryslan
                if stream == "android":
                    bitrate = 250
                    url = streams[stream]["videoLink"]
                elif stream == "iPad":
                    bitrate = 1000
                    url = streams[stream]["videoLink"]
                elif stream == "iPhone":
                    bitrate = 250
                    url = streams[stream]["videoLink"]

                # used in RTV Utrecht
                elif stream == "androidLink":
                    bitrate = 250
                    url = streams[stream]
                elif stream == "ipadLink":
                    bitrate = 1000
                    url = streams[stream]
                elif stream == "iphoneLink":
                    bitrate = 250
                    url = streams[stream]
                elif stream == "tabletLink":
                    bitrate = 300
                    url = streams[stream]

                # These windows stream won't work
                # elif stream == "windowsLink":
                #     bitrate = 1200
                #     url = streams[stream]
                # elif stream == "wpLink":
                #     bitrate = 1200
                #     url = streams[stream]

                elif stream == "name":
                    pass
                else:
                    Logger.Warning("No url found for type '%s'", stream)

                if "livestreams.omroep.nl/live/" in url and url.endswith("m3u8"):
                    Logger.Info("Found NPO Stream, adding ?protection=url")
                    url = "%s?protection=url" % (url, )

                if bitrate:
                    part.AppendMediaStream(url, bitrate)

                    if url == liveStreamValue and ".m3u8" in url:
                        # if it was equal to the previous one, assume we have a m3u8. Reset the others.
                        Logger.Info("Found same M3u8 stream for all streams for this Live channel, using that one: %s", url)
                        liveItem.MediaItemParts = []
                        liveItem.url = url
                        liveItem.complete = False
                        break
                    elif "playlist.m3u8" in url:
                        # if we have a playlist, use that one. Reset the others.
                        Logger.Info("Found M3u8 playlist for this Live channel, using that one: %s", url)
                        liveItem.MediaItemParts = []
                        liveItem.url = url
                        liveItem.complete = False
                        break
                    else:
                        # add it to the possibilities
                        liveStreamValue = url
            items.append(liveItem)
        return "", items

    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """
        Logger.Trace(resultSet)
        title = resultSet.get("title")

        if not title:
            return None

        if title.islower():
            title = "%s%s" % (title[0].upper(), title[1:])

        link = resultSet.get("feedLink")
        if not link.startswith("http"):
            link = urlparse.urljoin(self.baseUrl, link)

        item = mediaitem.MediaItem(title, link)
        item.icon = self.icon
        item.thumb = self.noImage
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

        mediaLink = resultSet.get("ipadLink")
        title = resultSet.get("title")

        # it seems overkill, but not all items have a contentLink and of we set
        # the url to self.baseUrl it will be a duplicate item if the titles are
        # equal
        url = resultSet.get("contentLink") or mediaLink or self.baseUrl
        if not url.startswith("http"):
            url = urlparse.urljoin(self.baseUrl, url)

        item = mediaitem.MediaItem(title, url)
        item.thumb = self.noImage

        if mediaLink:
            item.AppendSingleStream(mediaLink, self.channelBitrate)

        # get the thumbs from multiple locations
        thumbUrls = resultSet.get("images", None)
        thumbUrl = None
        if thumbUrls:
            thumbUrl = \
                thumbUrls[0].get("fullScreenLink", None) or \
                thumbUrls[0].get("previewLink", None) or \
                resultSet.get("imageLink", None)

        if thumbUrl and not thumbUrl.startswith("http"):
            thumbUrl = urlparse.urljoin(self.baseUrl, thumbUrl)

        item.thumb = self.noImage
        if thumbUrl:
            item.thumb = thumbUrl

        item.icon = self.icon
        item.type = 'video'

        item.description = HtmlHelper.ToText(resultSet.get("text"))
        #if item.description:
        #    item.description = item.description.replace("<br />", "\n")

        posix = resultSet.get("timestamp", None)
        if posix:
            broadcastDate = DateHelper.GetDateFromPosix(int(posix))
            item.SetDate(broadcastDate.year,
                         broadcastDate.month,
                         broadcastDate.day,
                         broadcastDate.hour,
                         broadcastDate.minute,
                         broadcastDate.second)

        item.complete = True
        return item

    def CtMnDownloadItem(self, item):
        """Downloads an existing MediaItem with more data.

         Arguments:
         item : MediaItem - the MediaItem that should be downloaded.

         Returns:
         The original item with more data added to it's properties.

         Used to download an <item>. If the item is not complete, the self.UpdateVideoItem
         method is called to update the item. The method downloads only the MediaStream
         with the bitrate that was set in the addon settings.

         After downloading the self.downloaded property is set.

         """

        item = self.DownloadVideoItem(item)
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

        Logger.Debug("Updating a (Live) video item")

        part = item.CreateNewEmptyMediaPart()
        for s, b in M3u8.GetStreamsFromM3u8(item.url, self.proxy, appendQueryString=True):
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)
        item.complete = True

        return item
