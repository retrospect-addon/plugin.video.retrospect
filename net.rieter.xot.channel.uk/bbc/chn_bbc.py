# ===============================================================================
# Make global object available
#===============================================================================
import chn_class
import mediaitem
from parserdata import ParserData
from locker import LockWithDialog
from config import Config
from helpers import htmlentityhelper
from helpers.xmlhelper import XmlHelper
from helpers import subtitlehelper
from helpers.jsonhelper import JsonHelper
from xbmcwrapper import XbmcWrapper
from helpers.languagehelper import LanguageHelper

from regexer import Regexer
from logger import Logger
from urihandler import UriHandler


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
        self.liveUrl = None

        # set context menu items
        # self.contextMenuItems.append(contextmenu.ContextMenuItem("Test Proxy Server", "CtMnTestProxy"))

        # setup the urls
        self.baseUrl = "http://www.bbc.co.uk/"
        self.swfUrl = "http://emp.bbci.co.uk/emp/SMPf/1.9.45/StandardMediaPlayerChromelessFlash.swf"

        if self.channelCode == "bbciplayer":
            self.noImage = "bbciplayerimage.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer"

        elif self.channelCode == "bbc1":
            self.noImage = "bbc1image.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/bbc_one/block_type/episode/format/json"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/bbc_one_london/pc_stream_audio_video_simulcast_uk_v_lm_p006"

        elif self.channelCode == "bbc2":
            self.noImage = "bbc2image.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/bbc_two/block_type/episode/format/json"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/bbc_two_england/pc_stream_audio_video_simulcast_uk_v_lm_p006"

        elif self.channelCode == "bbc3":
            self.noImage = "bbc3image.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/bbc_three/block_type/episode/format/json"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/bbc_three/pc_stream_audio_video_simulcast_uk_v_lm_p006"

        elif self.channelCode == "bbc4":
            self.noImage = "bbc4image.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/bbc_four/block_type/episode/format/json"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/bbc_four/pc_stream_audio_video_simulcast_uk_v_lm_p006"

        elif self.channelCode == "cbbc":
            self.noImage = "cbbcimage.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/cbbc/block_type/episode/format/json"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/cbbc/pc_stream_audio_video_simulcast_uk_v_lm_p006"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/bbc_three/pc_stream_audio_video_simulcast_uk_v_lm_p006"

        elif self.channelCode == "cbeebies":
            self.noImage = "cbeebiesimage.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/cbeebies/block_type/episode/format/json"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/cbeebies/pc_stream_audio_video_simulcast_uk_v_lm_p006"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/bbc_four/pc_stream_audio_video_simulcast_uk_v_lm_p006"

        elif self.channelCode == "bbchd":
            self.noImage = "bbchdimage.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/bbc_hd/block_type/episode/format/json"

        elif self.channelCode == "bbcnews":
            self.noImage = "bbcnewsimage.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/bbc_news24/block_type/episode/format/json"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/bbc_news24/pc_stream_audio_video_simulcast_uk_v_lm_p006"

        elif self.channelCode == "bbcparliament":
            self.noImage = "bbcparliamentimage.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/bbc_parliament/block_type/episode/format/json"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/bbc_parliament/pc_stream_audio_video_simulcast_uk_v_lm_p006"

        elif self.channelCode == "bbcalba":
            self.noImage = "bbcalbaimage.png"
            self.mainListUri = "http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/bbc_alba/block_type/episode/format/json"
            # self.liveUrl = "http://www.bbc.co.uk/mediaselector/4/mtis/stream/bbc_alba/pc_stream_audio_video_simulcast_uk_v_lm_p006"

        # elif self.channelCode == "bbciplayersearch":
        #     self.noImage = "bbciplayerimage.png"
        #     self.mainListUri = ""
        else:
            #http://www.bbc.co.uk/iplayer/ion/listview/masterbrand/bbc_three/block_type/episode/format/json
            raise ValueError("No such channelcode", self.channelCode)

        if self.channelCode == "bbciplayer":
            # setup the main parsing data
            self.episodeItemRegex = '<a class="letter stat" href="(?<url>/iplayer/a-z/[^"]+)">(?<title>[^<]+)</a>' \
                .replace("(?<", "(?P<")
            self._AddDataParser("http://www.bbc.co.uk/iplayer", matchType=ParserData.MatchExact,
                                parser=self.episodeItemRegex, creator=self.CreateEpisodeItem)

            self.folderItemRegex = '<a href="(?<url>/iplayer/brand/[^"]+)"[^>]*>\W+<i[^>]+></i>\W+<span[^>]+>' \
                                   '(?<title>[^<]+)<'.replace("(?<", "(?P<")
            self.videoItemRegex = 'data-pid="(?<url>[^"]+)"[^>]*>\W*<div class="image">\W*<img src="(?<thumburl>' \
                                  '[^"]+)"[^>]*>[\w\W]{50,300}<span class="title">(?<title>[^<]+)</span>\W*' \
                                  '<span class="subtitle">(?<subtitle>[^<]+)</span>'.replace("(?<", "(?P<")
            self._AddDataParser("*", preprocessor=self.PreProcessFolderList)
            self._AddDataParser("*",
                                parser=self.folderItemRegex, creator=self.CreateFolderItem)
            self._AddDataParser("*",
                                parser=self.videoItemRegex, creator=self.CreateVideoItem)
        else:
            self._AddDataParser("ion/listview/masterbrand", matchType=ParserData.MatchContains, json=True,
                                parser=("blocklist",), creator=self.CreateJsonEpisode)

        # Generic updater
        self._AddDataParser("*", updater=self.UpdateVideoItem)

        #===============================================================================================================
        # non standard items
        if self.proxy:
            self.proxy.Filter = ["mediaselector"]

        self.searchUrl = "http://feeds.bbc.co.uk/iplayer/search/tv/?q=%s"
        self.programs = dict()

        #===============================================================================================================
        # Test cases:
        # http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/pc/vpid/b04plqyv/atk/

        # ====================================== Actual channel setup STOPS here =======================================
        return

    # noinspection PyUnusedLocal
    @LockWithDialog(logger=Logger.Instance())
    def CtMnTestProxy(self, item):  # :@UnusedVariable
        """ Checks if the proxy is OK"""

        if not self.proxy:
            message = "Proxy not configured: %s" % (self.proxy, )
        else:
            url = Config.UpdateUrl + "proxy"
            data = UriHandler.Open(url, proxy=self.proxy)
            # Logger.Trace(data)
            if data == "1":
                message = LanguageHelper.GetLocalizedString(LanguageHelper.ProxyOkId) % (self.proxy, )
            else:
                message = LanguageHelper.GetLocalizedString(LanguageHelper.ProxyNokId) % (self.proxy, )

        Logger.Debug(message)

        XbmcWrapper.ShowDialog("", message)
        pass

    def CreateJsonEpisode(self, resultSet):
        Logger.Trace(resultSet)

        brandId = resultSet["brand_id"]
        if brandId in self.programs:
            parent = self.programs[brandId]
            child = mediaitem.MediaItem(resultSet["complete_title"], resultSet["my_mediaselector_xml_url"])
            child.description = resultSet["synopsis"]
            child.isGeoLocked = True
            child.type = 'video'
            child.icon = parent.icon
            child.thumb = "%s%s_512_288.jpg" % (resultSet["my_image_base_url"], resultSet["id"])
            child.SetDate(*self.__GetDate(resultSet["actual_start"]))

            # we do this by reference
            parent.items.append(child)
            return None
        else:
            brandTitle = resultSet["brand_title"]
            if brandTitle == "":
                Logger.Warning("Found empty title for: %s", resultSet)
                return None

            parent = mediaitem.MediaItem(brandTitle, "")
            parent.icon = self.icon
            parent.thumb = self.noImage
            parent.isGeoLocked = True

            child = mediaitem.MediaItem(resultSet["complete_title"], resultSet["my_mediaselector_xml_url"])
            child.description = resultSet["synopsis"]
            child.isGeoLocked = True
            child.type = 'video'
            child.icon = parent.icon
            child.thumb = "%s%s_512_288.jpg" % (resultSet["my_image_base_url"], resultSet["id"])
            child.SetDate(*self.__GetDate(resultSet["actual_start"]))
            parent.items.append(child)

            self.programs[brandId] = parent
            return parent

    def CreateEpisodeItem(self, resultSet):
        """Creates a new MediaItem for an episode

        Arguments:
        resultSet : list[string] - the resultSet of the self.episodeItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.Trace(resultSet)
        item = chn_class.Channel.CreateEpisodeItem(self, resultSet)
        if item is not None:
            item.name = "Shows: %s" % (item.name.upper(), )
        return item

    def CreateFolderItem(self, resultSet):
        """Creates a MediaItem of type 'folder' using the resultSet from the regex.

        Arguments:
        resultSet : tuple(strig) - the resultSet of the self.folderItemRegex

        Returns:
        A new MediaItem of type 'folder'

        This method creates a new MediaItem from the Regular Expression or Json
        results <resultSet>. The method should be implemented by derived classes
        and are specific to the channel.

        """

        Logger.Trace(resultSet)

        item = chn_class.Channel.CreateFolderItem(self, resultSet)
        brand = item.url[item.url.rindex("/") + 1:]
        item.url = "http://www.bbc.co.uk/iplayer/pagecomponents/recommendations/episode.json?pid=%s&container=%s" % (
            brand, brand)
        # item.thumb = "http://ichef.bbci.co.uk/images/ic/%sx%s/%s.jpg" % (192 * 2, 108 * 2, brand,)
        item.isGeoLocked = True
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

        item = chn_class.Channel.CreateVideoItem(self, resultSet)
        vid = item.url.replace(self.baseUrl, "")
        item.thumb = item.thumb.replace("192x108", "%sx%s" % (192 * 2, 108 * 2))
        item.url = "http://www.bbc.co.uk/iplayer/episode/%s" % (vid,)
        item.isGeoLocked = True
        # item.url = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/pc/vpid/%s/atk/" % (vid,)
        return item

    def PreProcessFolderList(self, data):
        """Performs pre-process actions for data processing/

        Arguments:
        data : string - the retrieve data that was loaded for the current item and URL.

        Returns:
        A tuple of the data and a list of MediaItems that were generated.


        Accepts an data from the ProcessFolderList method, BEFORE the items are
        processed. Allows setting of parameters (like title etc) for the channel.
        Inside this method the <data> could be changed and additional items can
        be created.

        The return values should always be instantiated in at least ("", []).

        """

        Logger.Info("Performing Pre-Processing")
        items = []

        if "episode.json" in self.parentItem.url:
            Logger.Debug("Fetching Carousel data")
            json = JsonHelper(data)
            data = json.GetValue("carousel")

        Logger.Debug("Pre-Processing finished")
        return data, items

    def UpdateVideoItem(self, item):
        """
        Accepts an item. It returns an updated item.
        """
        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        Logger.Trace(item.url)
        if not item.url.startswith("http://www.bbc.co.uk/mediaselector/"):
            Logger.Debug("Determining the stream URL")
            data = UriHandler.Open(item.url, proxy=self.proxy)
            needle = '"vpid"\W*"([^"]+)"'
            vid = Regexer.DoRegex(needle, data)[-1]
            streamDataUrl = "http://open.live.bbc.co.uk/mediaselector/4/mtis/stream/%s/" % (vid,)
            # streamDataUrl = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/pc/vpid/%s" % (vid,)
        else:
            streamDataUrl = item.url

        # this URL is one from the webbrowser but requires a security part. So NOT:
        # streamDataUrl = "http://open.live.bbc.co.uk/mediaselector/5/select/version
        # /2.0/mediaset/pc/vpid/%s" % (vid,)
        #
        # but:
        # streamDataUrl = "http://open.live.bbc.co.uk/mediaselector/5/select/version
        # /2.0/mediaset/pc/vpid/%s/atk/2214e42b5729dcdd012dfb61a3054d39309ccd31/asn/1/
        # And I don't know where that one comes from

        part = item.CreateNewEmptyMediaPart()

        if True:
            streamData = UriHandler.Open(streamDataUrl, proxy=self.proxy)
        else:
            from debug.router import Router
            streamData = Router.GetVia("uk", streamDataUrl, self.proxy)

        connectionDatas = Regexer.DoRegex(
            '<media bitrate="(\d+)"[^>]+>\W*(<connection[^>]+>)\W*(<connection[^>]+>)*\W*</media>', streamData)
        for connectionData in connectionDatas:
            Logger.Trace(connectionData)
            # first the bitrate
            bitrate = connectionData[0]
            Logger.Debug("Found bitrate       : %s", bitrate)

            # go through the available connections
            for connection in connectionData[1:3]:
                if not connection:
                    continue

                connectionXml = XmlHelper(connection)
                Logger.Debug("Analyzing: %s", connection)

                # port: we take the default one
                # determine protocol
                protocol = connectionXml.GetTagAttribute("connection", {"protocol": None})
                if protocol == "http":
                    Logger.Debug("Http stream found, skipping for now.")
                    continue

                elif protocol == "":
                    protocol = "rtmp"
                Logger.Debug("Found protocol      : %s", protocol)

                # now for the non-http version, we need application, authentication, server, file and kind
                application = connectionXml.GetTagAttribute("connection", {"application": None})
                if application == "":
                    application = "ondemand"
                Logger.Debug("Found application   : %s", application)

                authentication = connectionXml.GetTagAttribute("connection", {"authString": None})
                authentication = htmlentityhelper.HtmlEntityHelper.ConvertHTMLEntities(authentication)
                Logger.Debug("Found authentication: %s", authentication)

                server = connectionXml.GetTagAttribute("connection", {"server": None})
                Logger.Debug("Found server        : %s", server)

                fileName = connectionXml.GetTagAttribute("connection", {"identifier": None})
                Logger.Debug("Found identifier    : %s", fileName)

                kind = connectionXml.GetTagAttribute("connection", {"kind": None})
                Logger.Debug("Found kind          : %s", kind)
                if "akamai" in kind:
                    Logger.Debug("Not including AKAMAI streams")
                    continue
                    #url = "%s://%s/%s?%s playpath=%s?%s" % (protocol, server, application, authentication, fileName, authentication)
                    #Logger.Debug("Creating RTMP for Akamai type\n%s", url)

                # Logger.Trace("XML: %s\nProtocol: %s, Server: %s, Application: %s, Authentication: %s, File: %s , Kind: %s", connection, protocol, server, application, authentication, fileName, kind)
                elif kind == "limelight":
                    # for limelight we need to be more specific on what to play
                    url = "%s://%s/ app=%s?%s tcurl=%s://%s/%s?%s playpath=%s" % (
                        protocol, server, application, authentication, protocol, server, application, authentication,
                        fileName)
                    Logger.Debug("Creating RTMP for LimeLight type\n%s", url)
                else:
                    # for a none-limelight we just compose a RTMP stream
                    url = "%s://%s/%s?%s playpath=%s" % (protocol, server, application, authentication, fileName)
                    Logger.Debug("Creating RTMP for a None-LimeLight type\n%s", url)
                url = self.GetVerifiableVideoUrl(url)

                # if liveStream:
                #     url = "%s live=1" % (url, )
                part.AppendMediaStream(url, bitrate)

        # get the subtitle
        subtitles = Regexer.DoRegex('<connection href="(http://www.bbc.co.uk/iplayer/subtitles/[^"]+/)([^/]+.xml)"',
                                    streamData)
        if len(subtitles) > 0:
            subtitle = subtitles[0]
            subtitleUrl = "%s%s" % (subtitle[0], subtitle[1])
            part.Subtitle = subtitlehelper.SubtitleHelper.DownloadSubtitle(subtitleUrl, subtitle[1], "ttml",
                                                                           proxy=self.proxy)

        item.complete = True
        Logger.Trace('finishing UpdateVideoItem: %s.', item)
        return item

    def __GetDate(self, date):
        # actual_start=2014-12-07T10:03:56+0000
        datePart, timePart = date.split("T")
        year, month, day = datePart.split("-")
        hour, minute, ignore = timePart.split(":")
        # Logger.Trace((year, month, day, hour, minute, 0))
        return year, month, day, hour, minute, 0