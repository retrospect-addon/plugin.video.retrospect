import mediaitem
# import contextmenu
import chn_class

from logger import Logger
from parserdata import ParserData
from urihandler import UriHandler
from regexer import Regexer
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.datehelper import DateHelper


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
        self.noImage = "mtvnlimage.png"

        # setup the urls
        self.__backgroundServiceEp = None
        self.__region = None
        if self.channelCode == "mtvnl":
            # self.mainListUri = "http://api.mtvnn.com/v2/site/m79obhheh2/nl/franchises.json?per=2147483647"
            # Configuration on: http://api.playplex.viacom.com/feeds/networkapp/intl/main/1.5?key=networkapp1.0&brand=mtv&platform=android&region=NL&version=2.2
            # Main screens: http://api.playplex.viacom.com/feeds/networkapp/intl/screen/1.5/mgid:arc:page:mtv.nl:aec18556-7dbb-4ac4-a1f7-90e17fa2e069?key=networkapp1.0&brand=mtv&platform=android&region=NL&version=2.2&region=NL&mvpd=
            self.mainListUri = "http://api.playplex.viacom.com/feeds/networkapp/intl/promolist/1.5/" \
                               "mgid:arc:promotion:mtv.nl:0b8e68bb-8477-4eee-940f-6caa86e01960?" \
                               "key=networkapp1.0&" \
                               "brand=mtv&" \
                               "platform=android&" \
                               "region=NL&" \
                               "version=2.2&" \
                               "mvpd="
            self.baseUrl = "http://www.mtv.nl"
            self.__backgroundServiceEp = "1b5b03c4"
            self.__region = "NL"

        elif self.channelCode == "mtvde":
            # self.mainListUri = "http://api.mtvnn.com/v2/site/va7rcfymx4/de/franchises.json?per=2147483647"
            # http://api.playplex.viacom.com/feeds/networkapp/intl/main/1.5?key=networkapp1.0&
            # brand=mtv&platform=android&region=DE&version=2.2
            self.mainListUri = "http://api.playplex.viacom.com/feeds/networkapp/intl/promolist/1.5/" \
                               "mgid:arc:promotion:mtv.de:0af488a0-6610-4e25-8483-25e3039b19d3?" \
                               "key=networkapp1.0&" \
                               "brand=mtv&" \
                               "platform=android&" \
                               "region=DE&" \
                               "version=2.2&" \
                               "mvpd="
            self.baseUrl = "http://www.mtv.de"
            self.__backgroundServiceEp = "e6bfc4ca"
            self.__region = "DE"

        self.swfUrl = "http://media.mtvnservices.com/player/prime/mediaplayerprime.2.11.4.swf"

        self._add_data_parser("http://api.playplex.viacom.com/feeds/networkapp/intl/promolist/1.5/",
                              name="Main show listing PlayPlay API", json=True,
                              parser=["data", "items"], creator=self.create_episode_item)

        self._add_data_parser("http://api.playplex.viacom.com/feeds/networkapp/intl/series/items",
                              name="Main video listing PlayPlay API", json=True,
                              parser=["data", "items"], creator=self.create_video_item)

        # Old API
        self._add_data_parser("http://api.mtvnn.com/v2/site/[^/]+/\w+/franchises.json",
                              match_type=ParserData.MatchRegex,
                              name="V2 API show listing", json=True,
                              parser=[], creator=self.CreateEpisodeItemJson)
        self._add_data_parser("http://api.mtvnn.com/v2/site/[^/]+/\w+/episodes.json",
                              match_type=ParserData.MatchRegex,
                              name="V2 API video listing", json=True,
                              parser=[], creator=self.CreateVideoItemJson)

        self._add_data_parser("*", updater=self.update_video_item)

        # # setup the main parsing data
        # if "json" in self.mainListUri:
        #     Logger.Debug("Doing a JSON version of MTV")
        #     self.episodeItemJson = ()
        #     self.videoItemJson = ()
        #     self.create_episode_item = self.CreateEpisodeItemJson
        #     self.create_video_item = self.CreateVideoItemJson
        # else:
        #     Logger.Debug("Doing a HTML version of MTV")
        #     self.episodeItemRegex = '<a href="/(shows/[^"]+)" title="([^"]+)"><img [^>]+src="([^"]+)"'  # used for the ParseMainList
        #     self.videoItemRegex = '<a href="([^"]+)" title="([^"]+)">(?:<span class=\Wepisode_number\W>(\d+)</span>){0,1}[\w\W]{0,100}?<img[^>]+src="([^"]+)"[^>]+\W+</a>'
        #     self.folderItemRegex = '<li>\W+<a href="/(seizoen/[^"]+)">([^<]+)</a>'

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def create_episode_item(self, resultSet):
        Logger.trace(resultSet)

        title = resultSet["title"]
        # id = resultSet["id"]
        url = "http://api.playplex.viacom.com/feeds/networkapp/intl/series/items/1.5/%s" \
              "?key=networkapp1.0&brand=mtv&platform=android&region=%s&version=2.2" % \
              (resultSet["id"], self.__region)
        # url = "http://api.playplex.viacom.com/feeds/networkapp/intl/series/clips/1.5/%(id)s" \
        #       "?key=networkapp1.0&brand=mtv&platform=android&region=NL&version=2.2" % resultSet
        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.description = resultSet.get("description", None)
        item.complete = True

        images = resultSet.get("images", [])
        if images:
            #  mgid:file:gsp:scenic:/international/mtv.nl/playplex/dutch-ridiculousness/Dutch_Ridiculousness_Landscape.png
            # http://playplex.mtvnimages.com/uri/mgid:file:gsp:scenic:/international/mtv.nl/playplex/dutch-ridiculousness/Dutch_Ridiculousness_Landscape.png
            for image in images:
                if image["width"] > 500:
                    item.fanart = "http://playplex.mtvnimages.com/uri/%(url)s" % image
                else:
                    item.thumb = "http://playplex.mtvnimages.com/uri/%(url)s" % image

        return item

    def create_video_item(self, resultSet):
        Logger.trace(resultSet)

        title = resultSet["title"]
        if "subTitle" in resultSet:
            title = "%s - %s" % (title, resultSet["subTitle"])
        mgid = resultSet["id"].split(":")[-1]
        url = "http://feeds.mtvnservices.com/od/feed/intl-mrss-player-feed" \
              "?mgid=mgid:arc:episode:mtvplay.com:%s" \
              "&ep=%s" \
              "&episodeType=segmented" \
              "&imageEp=android.playplex.mtv.%s" \
              "&arcEp=android.playplex.mtv.%s" \
              % (mgid, self.__backgroundServiceEp, self.__region.lower(), self.__region.lower())

        item = mediaitem.MediaItem(title, url)
        item.type = "video"
        item.icon = self.icon
        item.description = resultSet.get("description", None)

        item.thumb = self.parentItem.thumb
        item.fanart = self.parentItem.fanart
        item.isGeoLocked = True
        images = resultSet.get("images", [])
        if images:
            # mgid:file:gsp:scenic:/international/mtv.nl/playplex/dutch-ridiculousness/Dutch_Ridiculousness_Landscape.png
            # http://playplex.mtvnimages.com/uri/mgid:file:gsp:scenic:/international/mtv.nl/playplex/dutch-ridiculousness/Dutch_Ridiculousness_Landscape.png
            for image in images:
                if image["width"] > 500:
                    pass  # no fanart here
                else:
                    item.thumb = "http://playplex.mtvnimages.com/uri/%(url)s" % image

        date = resultSet.get("originalAirDate", None)
        if not date:
            date = resultSet.get("originalPublishDate", None)
        if date:
            timeStamp = date["timestamp"]
            dateTime = DateHelper.get_date_from_posix(timeStamp)
            item.set_date(dateTime.year, dateTime.month, dateTime.day, dateTime.hour,
                          dateTime.minute,
                          dateTime.second)

        return item

    def CreateEpisodeItemJson(self, resultSet):
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

        # add  { to make it valid Json again. if it would be in the regex it would
        # not find all items
        # data = JsonHelper("{%s" % (resultSet,))

        # title
        localTitle = resultSet.get("local_title")
        originalTitle = resultSet.get("original_name")
        if localTitle == "" or localTitle is None:
            title = originalTitle
        elif originalTitle != localTitle:
            title = "%s (%s)" % (localTitle, originalTitle)
        else:
            title = localTitle

        # the URL
        serieId = resultSet["id"]
        url = "%sepisodes.json?per=2147483647&franchise_id=%s" % (self.mainListUri[0:43], serieId)

        item = mediaitem.MediaItem(title, url)
        item.icon = self.icon
        item.complete = True

        # thumbs
        if "image" in resultSet and resultSet["image"] is not None:
            thumb = resultSet["image"]["riptide_image_id"]
            thumb = "http://images.mtvnn.com/%s/original" % (thumb,)
            item.thumb = thumb

        # others
        item.description = resultSet["local_long_description"]

        # http://www.mtv.nl/shows/195-16-pregnant
        return item

    def CreateVideoItemJson(self, resultSet):
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
        self.update_video_item method is called if the item is focussed or selected
        for playback.

        """

        Logger.trace(resultSet)

        # get the title
        originalTitle = resultSet.get("original_title")
        localTitle = resultSet.get("local_title")
        # Logger.Trace("%s - %s", originalTitle, localTitle)
        if originalTitle == "":
            title = localTitle
        else:
            title = originalTitle

        # get the other meta data
        playLists = resultSet.get("local_playlists", [])
        videoMgid = None
        for playList in playLists:
            language = playList["language_code"]
            if language == self.language:
                Logger.trace("Found '%s' playlist, using this one.", language)
                videoMgid = playList["id"]
                break
            elif language == "en":
                Logger.trace("Found '%s' instead of '%s' playlist", language, self.language)
                videoMgid = playList["id"]

        if videoMgid is None:
            Logger.error("No video MGID found for: %s", title)
            return None

        url = "http://api.mtvnn.com/v2/mrss.xml?uri=mgid:sensei:video:mtvnn.com:local_playlist-%s" % (videoMgid,)

        thumb = resultSet.get("riptide_image_id")
        thumb = "http://images.mtvnn.com/%s/original" % (thumb,)

        description = resultSet.get("local_long_description")

        date = resultSet.get("published_from")
        date = date[0:10].split("-")

        item = mediaitem.MediaItem(title, url)
        item.thumb = thumb
        item.description = description
        item.icon = self.icon
        item.type = 'video'
        item.set_date(date[0], date[1], date[2])
        item.complete = False
        return item

    def update_video_item(self, item):
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

        Logger.debug('Starting update_video_item for %s (%s)', item.name, self.channelName)

        url = item.url
        data = UriHandler.open(url, proxy=self.proxy)

        renditionsUrl = Regexer.do_regex('<media:content[^>]+url=\W([^\'"]+)\W', data)[0]
        renditionsUrl = HtmlEntityHelper.strip_amp(renditionsUrl)
        renditionData = UriHandler.open(renditionsUrl, proxy=self.proxy)
        videoItems = Regexer.do_regex('<rendition[^>]+bitrate="(\d+)"[^>]*>\W+<src>([^<]+)<', renditionData)

        item.MediaItemParts = []
        part = item.create_new_empty_media_part()
        for videoItem in videoItems:
            mediaUrl = self.get_verifiable_video_url(videoItem[1].replace("rtmpe", "rtmp"))
            part.append_media_stream(mediaUrl, videoItem[0])

        item.complete = True
        return item
