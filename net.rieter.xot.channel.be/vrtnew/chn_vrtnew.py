# coding:Cp1252

import mediaitem
import chn_class

from parserdata import ParserData
from regexer import Regexer
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
        if self.channelCode == "redactie":
            self.noImage = "redactieimage.png"
            self.mainListUri = "http://deredactie.be/cm/vrtnieuws/videozone"
            self.baseUrl = "http://deredactie.be"

        else:
            raise IndexError("Invalid Channel Code")  # setup the urls

        self.swfUrl = "%s/html/flash/common/player.5.10.swf" % (self.baseUrl,)

        # setup the main parsing data
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            parser='<li[^>]*>\W*<a href="(/cm/[^"]+/videozone/programmas/[^"]+)" title="([^"]+)"\W*>',
                            creator=self.CreateEpisodeItem)

        self._AddDataParser("*", creator=self.CreateVideoItem,
                            parser='<a href="(/cm/[^/]+/videozone/programmas/[^?"]+)"[^>]*>\W*<span[^>]+>([^<]+)</span>\W*(?:<span[^<]+</span>\W*){0,2}<span class="video">\W*<img src="([^"]+)"')
        self._AddDataParser("*", creator=self.CreateVideoItem,
                            parser='data-video-permalink="([^"]+)"[^>]*>\W+<span[^>]*>([^<]+)</span>\W+<span[^>]*>\W+<img[^>]*src="([^"]+)"', updater=self.UpdateVideoItem)

        self._AddDataParser("*", creator=self.CreatePageItem,
                            parser='<a href="([^"]+\?page=\d+)"[^>]+>(\d+)')
        self.pageNavigationRegexIndex = 1

        self.mediaUrlRegex = 'data-video-((?:src|rtmp|iphone|mobile)[^=]*)="([^"]+)"\W+(?:data-video-[^"]+path="([^"]+)){0,1}'
        # ====================================== Actual channel setup STOPS here =======================================
        return

    def PreProcessFolderList(self, data):
        # Only get the first bit
        seperatorIndex = data.find('<div class="splitter split24">')
        data = data[:seperatorIndex]
        return chn_class.Channel.PreProcessFolderList(self, data)

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

        url = "%s%s" % (self.baseUrl, resultSet[0])
        name = resultSet[1]

        item = mediaitem.MediaItem(name.capitalize(), url)
        item.icon = self.icon
        item.type = "folder"
        item.complete = True
        return item

    def CreateFolderItem(self, resultSet):
        """Creates a MediaItem of type 'folder' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(strig) - the resultSet of the self.folderItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.Trace(resultSet)
        item = None
        # not implemented yet
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

        Logger.Trace(resultSet)

        name = resultSet[1]
        url = resultSet[0]
        if not url.startswith("http"):
            url = "%s%s" % (self.baseUrl, resultSet[0])

        if len(resultSet) == 3:
            thumb = resultSet[2]
        else:
            thumb = ""

        if thumb and not thumb.startswith("http://"):
            thumb = "%s%s" % (self.baseUrl, thumb)

        item = mediaitem.MediaItem(name, url)
        item.thumb = thumb
        item.description = name
        item.icon = self.icon
        item.type = 'video'
        item.complete = False

        nameParts = name.rsplit("/", 3)
        # if name[-3] == name[-6] == "/":
        #     year = int(name[-2:]) + 2000
        #     month = name[-5:-3]
        #     day = name[-8:-6]
        if len(nameParts) == 3:
            Logger.Debug("Found possible date in name: %s", nameParts)
            year = nameParts[2]
            if len(year) == 2:
                year = 2000 + int(year)
            month = nameParts[1]
            day = nameParts[0].rsplit(" ", 1)[1]
            Logger.Trace("%s - %s - %s", year, month, day)
            item.SetDate(year, month, day)

        return item

    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        # noinspection PyStatementEffect
        """
        data-video-id="1613274"
        data-video-type="video"
        data-video-src="http://media.vrtnieuws.net/2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-title="Het journaal 1 - 25/04/13"
        data-video-rtmp-server="rtmp://vrt.flash.streampower.be/vrtnieuws"
        data-video-rtmp-path="2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-rtmpt-server="rtmpt://vrt.flash.streampower.be/vrtnieuws"
        data-video-rtmpt-path="2013/04/135132051ONL1304255866693.urlFLVLong.flv"
        data-video-iphone-server="http://iphone.streampower.be/vrtnieuws_nogeo/_definst_"
        data-video-iphone-path="2013/04/135132051ONL1304255866693.urlMP4_H.264.m4v"
        data-video-mobile-server="rtsp://mp4.streampower.be/vrt/vrt_mobile/vrtnieuws_nogeo"
        data-video-mobile-path="2013/04/135132051ONL1304255866693.url3GP_MPEG4.3gp"
        data-video-sitestat-program="het_journaal_1_-_250413_id_1-1613274"
        """

        # now the mediaurl is derived. First we try WMV
        data = UriHandler.Open(item.url)

        descriptions = Regexer.DoRegex('<div class="longdesc"><p>([^<]+)</', data)
        Logger.Trace(descriptions)
        for desc in descriptions:
            item.description = desc

        data = data.replace("\\/", "/")
        urls = Regexer.DoRegex(self.mediaUrlRegex, data)
        part = item.CreateNewEmptyMediaPart()
        for url in urls:
            Logger.Trace(url)
            if url[0] == "src":
                flv = url[1]
                bitrate = 750
            else:
                flvServer = url[1]
                flvPath = url[2]

                if url[0] == "rtmp-server":
                    flv = "%s//%s" % (flvServer, flvPath)
                    bitrate = 750

                elif url[0] == "rtmpt-server":
                    continue
                    #flv = "%s//%s" % (flvServer, flvPath)
                    #flv = self.GetVerifiableVideoUrl(flv)
                    #bitrate = 1500

                elif url[0] == "iphone-server":
                    flv = "%s/%s" % (flvServer, flvPath)
                    if not flv.endswith("playlist.m3u8"):
                        flv = "%s/playlist.m3u8" % (flv,)

                    for s, b in M3u8.GetStreamsFromM3u8(flv, self.proxy):
                        item.complete = True
                        part.AppendMediaStream(s, b)
                    # no need to continue adding the streams
                    continue

                elif url[0] == "mobile-server":
                    flv = "%s/%s" % (flvServer, flvPath)
                    bitrate = 250

                else:
                    flv = "%s/%s" % (flvServer, flvPath)
                    bitrate = 0

            part.AppendMediaStream(flv, bitrate)

        item.complete = True
        return item
