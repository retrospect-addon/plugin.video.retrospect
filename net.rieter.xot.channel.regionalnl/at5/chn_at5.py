import mediaitem
import chn_class
from helpers.datehelper import DateHelper
from helpers.jsonhelper import JsonHelper
from logger import Logger
from regexer import Regexer
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
        self.noImage = "at5image.png"

        # setup the urls
        self.mainListUri = "http://www.at5.nl/gemist/tv"
        self.baseUrl = "http://www.at5.nl"
        self.swfUrl = "http://www.at5.nl/embed/at5player.swf"

        # setup the main parsing data
        self.episodeItemRegex = '<option value="(\d+)"[^>]*>([^<]+)'
        self.videoItemRegex = 'data-href="(/gemist/tv/\d+/(\d+)/[^"]+)"[^>]*>\W*<div class="uitz_new">\W*<div class="uitz_new_image">\W*<img src="([^"]+)[^>]*>\W+</div>\W+<div class="uitz_new_desc">\W+<div class="uitz_new_desc_title">([^<]+)'
        self.mediaUrlRegex = '.setup([^<]+);\W*</script>'
        self.pageNavigationRegex = '<a href="(/[^"]+page/)(\d+)">\d+</a>'
        self.pageNavigationRegexIndex = 1

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def CreateEpisodeItem(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """

        item = mediaitem.MediaItem(resultSet[1], "%s/%s" % (self.mainListUri, resultSet[0]))
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

        # vid = resultSet[1]
        thumbUrl = resultSet[2]
        title = resultSet[3].strip()
        if "http" not in thumbUrl:
            thumbUrl = "%s%s" % (self.baseUrl, thumbUrl)

        url = "%s/%s" % (self.baseUrl, resultSet[0])
        item = mediaitem.MediaItem(title, url)
        item.thumb = thumbUrl
        item.icon = self.icon
        item.type = 'video'
        item.complete = False

        # try to parse a date (for Journaal)
        try:
            dateParts = resultSet[0].split("/")[-1].split("+")
            Logger.Trace(dateParts)
            day = dateParts[1]
            monthName = dateParts[2]
            year = dateParts[3]
            month = DateHelper.GetMonthFromName(monthName, "nl")
            hour = dateParts[5][:2]
            minutes = dateParts[5][-2:]
            item.SetDate(year, month, day, hour, minutes, 0)
        except:
            Logger.Warning("Error parsing date", exc_info=True)
        return item

    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        data = UriHandler.Open(item.url, proxy=self.proxy).decode('unicode_escape')
        streams = Regexer.DoRegex("file:\W+'([^']+)'", data)
        part = item.CreateNewEmptyMediaPart()
        for s in streams:
            if "anifest" in s:
                continue
            s = JsonHelper.ConvertSpecialChars(s)
            if s.startswith("rtmp"):
                s = self.GetVerifiableVideoUrl(s)
                part.AppendMediaStream(s, 1001)
                part.AppendMediaStream(s.replace("_medium.mp4", "_low.mp4"), 301)
            else:
                part.AppendMediaStream(s, 1002)
                part.AppendMediaStream(s.replace("_medium.mp4", "_low.mp4"), 302)

        item.complete = True
        return item
