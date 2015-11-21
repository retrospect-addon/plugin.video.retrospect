import mediaitem
import chn_class

from regexer import Regexer
from helpers.datehelper import DateHelper

from logger import Logger
from urihandler import UriHandler
from parserdata import ParserData


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
        self.noImage = "twitimage.png"

        # setup the urls
        self.mainListUri = "https://twit.tv/shows"
        self.baseUrl = "https://twit.tv"

        # setup the main parsing data
        self.episodeItemRegex = '<img[^>]+src="(?<thumburl>[^"]+)"[^>]*></a>\W+<div[^>]+>\W+' \
                                '<h2[^>]*><a[^>]+href="/(?<url>shows/[^"]+)"[^>]*>(?<title>[^<]+)' \
                                '</a></h2>\W+<div[^>]*>(?<description>[^<]+)'
        self.episodeItemRegex = Regexer.FromExpresso(self.episodeItemRegex)
        self._AddDataParser(self.mainListUri, preprocessor=self.AddLiveStream, matchType=ParserData.MatchExact,
                            parser=self.episodeItemRegex, creator=self.CreateEpisodeItem)

        self.videoItemRegex = '<div[^>]+class="episode item"[^>]*>\W+<a[^>]+href="(?<url>[^"]+)" ' \
                              'title="(?<title>[^"]+)">[\w\W]{0,500}?<img[^>]+src="' \
                              '(?<thumburl>[^"]+)"[^>]+>[\w\W]{0,500}?<span[^>]+class="date"' \
                              '[^>]*>(?<month>\w+) (?<day>\d+)\w+ (?<year>\d+)'
        self.videoItemRegex = Regexer.FromExpresso(self.videoItemRegex)
        self._AddDataParser("*", parser=self.videoItemRegex, creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        self.mediaUrlRegex = '<a href="([^"]+_(\d+).mp4)"[^>]+download>'

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddLiveStream(self, data):
        """ Adds live streams to the initial list to display

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        The return values should always be instantiated in at least ("", []).

        """

        items = []

        item = mediaitem.MediaItem("\a.: TWiT.TV Live :.", "http://live.twit.tv/")
        item.thumb = self.noImage
        item.icon = self.icon
        item.complete = True

        playbackItem = mediaitem.MediaItem("Play Live", "http://live.twit.tv/")
        playbackItem.type = "playlist"
        playbackItem.thumb = self.noImage
        playbackItem.icon = self.icon
        playbackItem.isLive = True
        playbackPart = playbackItem.CreateNewEmptyMediaPart()

        # noinspection PyStatementEffect
        """
        BitGravity
        There are two streams available from BitGravity; a 512 kbps low-bandwidth stream
        and a 1 Mbps high-bandwidth stream.

        UStream
        This is the default stream. The UStream stream is a variable stream that maxes at
        2.2 Mbps and adjusts down based on your bandwidth.
        Justin.tv

        The Justin.tv stream is a 2.2 mbps high-bandwidth stream that will adjust to lower
        bandwidth and resolutions.

        Flosoft.biz
        The Flosoft.biz stream is a 5 resolution/bitrate HLS stream, intended for our app developers.
        Please see Flosoft Developer Section. This stream is hosted by TWiT through Flosoft.biz
        """

        # http://wiki.twit.tv/wiki/TWiT_Live#Direct_links_to_TWiT_Live_Video_Streams
        mediaUrls = {  # Justin TV
                       # "2000": "http://usher.justin.tv/stream/multi_playlist/twit.m3u8",

                       # Flosoft (http://wiki.twit.tv/wiki/Developer_Guide#Flosoft.biz)
                       "264": "http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_240/playlist.m3u8",
                       "512": "http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_360/playlist.m3u8",
                       "1024": "http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_480/playlist.m3u8",
                       "1475": "http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_540/playlist.m3u8",
                       "1778": "http://hls.cdn.flosoft.biz/flosoft/mp4:twitStream_720/playlist.m3u8",

                       # UStream
                       "1524": "http://iphone-streaming.ustream.tv/ustreamVideo/1524/streams/live/playlist.m3u8",

                       # BitGravity
                       # "512": "http://209.131.99.99/twit/live/low",
                       # "1024": "http://209.131.99.99/twit/live/high",
                       #"512": "http://64.185.191.180/cdn-live-s1/_definst_/twit/live/low/playlist.m3u8",
                       #"1024": "http://64.185.191.180/cdn-live-s1/_definst_/twit/live/high/playlist.m3u8",
        }

        for bitrate in mediaUrls:
            playbackPart.AppendMediaStream(mediaUrls[bitrate], bitrate)

        Logger.Debug("Streams: %s", playbackPart)
        playbackItem.complete = True
        item.items.append(playbackItem)
        Logger.Debug("Appended: %s", playbackItem)

        items.append(item)
        return data, items

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

        url = "%s/%s" % (self.baseUrl, resultSet["url"])
        item = mediaitem.MediaItem(resultSet["title"], url)

        item.thumb = resultSet["thumburl"]
        if not item.thumb.startswith("http"):
            item.thumb = "%s%s" % (self.baseUrl, item.thumb)
        item.thumb = item.thumb.replace("coverart-small", "coverart")

        item.icon = self.icon
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

        url = resultSet["url"]
        if not url.startswith("http"):
            url = "%s%s" % (self.baseUrl, url)
        name = resultSet["title"]

        item = mediaitem.MediaItem(name, url)
        # item.description = resultSet["description"]
        item.type = 'video'
        item.icon = self.icon
        item.thumb = self.noImage

        month = resultSet["month"]
        month = DateHelper.GetMonthFromName(month, "en", False)
        day = resultSet["day"]
        year = resultSet["year"]
        item.SetDate(year, month, day)

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

        data = UriHandler.Open(item.url, proxy=self.proxy)
        streams = Regexer.DoRegex(self.mediaUrlRegex, data)

        item.MediaItemParts = []
        part = item.CreateNewEmptyMediaPart()
        for stream in streams:
            Logger.Trace(stream)
            part.AppendMediaStream(stream[0], stream[1])

        item.complete = True
        return item
