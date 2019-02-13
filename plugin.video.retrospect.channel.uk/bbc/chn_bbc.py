import chn_class
from mediaitem import MediaItem
from helpers.xmlhelper import XmlHelper
from helpers import subtitlehelper
from helpers.jsonhelper import JsonHelper
from helpers.datehelper import DateHelper
from streams.f4m import F4m
from logger import Logger
from parserdata import ParserData
from regexer import Regexer
from urihandler import UriHandler


class Channel(chn_class.Channel):
    def __init__(self, channel_info):
        """ Initialisation of the class.

        All class variables should be instantiated here and this method should not
        be overridden by any derived classes.

        :param ChannelInfo channel_info: The channel info object to base this channel on.

        """

        chn_class.Channel.__init__(self, channel_info)

        # ============== Actual channel setup STARTS here and should be overwritten from derived classes ===============
        self.liveUrl = None

        # setup the urls
        self.baseUrl = "http://www.bbc.co.uk/"
        self.swfUrl = "http://emp.bbci.co.uk/emp/SMPf/1.13.13/StandardMediaPlayerChromelessFlash.swf"

        self.noImage = "bbciplayerimage.png"
        self.mainListUri = "http://www.bbc.co.uk/iplayer"

        # setup the main parsing data
        self.episodeItemRegex = '<a class="letter stat" href="(?<url>/iplayer/a-z/[^"]+)">(?<title>[^<]+)</a>'\
                                .replace("(?<", "(?P<")
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              preprocessor=self.add_live_channels,
                              parser=self.episodeItemRegex, creator=self.create_episode_item)

        # Standard items
        self._add_data_parser("*", preprocessor=self.pre_process_folder_list)
        self.folderItemRegex = r'<a href="(?<url>/iplayer/brand/[^"]+)"[^>]*>\W+<i[^>]+></i>\W+' \
                               r'<span[^>]+>(?<title>[^<]+)<'.replace("(?<", "(?P<")
        self._add_data_parser("*", parser=self.folderItemRegex, creator=self.create_folder_item)
        self.videoItemRegex = r'<a\W+href="/iplayer/episode/(?<url>[^/]+)[^>]+>\W+<div[^>]+>[^>]+' \
                              r'</div>\W+(?:<div[^>]+>[^>]+</div>\W+)?[\w\W]{0,500}?<source ' \
                              r'srcset="(?<thumburl>[^"]+)"[\w\W]{0,500}?<div class="secondary">' \
                              r'\W+<div[^>]+>(?<title>[^<]+)</div>\W+(?:<div[^>]+>(?<subtitle>' \
                              r'[^<]+)</div>\W+)?<p[^>]*>(?<description>[^<]*)</p>[\w\W]{0,1000}?' \
                              r'(?:<span class="release">\W+First shown: (?<day>\d+) (?<month>\w+) ' \
                              r'(?<year>\d+)|<div class="period")'
        self.videoItemRegex = Regexer.from_expresso(self.videoItemRegex)
        self._add_data_parser("*", parser=self.videoItemRegex, creator=self.create_video_item)

        # Live channels
        self._add_data_parser("http://vs-hds-uk-live.edgesuite.net/",
                              updater=self.update_live_item)
        self._add_data_parser("http://a.files.bbci.co.uk/media/live/manifesto/",
                              updater=self.update_live_item)

        # Generic updater
        self._add_data_parser("*", updater=self.update_video_item)

        # ===============================================================================================================
        # non standard items
        # if self.proxy:
        #     self.proxy.Filter = ["mediaselector"]

        self.searchUrl = "http://feeds.bbc.co.uk/iplayer/search/tv/?q=%s"
        self.programs = dict()

        # ===============================================================================================================
        # Test cases:
        # http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/pc/vpid/b04plqyv/atk/

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_episode_item(self, result_set):
        """ Creates a new MediaItem for an episode.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)
        item = chn_class.Channel.create_episode_item(self, result_set)
        if item is not None:
            item.name = "Shows: %s" % (item.name.upper(),)
        return item

    def pre_process_folder_list(self, data):
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

        if "episode.json" in self.parentItem.url:
            Logger.debug("Fetching Carousel data")
            json = JsonHelper(data)
            data = json.get_value("carousel")

        Logger.debug("Pre-Processing finished")
        return data, items

    def create_folder_item(self, result_set):
        """ Creates a MediaItem of type 'folder' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'folder'.
        :rtype: MediaItem|None

        """

        Logger.trace(result_set)

        item = chn_class.Channel.create_folder_item(self, result_set)
        brand = item.url[item.url.rindex("/") + 1:]

        # to match the first video regex: item.url = "http://www.bbc.co.uk/programmes/%s/episodes/player" % (brand, )
        item.url = "http://www.bbc.co.uk/iplayer/episodes/%s" % (brand,)
        item.isGeoLocked = True
        return item

    def create_video_item(self, result_set):
        """ Creates a MediaItem of type 'video' using the result_set from the regex.

        This method creates a new MediaItem from the Regular Expression or Json
        results <result_set>. The method should be implemented by derived classes
        and are specific to the channel.

        If the item is completely processed an no further data needs to be fetched
        the self.complete property should be set to True. If not set to True, the
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        :param list[str]|dict[str,str] result_set: The result_set of the self.episodeItemRegex

        :return: A new MediaItem of type 'video' or 'audio' (despite the method's name).
        :rtype: MediaItem|None

        """

        if "subtitle" in result_set and not result_set["subtitle"]:
            del result_set["subtitle"]

        item = chn_class.Channel.create_video_item(self, result_set)
        vid = item.url.replace(self.baseUrl, "")
        item.url = "http://www.bbc.co.uk/iplayer/episode/%s" % (vid,)
        if "year" in result_set and result_set["year"]:
            month = DateHelper.get_month_from_name(result_set["month"], "en", short=True)
            item.set_date(result_set["year"], month, result_set["day"])

        item.isGeoLocked = True
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

        Logger.trace(item.url)
        if not item.url.startswith("http://www.bbc.co.uk/mediaselector/"):
            Logger.debug("Determining the stream URL")
            data = UriHandler.open(item.url, proxy=self.proxy)
            needle = r'"vpid"\W*"([^"]+)"'
            vid = Regexer.do_regex(needle, data)[-1]
            stream_data_url = "http://open.live.bbc.co.uk/mediaselector/5/select/version/" \
                              "2.0/mediaset/iptv-all/vpid/%s" % (vid,)
        else:
            stream_data_url = item.url

        # this URL is one from the webbrowser but requires a security part. So NOT:
        # streamDataUrl = "http://open.live.bbc.co.uk/mediaselector/5/select/version
        # /2.0/mediaset/pc/vpid/%s" % (vid,)
        #
        # but:
        # streamDataUrl = "http://open.live.bbc.co.uk/mediaselector/5/select/version
        # /2.0/mediaset/pc/vpid/%s/atk/2214e42b5729dcdd012dfb61a3054d39309ccd31/asn/1/
        # And I don't know where that one comes from

        part = item.create_new_empty_media_part()

        stream_data = UriHandler.open(stream_data_url, proxy=self.proxy)
        # Reroute for debugging
        # from debug.router import Router
        # streamData = Router.get_via("uk", streamDataUrl, self.proxy)

        connection_datas = Regexer.do_regex(
            r'<media bitrate="(\d+)"[^>]+>\W*'
            r'(<connection[^>]+>\W*)'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?'
            r'(<connection[^>]+>\W*)?</media>', stream_data)

        for connection_data in connection_datas:
            # first the bitrate
            bitrate = connection_data[0]
            Logger.trace("Found Media: %s", connection_data)

            # go through the available connections
            for connection in connection_data[1:]:
                if not connection:
                    continue

                connection_xml = XmlHelper(connection)
                Logger.trace("Analyzing Connection: %s", connection)
                supplier = connection_xml.get_tag_attribute("connection", {"supplier": None})
                protocol = connection_xml.get_tag_attribute("connection", {"protocol": None})
                transfer_format = connection_xml.get_tag_attribute("connection", {"transferFormat": None})
                Logger.debug("Found connection information:\n"
                             "Protocol:       %s\n"
                             "TransferFormat: %s\n"
                             "Supplier:       %s\n"
                             "Bitrate:        %s",
                             protocol, transfer_format, supplier, bitrate)

                if protocol.startswith("http"):
                    if transfer_format != "hls":
                        Logger.debug("Ignoring TransferFormat: %s", transfer_format)
                        continue
                    if "lime" in supplier or "mf_akamai_uk" in supplier:
                        Logger.debug("Ignoring Supplier: %s", supplier)
                        continue
                    url = connection_xml.get_tag_attribute("connection", {"href": None})
                elif protocol.startswith("rtmp"):
                    Logger.warning("Ignoring RTMP for now")
                    continue
                else:
                    Logger.warning("Unknown protocol: %s", protocol)
                    continue

                part.append_media_stream(url, bitrate)

        # get the subtitle
        subtitles = Regexer.do_regex(
            '<connection href="(http://www.bbc.co.uk/iplayer/subtitles/[^"]+/)([^/]+.xml)"',
            stream_data)
        if len(subtitles) > 0:
            subtitle = subtitles[0]
            subtitle_url = "%s%s" % (subtitle[0], subtitle[1])
            part.Subtitle = subtitlehelper.SubtitleHelper.download_subtitle(
                subtitle_url, subtitle[1], "ttml", proxy=self.proxy)

        item.complete = True
        Logger.trace('finishing update_video_item: %s.', item)
        return item

    def add_live_channels(self, data):
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

        Logger.info("Generating Live channels")

        live_channels = [
            {"name": "BBC 1 HD", "code": "bbc_one_hd", "image": "bbc1large.png"},
            {"name": "BBC 2 HD", "code": "bbc_two_hd", "image": "bbc2large.png"},
            {"name": "BBC 3 HD", "code": "bbc_three_hd", "image": "bbc3large.png"},
            {"name": "BBC 4 HD", "code": "bbc_four_hd", "image": "bbc4large.png"},
            {"name": "CBBC", "code": "cbbc_hd", "image": "cbbclarge.png"},
            {"name": "CBeebies", "code": "cbeebies_hd", "image": "cbeebieslarge.png"},
            {"name": "BBC News Channel", "code": "bbc_news24", "image": "bbcnewslarge.png"},
            {"name": "BBC Parliament", "code": "bbc_parliament", "image": "bbcparliamentlarge.png"},
            {"name": "Alba", "code": "bbc_alba", "image": "bbcalbalarge.png"},

            {"name": "S4C", "code": "s4cpbs", "image": "bbchdlarge.png"},
            {"name": "BBC One London", "code": "bbc_one_london", "image": "bbchdlarge.png"},
            {"name": "BBC One Scotland", "code": "bbc_one_scotland_hd", "image": "bbchdlarge.png"},
            {"name": "BBC One Northern Ireland", "code": "bbc_one_northern_ireland_hd", "image": "bbchdlarge.png"},
            {"name": "BBC One Wales", "code": "bbc_one_wales_hd", "image": "bbchdlarge.png"},
            {"name": "BBC Two Scotland", "code": "bbc_two_scotland", "image": "bbchdlarge.png"},
            {"name": "BBC Two Northern Ireland", "code": "bbc_two_northern_ireland_digital", "image": "bbchdlarge.png"},
            {"name": "BBC Two Wales", "code": "bbc_two_wales_digital", "image": "bbchdlarge.png"},
        ]

        live = MediaItem("Live Channels", "")
        live.dontGroup = True
        live.type = "folder"

        for channel in live_channels:
            url = "http://a.files.bbci.co.uk/media/live/manifesto/audio_video/simulcast/hds/uk/pc/ak/%(code)s.f4m" % channel
            item = MediaItem(channel["name"], url)
            item.isGeoLocked = True
            item.isLive = True
            item.type = "video"
            item.complete = False
            item.thumb = self.get_image_location(channel["image"])
            live.items.append(item)

        return data, [live, ]

    def update_live_item(self, item):
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

        Logger.debug('Starting update_live_item for %s (%s)', item.name, self.channelName)
        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=self.httpHeaders)
        stream_root = Regexer.do_regex(r'<media href="([^"]+\.isml)', data)[0]
        Logger.debug("Found Live stream root: %s", stream_root)

        part = item.create_new_empty_media_part()
        for s, b in F4m.get_streams_from_f4m(item.url, self.proxy):
            item.complete = True
            s = s.replace(".f4m", ".m3u8")
            part.append_media_stream(s, b)

        return item

    def __get_date(self, date):
        # actual_start=2014-12-07T10:03:56+0000
        date_part, time_part = date.split("T")
        year, month, day = date_part.split("-")
        hour, minute, ignore = time_part.split(":")
        # Logger.Trace((year, month, day, hour, minute, 0))
        return year, month, day, hour, minute, 0
