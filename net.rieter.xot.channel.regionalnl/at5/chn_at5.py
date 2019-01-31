import chn_class

from mediaitem import MediaItem
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

    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.noImage = "at5image.png"

        # setup the urls
        self.mainListUri = "http://www.at5.nl/gemist/tv"
        self.baseUrl = "http://www.at5.nl"
        self.swfUrl = "http://www.at5.nl/embed/at5player.swf"

        # setup the main parsing data
        epside_item_regex = r'<option value="(\d+)"[^>]*>([^<]+)'
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              parser=epside_item_regex, creator=self.create_episode_item,
                              preprocessor=self.add_live_channel)

        # Main video items
        video_item_regex = r'data-href="/(gemist/tv/\d+/(\d+)/[^"]+)"[^>]*>\W*<div class="uitz_new">' \
                           r'\W*<div class="uitz_new_image">\W*<img src="([^"]+)[^>]*>\W+</div>\W+' \
                           r'<div class="uitz_new_desc">(?:\W*<div[^>]*>){1,2}[^-]*-([^<]+)</div>' \
                           r'\W+div class="uitz_new_desc_title_time">\W+\w+ (\d+) (\w+) (\d+) (\d+):(\d+)'
        self._add_data_parser("*",
                              parser=video_item_regex, creator=self.create_video_item,
                              updater=self.update_video_item)

        # Paging
        self.pageNavigationRegexIndex = 1
        page_navigation_regex = r'<a[^>]+href="([^"]+/)(\d+)"[^>]*>\W+gt;\W+</a>'
        self._add_data_parser("*", parser=page_navigation_regex, creator=self.create_page_item)

        self._add_data_parser("#livestream", updater=self.update_live_stream)

        #===============================================================================================================
        # non standard items
        self.mediaUrlRegex = r'.setup([^<]+);\W*</script>'

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        item = MediaItem(result_set[1], "%s/%s" % (self.mainListUri, result_set[0]))
        item.icon = self.icon
        item.thumb = self.noImage
        item.complete = True
        return item

    def add_live_channel(self, data):
        """ Performs pre-process actions for data processing.

        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        :param str data: The retrieve data that was loaded for the current item and URL.

        :return: A tuple of the data and a list of MediaItems that were generated.
        :rtype: tuple[str|JsonHelper,list[MediaItem]]

        """

        Logger.info("Performing Pre-Processing")
        items = []

        title = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
        item = MediaItem("\a.: {} :.".format(title), "")
        item.type = "folder"
        items.append(item)

        live_item = MediaItem(title, "#livestream")
        live_item.type = "video"
        live_item.isLive = True
        item.items.append(live_item)

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        thumb_url = result_set[2]
        title = result_set[3].strip()
        if "http" not in thumb_url:
            thumb_url = "%s%s" % (self.baseUrl, thumb_url)

        url = "%s/%s" % (self.baseUrl, result_set[0])
        item = MediaItem(title, url)
        item.thumb = thumb_url
        item.icon = self.icon
        item.type = 'video'
        item.complete = False

        day = result_set[4]
        month = result_set[5]
        month = DateHelper.get_month_from_name(month, language="nl")
        year = result_set[6]
        hour = result_set[7]
        minute = result_set[8]
        item.set_date(year, month, day, hour, minute, 0)
        return item

    def update_live_stream(self, item):
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug("Updating the live stream")
        url = "https://rrr.sz.xlcdn.com/?account=atvijf" \
              "&file=live&type=live&service=wowza&protocol=https&output=playlist.m3u8"

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
        """ Updates an existing MediaItem with more data.

        Used to update none complete MediaItems (self.complete = False). This
        could include opening the item's URL to fetch more data and then process that
        data or retrieve it's real media-URL.

        The method should at least:
        * cache the thumbnail to disk (use self.noImage if no thumb is available).
        * set at least one MediaItemPart with a single MediaStream.
        * set self.complete = True.

        if the returned item does not have a MediaItemPart then the self.complete flag
        will automatically be set back to False.

        :param MediaItem item: the original MediaItem that needs updating.

        :return: The original item with more data added to it's properties.
        :rtype: MediaItem

        """

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        data = UriHandler.open(item.url, proxy=self.proxy).decode('unicode_escape')
        streams = Regexer.do_regex(r"file:\W+'([^']+)'", data)
        part = item.create_new_empty_media_part()
        for s in streams:
            if "anifest" in s or "smil?" in s:
                continue
            s = JsonHelper.convert_special_chars(s)
            if s.startswith("rtmp"):
                continue

            bitrate_add = 0
            if s.endswith(".m3u8"):
                bitrate_add = 200

            if "_hi.mp4" in s:
                part.append_media_stream(s, 2402 + bitrate_add)
                part.append_media_stream(s.replace("_hi.mp4", "_medium.mp4"), 1402 + bitrate_add)
                part.append_media_stream(s.replace("_hi.mp4", "_low.mp4"), 302 + bitrate_add)

            elif "_medium.mp4" in s:
                part.append_media_stream(s, 1402 + bitrate_add)
                part.append_media_stream(s.replace("_medium.mp4", "_low.mp4"), 302 + bitrate_add)
        item.complete = True
        return item
