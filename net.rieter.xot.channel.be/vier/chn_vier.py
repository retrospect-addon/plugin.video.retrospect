import chn_class
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.jsonhelper import JsonHelper
from mediaitem import MediaItem
from logger import Logger
from regexer import Regexer
from urihandler import UriHandler
from parserdata import ParserData
from streams.m3u8 import M3u8
from helpers.datehelper import DateHelper
from addonsettings import AddonSettings
from xbmcwrapper import XbmcWrapper
from helpers.languagehelper import LanguageHelper
from awsidp import AwsIdp
from vault import Vault


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

        # setup the main parsing data
        if self.channelCode == "vijfbe":
            self.noImage = "vijfimage.png"
            self.mainListUri = "https://www.vijf.be/programmas"
            self.baseUrl = "https://www.vijf.be"
        # elif self.channelCode == "zesbe":
        #     self.noImage = "zesimage.png"
        #     self.mainListUri = "https://www.zestv.be/programmas"
        #     self.baseUrl = "https://www.zestv.be"
        else:
            self.noImage = "vierimage.png"
            self.mainListUri = "https://www.vier.be/programmas"
            self.baseUrl = "https://www.vier.be"

        episodeRegex = '<a class="program-overview__link" href="(?<url>[^"]+)">(?<title>[^<]+)</a>'
        episodeRegex = Regexer.from_expresso(episodeRegex)
        self._add_data_parser(self.mainListUri, match_type=ParserData.MatchExact,
                              parser=episodeRegex,
                              creator=self.create_episode_item)

        videoRegex = '<a(?:[^>]+data-background-image="(?<thumburl>[^"]+)")?[^>]+href="(?<url>/video/[^"]+)"[^>]*>(?:\s+<div[^>]+>\s+<div [^>]+data-background-image="(?<thumburl2>[^"]+)")?[\w\W]{0,1000}?<h3[^>]*>(?:<span>)?(?<title>[^<]+)(?:</span>)?</h3>(?:\s+(?:<div[^>]*>\s+)?<div[^>]*>[^<]+</div>\s+<div[^>]+data-timestamp="(?<timestamp>\d+)")?'
        videoRegex = Regexer.from_expresso(videoRegex)
        self._add_data_parser("*", match_type=ParserData.MatchExact,
                              name="Normal video items",
                              parser=videoRegex,
                              creator=self.create_video_item)

        pageRegex = '<button class="button button--default js-load-more-button"\W+data-url="(?<url>[^"]+)"\W+data-page="(?<title>\d+)"'
        pageRegex = Regexer.from_expresso(pageRegex)
        self._add_data_parser("*", match_type=ParserData.MatchExact,
                              parser=pageRegex,
                              creator=self.create_page_item)

        self._add_data_parser("/api/program/fixed/", name="API paging",
                              match_type=ParserData.MatchContains,
                              # json=False,
                              preprocessor=self.ExtractPageData,
                              parser=videoRegex,
                              creator=self.create_video_item)

        # imageVideoRegex = '<a[^>]+url\((?<thumburl>[^)]+)[^>]+href="(?<url>/video/[^"]+)"[\w\W]{500,2000}<h3[^>]+>(?<title>[^<]+)</h3>\W*<div[^>]*>(?<description>[^<]+)(?:</div>\W*<div[^>]*>\W*)?<div[^>]+data-videoid="(?<videoid>[^"]+)"'
        # imageVideoRegex = Regexer.from_expresso(imageVideoRegex)
        # self._add_data_parser("*", matchType=ParserData.MatchExact,
        #                     parser=imageVideoRegex,
        #                     creator=self.create_video_item)

        # Generic updater with login
        self._add_data_parser("*",
                              # requiresLogon=True,
                              updater=self.update_video_item)

        # ==========================================================================================
        # Channel specific stuff
        self.__idToken = None

        # ==========================================================================================
        # Test cases:
        # Documentaire: pages (has http://www.canvas.be/tag/.... url)
        # Not-Geo locked: Kroost

        # ====================================== Actual channel setup STOPS here ===================
        return

    def log_on(self):
        if self.__idToken:
            return True

        # check if there is a refresh token
        # refresh token: viervijfzes_refresh_token
        refreshToken = AddonSettings.get_setting("viervijfzes_refresh_token")
        client = AwsIdp("eu-west-1_dViSsKM5Y", "6s1h851s8uplco5h6mqh1jac8m",
                        proxy=self.proxy, logger=Logger.instance())
        if refreshToken:
            idToken = client.RenewToken(refreshToken)
            if idToken:
                self.__idToken = idToken
                return True
            else:
                Logger.info("Extending token for VierVijfZes failed.")

        # username: viervijfzes_username
        username = AddonSettings.get_setting("viervijfzes_username")
        # password: viervijfzes_password
        v = Vault()
        password = v.get_setting("viervijfzes_password")
        if not username or not password:
            XbmcWrapper.show_dialog(
                title=None,
                lines=LanguageHelper.get_localized_string(LanguageHelper.MissingCredentials),
            )
            return False

        idToken, refreshToken = client.Authenticate(username, password)
        if not idToken or not refreshToken:
            Logger.error("Error getting a new token. Wrong password?")
            return False

        self.__idToken = idToken
        AddonSettings.set_setting("viervijfzes_refresh_token", refreshToken)
        return True

    def create_episode_item(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        item = chn_class.Channel.create_episode_item(self, resultSet)
        if item is None:
            return item

        # All of vier.be video's seem GEO locked.
        item.isGeoLocked = True
        item.thumb = item.thumb or self.noImage
        return item

    def create_page_item(self, resultSet):
        resultSet["url"] = "{0}/{1}".format(resultSet["url"], resultSet["title"])
        resultSet["title"] = str(int(resultSet["title"]) + 1)

        item = self.create_folder_item(resultSet)
        item.type = "page"
        return item

    def ExtractPageData(self, data):
        items = []
        json = JsonHelper(data)
        data = json.get_value("data")
        Logger.trace(data)

        if json.get_value("loadMore", fallback=False):
            url, page = self.parentItem.url.rsplit("/", 1)
            url = "{0}/{1}".format(url, int(page) + 1)
            pageItem = MediaItem("{0}".format(int(page) + 2), url)
            pageItem.type = "page"
            items.append(pageItem)
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

        item = chn_class.Channel.create_video_item(self, resultSet)

        # All of vier.be video's seem GEO locked.
        item.isGeoLocked = True

        # Set the correct url
        # videoId = resultSet["videoid"]
        # item.url = "https://api.viervijfzes.be/content/%s" % (videoId, )
        time_stamp = resultSet.get("timestamp")
        if time_stamp:
            dateTime = DateHelper.get_date_from_posix(int(resultSet["timestamp"]))
            item.set_date(dateTime.year, dateTime.month, dateTime.day, dateTime.hour,
                          dateTime.minute,
                          dateTime.second)

        if not item.thumb and "thumburl2" in resultSet and resultSet["thumburl2"]:
            item.thumb = resultSet["thumburl2"]

        if item.thumb and item.thumb != self.noImage:
            item.thumb = HtmlEntityHelper.strip_amp(item.thumb)
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

        # https://api.viervijfzes.be/content/c58996a6-9e3d-4195-9ecf-9931194c00bf
        # videoId = item.url.split("/")[-1]
        # url = "%s/video/v3/embed/%s" % (self.baseUrl, videoId,)
        url = item.url
        data = UriHandler.open(url, proxy=self.proxy)
        return self.__UpdateVideo(item, data)

    def __UpdateVideo(self, item, data):
        regex = 'data-file="([^"]+)'
        m3u8Url = Regexer.do_regex(regex, data)[-1]

        if ".m3u8" not in m3u8Url:
            Logger.info("Not a direct M3u8 file. Need to log in")
            url = "https://api.viervijfzes.be/content/%s" % (m3u8Url, )

            # We need to log in
            if not self.loggedOn:
                self.log_on()

            # add authorization header
            authenticationHeader = {
                "authorization": self.__idToken,
                "content-type": "application/json"
            }
            data = UriHandler.open(url, proxy=self.proxy, additional_headers=authenticationHeader)
            jsonData = JsonHelper(data)
            m3u8Url = jsonData.get_value("video", "S")

        # Geo Locked?
        if "geo" in m3u8Url.lower():
            # set it for the error statistics
            item.isGeoLocked = True

        part = item.create_new_empty_media_part()
        for s, b in M3u8.get_streams_from_m3u8(m3u8Url, self.proxy):
            if int(b) < 200:
                Logger.info("Skipping stream of quality '%s' kbps", b)
                continue

            item.complete = True
            # s = self.get_verifiable_video_url(s)
            part.append_media_stream(s, b)

        item.complete = True
        return item
