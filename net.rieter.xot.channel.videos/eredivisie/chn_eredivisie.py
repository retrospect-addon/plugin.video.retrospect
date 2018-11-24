import mediaitem
import chn_class

from logger import Logger
from addonsettings import AddonSettings
# from streams.m3u8 import M3u8
from streams.mpd import Mpd
from regexer import Regexer
from helpers.jsonhelper import JsonHelper
from urihandler import UriHandler
from helpers.languagehelper import LanguageHelper
from xbmcwrapper import XbmcWrapper


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
        self.videoType = None
        self.noImage = "eredivisieimage.jpg"

        # setup the urls
        self.baseUrl = "https://www.foxsports.nl"
        self.mainListUri = "https://www.foxsports.nl/videos/"
        self.swfUrl = "https://static.eredivisielive.nl/static/swf/edPlayer-1.6.2.plus.swf"

        # setup the main parsing data
        # self.episodeItemRegex = '<option[^>]+value="([^"]+)"[^=>]+(?:data-season="([^"]+)")?[^=>]*>([^<]+)</option>'
        # self.videoItemJson = ("item",)
        self._add_data_parser(
            self.mainListUri,
            parser=Regexer.from_expresso('<a [hd][^>]*ata-(?<Type>area|sport)="(?<Url>[^"]+)[^>]*>'
                                         '(?<Title>[^<]+)</a>'),
            creator=self.create_folder_item
        )

        self._add_data_parser(
            self.mainListUri,
            parser=Regexer.from_expresso('<a[^>]+href="/video/(?<Type>filter|meest_bekeken)/?'
                                         '(?<Url>[^"]*)">[^<]*</a>\W+<h1[^>]*>(?<Title>[^<;]+)'
                                         '(?:&#39;s){0,1}</h1>'),
            creator=self.create_folder_item
        )

        self._add_data_parser(
            "https://www.foxsports.nl/video/filter/fragments/",
            preprocessor=self.AddPages,
            parser=Regexer.from_expresso('<img[^>]+src=\'(?<Thumb>[^\']+)\'[^>]*>\W+</picture>\W+'
                                         '<span class="[^"]+play[\w\W]{0,500}?<h1[^>]*>\W+<a href="'
                                         '(?<Url>[^"]+)"[^>]*>(?<Title>[^<]+)</a>\W+</h1>\W+<span'
                                         '[^>]*>(?<Date>[^>]+)</span>'),
            creator=self.create_video_item
        )

        self._add_data_parser("*", updater=self.update_video_item)

        # ====================================== Actual channel setup STOPS here =======================================
        return

    def AddPages(self, data):
        """Performs pre-process actions for data processing

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

        Logger.info("Adding pages")

        # extract the current page from:
        # http://www.foxsports.nl/video/filter/fragments/1/alle/tennis/
        currentPages = Regexer.do_regex('(.+filter/fragments)/(\d+)/(.+)', self.parentItem.url)
        if not currentPages:
            return data, []

        currentPage = currentPages[0]
        items = []

        url = "%s/%s/%s" % (currentPage[0], int(currentPage[1]) + 1, currentPage[2])
        pageItem = mediaitem.MediaItem(LanguageHelper.get_localized_string(LanguageHelper.MorePages), url)
        pageItem.fanart = self.parentItem.fanart
        pageItem.thumb = self.parentItem.thumb
        pageItem.dontGroup = True
        items.append(pageItem)

        return data, items

    def create_folder_item(self, resultSet):
        """Creates a MediaItem of type 'folder' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(strig) - the resultSet of the self.folderItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.trace(resultSet)

        if resultSet["Type"] == "sport":
            # http://www.foxsports.nl/video/filter/alle/tennis/
            url = "%s/video/filter/fragments/1/alle/%s/" % (self.baseUrl, resultSet["Url"])
        elif resultSet["Type"] == "meest_bekeken":
            url = "%s/video/filter/fragments/1/meer" % (self.baseUrl, )
        else:
            # http://www.foxsports.nl/video/filter/samenvattingen/
            url = "%s/video/filter/fragments/1/%s/" % (self.baseUrl, resultSet["Url"])

        title = resultSet["Title"]
        if not title[0].isupper():
            title = "%s%s" % (title[0].upper(), title[1:])
        item = mediaitem.MediaItem(title, url)
        item.complete = True
        item.thumb = self.noImage
        item.fanart = self.fanart
        return item

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

        url = "%s%s" % (self.baseUrl, resultSet["Url"])
        item = mediaitem.MediaItem(resultSet["Title"], url)
        item.type = "video"
        item.thumb = resultSet["Thumb"]
        item.complete = False
        if self.parentItem is None:
            item.fanart = self.fanart
        else:
            item.fanart = self.parentItem.fanart
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

        if not AddonSettings.use_adaptive_stream_add_on(with_encryption=False):
            Logger.error("Cannot playback video without adaptive stream addon")
            return item

        # https://www.foxsports.nl/api/video/videodata/2945190
        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=item.HttpHeaders)
        videoId = Regexer.do_regex('data-videoid="(\d+)" ', data)[-1]
        data = UriHandler.open("https://www.foxsports.nl/api/video/videodata/%s" % (videoId,),
                               proxy=self.proxy, additional_headers=item.HttpHeaders, no_cache=True)
        streamId = Regexer.do_regex('<uri>([^>]+)</uri>', data)[-1]

        # POST https://d3api.foxsports.nl/api/V2/entitlement/tokenize
        postData = {
          "Type": 1,
          "User": "",
          "VideoId": "{0}".format(videoId),
          "VideoSource": "{0}".format(streamId),
          "VideoKind": "vod",
          "AssetState": "3",
          "PlayerType": "HTML5",
          "VideoSourceFormat": "DASH",
          "VideoSourceName": "DASH",
          # "VideoSourceFormat": "HLS",
          # "VideoSourceName": "HLS",
          "DRMType": "widevine",
          "AuthType": "Token",
          "ContentKeyData": "",
          "Other__": "playerName=HTML5-Web-vod|ae755267-8482-455b-9055-529b643ece1d|undefined|undefined|undefined|2945541|HTML5|web|diva.MajorVersion=4|diva.MinorVersion=2|diva.PatchVersion=13"
        }

        data = UriHandler.open("https://d3api.foxsports.nl/api/V2/entitlement/tokenize",
                               json=postData, no_cache=True, proxy=self.proxy)
        streamInfo = JsonHelper(data)
        streamUrl = streamInfo.get_value("ContentUrl")
        if not streamUrl:
            message = "Protected stream: {0}".format(streamInfo.get_value("Message"))
            XbmcWrapper.show_notification(None, message,
                                          notification_type=XbmcWrapper.Error, display_time=5000)

        licenseUrl = streamInfo.get_value("LicenseURL")
        part = item.create_new_empty_media_part()
        stream = part.append_media_stream(streamUrl, 0)
        licenseKey = Mpd.get_license_key(licenseUrl)
        Mpd.set_input_stream_addon_input(stream, proxy=self.proxy, license_key=licenseKey)
        return item
