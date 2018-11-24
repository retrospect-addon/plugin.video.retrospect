import mediaitem
import chn_class
from helpers import datehelper
from regexer import Regexer

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
        self.noImage = "amtimage.png"

        # setup the urls
        self.baseUrl = "http://trailers.apple.com"
        self.mainListUri = "http://trailers.apple.com/trailers/home/feeds/just_added.json"
        # self.mainListUri = "http://trailers.apple.com/ca/home/feeds/most_pop.json"

        # setup the main parsing data
        self._add_data_parser(self.mainListUri, parser=[], json=True, creator=self.create_episode_item)
        self._add_data_parser("*", json=True, preprocessor=self.GetMovieId,
                              parser=["clips", ], creator=self.create_video_item)

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_episode_item(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """

        Logger.trace(resultSet)
        title = resultSet["title"]
        date = resultSet["trailers"][0]["postdate"]
        url = resultSet["trailers"][0]["url"]
        thumbUrl = resultSet["poster"]
        if "http:" not in thumbUrl:
            thumbUrl = "%s%s" % (self.baseUrl, thumbUrl)
        fanart = thumbUrl.replace("poster.jpg", "background.jpg")

        # get the url that shows all trailers/clips. Because the json
        # only shows the most recent one.
        url = "%s%s" % (self.baseUrl, url)

        # Logger.Trace(date)
        dates = date.split(" ")
        # Logger.Trace(dates)
        day = dates[1]
        month = datehelper.DateHelper.get_month_from_name(dates[2], "en")
        year = dates[3]

        # dummy class
        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.thumb = thumbUrl.replace("poster.jpg", "poster-xlarge.jpg")
        item.fanart = fanart
        item.set_date(year, month, day)
        item.complete = True
        return item

    def GetMovieId(self, data):
        """ Extract the movie ID and replace the data with the correct JSON

        @param data: the original data
        @return: the new data
        """
        Logger.info("Performing Pre-Processing")
        items = []

        movieId = Regexer.do_regex("movietrailers://movie/detail/(\d+)", data)[-1]
        Logger.debug("Found Movie ID: %s", movieId)
        url = "%s/trailers/feeds/data/%s.json" % (self.baseUrl, movieId)
        data = UriHandler.open(url, proxy=self.proxy)

        # set it for logging purposes
        self.parentItem.url = url

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_video_item(self, resultSet):
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
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        """

        Logger.trace(resultSet)

        title = resultSet["title"]
        title = "%s - %s" % (self.parentItem.name, title)

        thumb = resultSet["thumb"]
        year, month, day = resultSet["posted"].split("-")
        item = mediaitem.MediaItem(title, self.parentItem.url)
        item.icon = self.icon
        item.description = self.parentItem.description
        item.type = 'video'
        item.thumb = thumb
        item.fanart = self.parentItem.fanart
        item.set_date(year, month, day)

        part = item.create_new_empty_media_part()
        part.HttpHeaders["User-Agent"] = "QuickTime/7.6 (qtver=7.6;os=Windows NT 6.0Service Pack 2)"

        if "versions" in resultSet and "enus" in resultSet["versions"] and "sizes" in resultSet["versions"]["enus"]:
            streams = resultSet["versions"]["enus"]["sizes"]
            streamTypes = ("src", "srcAlt")
            bitrates = {"hd1080": 8300, "hd720": 5300, "sd": 1200}
            for s in streams:
                bitrate = bitrates.get(s, 0)
                streamData = streams[s]

                # find all possible stream stream types
                for t in streamTypes:
                    if t in streamData:
                        streamUrl = streamData[t]
                        if streamUrl.endswith(".mov"):
                            # movs need to have a 'h' before the quality
                            parts = streamUrl.rsplit("_", 1)
                            if len(parts) == 2:
                                Logger.trace(parts)
                                streamUrl = "%s_h%s" % (parts[0], parts[1])
                            part.append_media_stream(streamUrl, bitrate)
                        else:
                            part.append_media_stream(streamUrl, bitrate)
                        item.complete = True

        return item
