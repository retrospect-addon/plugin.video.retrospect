import mediaitem
import chn_class
from addonsettings import AddonSettings
from helpers.datehelper import DateHelper
from helpers.jsonhelper import JsonHelper
from helpers.languagehelper import LanguageHelper
from logger import Logger
from parserdata import ParserData
from regexer import Regexer
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
        self.noImage = "at5image.png"

        # setup the urls
        self.mainListUri = "http://www.at5.nl/gemist/tv"
        self.baseUrl = "http://www.at5.nl"
        self.swfUrl = "http://www.at5.nl/embed/at5player.swf"

        # setup the main parsing data
        epsideItemRegex = '<option value="(\d+)"[^>]*>([^<]+)'
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              parser=epsideItemRegex, creator=self.create_episode_item,
                              preprocessor=self.AddLiveChannel)

        # Main video items
        videoItemRegex = 'data-href="/(gemist/tv/\d+/(\d+)/[^"]+)"[^>]*>\W*<div class="uitz_new">' \
                         '\W*<div class="uitz_new_image">\W*<img src="([^"]+)[^>]*>\W+</div>\W+' \
                         '<div class="uitz_new_desc">(?:\W*<div[^>]*>){1,2}[^-]*-([^<]+)</div>' \
                         '\W+div class="uitz_new_desc_title_time">\W+\w+ (\d+) (\w+) (\d+) (\d+):(\d+)'
        self._add_data_parser("*",
                              parser=videoItemRegex, creator=self.create_video_item,
                              updater=self.update_video_item)

        # Paging
        self.pageNavigationRegexIndex = 1
        pageNavigationRegex = '<a[^>]+href="([^"]+/)(\d+)"[^>]*>\W+gt;\W+</a>'
        self._add_data_parser("*",
                              parser=pageNavigationRegex, creator=self.create_page_item)

        self._add_data_parser("#livestream", updater=self.UpdateLiveStream)

        #===============================================================================================================
        # non standard items
        self.mediaUrlRegex = '.setup([^<]+);\W*</script>'

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_episode_item(self, resultSet):
        """
        Accepts an arraylist of results. It returns an item.
        """

        item = mediaitem.MediaItem(resultSet[1], "%s/%s" % (self.mainListUri, resultSet[0]))
        item.icon = self.icon
        item.thumb = self.noImage
        item.complete = True
        return item

    def AddLiveChannel(self, data):
        Logger.info("Performing Pre-Processing")
        items = []

        title = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
        item = mediaitem.MediaItem("\a.: {} :.".format(title), "")
        item.type = "folder"
        items.append(item)

        liveItem = mediaitem.MediaItem(title, "#livestream")
        liveItem.type = "video"
        liveItem.isLive = True
        item.items.append(liveItem)

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

        day = resultSet[4]
        month = resultSet[5]
        month = DateHelper.get_month_from_name(month, language="nl")
        year = resultSet[6]
        hour = resultSet[7]
        minute = resultSet[8]
        item.set_date(year, month, day, hour, minute, 0)
        return item

    def UpdateLiveStream(self, item):
        Logger.debug("Updating the live stream")
        url = "https://rrr.sz.xlcdn.com/?account=atvijf&file=live&type=live&service=wowza&protocol=https&output=playlist.m3u8"

        part = item.create_new_empty_media_part()
        if AddonSettings.use_adaptive_stream_add_on():
            stream = part.append_media_stream(url, 0)
            M3u8.set_input_stream_addon_input(stream, self.proxy, item.HttpHeaders)
        else:
            for s, b in M3u8.get_streams_from_m3u8(url, self.proxy):
                item.complete = True
                part.append_media_stream(s, b)
        return item

    def update_video_item(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        data = UriHandler.open(item.url, proxy=self.proxy).decode('unicode_escape')
        streams = Regexer.do_regex("file:\W+'([^']+)'", data)
        part = item.create_new_empty_media_part()
        for s in streams:
            if "anifest" in s or "smil?" in s:
                continue
            s = JsonHelper.convert_special_chars(s)
            if s.startswith("rtmp"):
                continue

            bitrateAdd = 0
            if s.endswith(".m3u8"):
                bitrateAdd = 200

            if "_hi.mp4" in s:
                # if s.startswith("rtmp"):
                #     s = self.get_verifiable_video_url(s)
                part.append_media_stream(s, 2402 + bitrateAdd)
                part.append_media_stream(s.replace("_hi.mp4", "_medium.mp4"), 1402 + bitrateAdd)
                part.append_media_stream(s.replace("_hi.mp4", "_low.mp4"), 302 + bitrateAdd)

            elif "_medium.mp4" in s:
                # if s.startswith("rtmp"):
                #     s = self.get_verifiable_video_url(s)
                part.append_media_stream(s, 1402 + bitrateAdd)
                part.append_media_stream(s.replace("_medium.mp4", "_low.mp4"), 302 + bitrateAdd)
        item.complete = True
        return item
