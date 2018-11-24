import mediaitem
import chn_class
from helpers import datehelper
from helpers.languagehelper import LanguageHelper
from logger import Logger
from streams.npostream import NpoStream
from urihandler import UriHandler
from regexer import Regexer
from helpers.jsonhelper import JsonHelper


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
        self.noImage = "l1image.png"

        # setup the urls
        self.mainListUri = "https://l1.nl/gemist/"
        self.baseUrl = "https://l1.nl"

        # setup the main parsing data
        episodeRegex = '<li>\W*<a[^>]*href="(?<url>/[^"]+)"[^>]*>(?<title>[^<]+)</a>\W*</li>'
        episodeRegex = Regexer.from_expresso(episodeRegex)
        self._add_data_parser(self.mainListUri, preprocessor=self.pre_process_folder_list,
                              parser=episodeRegex, creator=self.create_episode_item)

        # live stuff
        self._add_data_parsers(["#livetv", "#liveradio"], updater=self.UpdateLiveStream)

        videoRegex = '<a[^>]*class="mediaItem"[^>]*href="(?<url>[^"]+)"[^>]*title="(?<title>' \
                     '[^"]+)"[^>]*>[\w\W]{0,500}?<img[^>]+src="/(?<thumburl>[^"]+)'
        videoRegex = Regexer.from_expresso(videoRegex)
        self._add_data_parser("*", parser=videoRegex, creator=self.create_video_item, updater=self.update_video_item)

        pageRegex = '<a[^>]+href="https?://l1.nl/([^"]+?pagina=)(\d+)"'
        pageRegex = Regexer.from_expresso(pageRegex)
        self.pageNavigationRegexIndex = 1
        self._add_data_parser("*", parser=pageRegex, creator=self.create_page_item)
        # self.episodeItemRegex = '<a href="(http://www.l1.nl/programma/[^"]+)">([^<]+)'  # used for the ParseMainList
        # self.videoItemRegex = '(:?<a href="/video/[^"]+"[^>]+><img src="([^"]+)"[^>]+>[\w\W]{0,200}){0,1}<a href="(/video/[^"]+-(\d{1,2})-(\w{3})-(\d{4})[^"]*|/video/[^"]+)"[^>]*>([^>]+)</a>'

        #===============================================================================================================
        # non standard items

        #===============================================================================================================
        # Test cases:

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def pre_process_folder_list(self, data):
        """Performs pre-process actions for data processing/

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        Accepts an data from the process_folder_list method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """

        Logger.info("Performing Pre-Processing")
        items = []

        if '>Populair<' in data:
            data = data[data.index('>Populair<'):]
        if '>L1-kanalen<' in data:
            data = data[:data.index('>L1-kanalen<')]

        Logger.debug("Pre-Processing finished")

        # add live items
        title = LanguageHelper.get_localized_string(LanguageHelper.LiveStreamTitleId)
        item = mediaitem.MediaItem("\a.: {} :.".format(title), "")
        item.type = "folder"
        items.append(item)

        liveItem = mediaitem.MediaItem("L1VE TV".format(title), "#livetv")
        liveItem.type = "video"
        liveItem.isLive = True
        item.items.append(liveItem)

        liveItem = mediaitem.MediaItem("L1VE Radio".format(title), "#liveradio")
        liveItem.type = "video"
        liveItem.isLive = True
        item.items.append(liveItem)

        return data, items

    def create_episode_item(self, resultSet):
        """ We need to exclude L1 Gemist """

        item = chn_class.Channel.create_episode_item(self, resultSet)
        if "L1 Gemist" in item.name:
            return None
        return item

    def create_video_item(self, resultSet):
        item = chn_class.Channel.create_video_item(self, resultSet)
        if not item.thumb.startswith("http"):
            item.thumb = "%s/%s" % (self.baseUrl, item.thumb)
        return item

    def CreateVideoItem_old(self, resultSet):
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

        thumbUrl = resultSet[1]
        url = "%s%s" % (self.baseUrl, resultSet[2])
        title = resultSet[6]

        item = mediaitem.MediaItem(title, url)
        item.thumb = self.noImage
        if thumbUrl:
            item.thumb = thumbUrl
        item.icon = self.icon
        item.type = 'video'

        if resultSet[3]:
            # set date
            day = resultSet[3]
            month = resultSet[4]
            year = resultSet[5]
            Logger.trace("%s-%s-%s", year, month, day)
            month = datehelper.DateHelper.get_month_from_name(month, "nl", True)
            item.set_date(year, month, day)

        item.complete = False
        return item

    def UpdateLiveStream(self, item):
        if item.url == "#livetv":
            episodeId = "LI_L1_716599"
            # url = "https://ida.omroep.nl/app.php/LI_L1_716599?adaptive=yes&token={}"
        else:
            episodeId = "LI_L1_716685"
            # url = "https://ida.omroep.nl/app.php/LI_L1_716685?adaptive=yes&token={}"

        part = item.create_new_empty_media_part()
        for s, b in NpoStream.get_streams_from_npo(None, episode_id=episodeId, proxy=self.proxy):
            item.complete = True
            # s = self.get_verifiable_video_url(s)
            part.append_media_stream(s, b)

        return item

    def update_video_item(self, item):
        """
        Accepts an item. It returns an updated item. Usually retrieves the MediaURL
        and the Thumb! It should return a completed item.
        """
        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        data = UriHandler.open(item.url, proxy=self.proxy)
        javascriptUrls = Regexer.do_regex('<script type="text/javascript" src="(//l1.bbvms.com/p/\w+/c/\d+.js)"', data)
        dataUrl = None
        for javascriptUrl in javascriptUrls:
            dataUrl = javascriptUrl
            if not dataUrl.startswith("http"):
                dataUrl = "https:%s" % (dataUrl, )

        if not dataUrl:
            return item

        data = UriHandler.open(dataUrl, proxy=self.proxy)
        jsonData = Regexer.do_regex('clipData\W*:([\w\W]{0,10000}?\}),"playerWidth', data)
        Logger.trace(jsonData)
        json = JsonHelper(jsonData[0], logger=Logger.instance())
        Logger.trace(json)

        streams = json.get_value("assets")
        item.MediaItemParts = []
        part = item.create_new_empty_media_part()
        for stream in streams:
            url = stream.get("src", None)
            if "://" not in url:
                url = "http://static.l1.nl/bbw%s" % (url, )
            bitrate = stream.get("bandwidth", None)
            if url:
                part.append_media_stream(url, bitrate)

        if not item.thumb and json.get_value("thumbnails"):
            url = json.get_value("thumbnails")[0].get("src", None)
            if url and "http:/" not in url:
                url = "%s%s" % (self.baseUrl, url)
            item.thumb = url
        item.complete = True
        return item
