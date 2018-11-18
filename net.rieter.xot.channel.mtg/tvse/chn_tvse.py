# coding:UTF-8
import chn_class
# import proxyinfo

import mediaitem
from logger import Logger
from regexer import Regexer
from urihandler import UriHandler
from parserdata import ParserData
from addonsettings import AddonSettings
from streams.m3u8 import M3u8


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
        # The following data was taken from http://playapi.mtgx.tv/v3/channels
        self.channelIds = None
        self.mainListUri = None

        # The LV channels
        if self.channelCode == "tv3lv":
            self.noImage = "tv3lvimage.png"
            # self.mainListUri = "https://tvplay.skaties.lv/seriali/tv3/"
            self.mainListUri = "https://tvplay.skaties.lv/seriali/"
            self.channelIds = (
                1482,  # TV3
                6400,  # LNT
                6401,  # TV6
                6402,  # TV5
                6403,  # Kanals2
                6404,  # TVPlay
                6405   # 3+
            )

        # EE channels
        elif self.channelCode == "tv3ee":
            self.mainListUri = "https://tvplay.tv3.ee/saated/tv3/"
            self.noImage = "tv3noimage.png"
            self.channelId = (1375, 6301, 6302)

        elif self.channelCode == "tv6ee":
            self.mainListUri = "https://tvplay.tv3.ee/saated/tv6/"
            self.noImage = "tv6seimage.png"
            self.channelId = (6300, )

        # Lithuanian channels
        elif self.channelCode == "tv3lt":
            self.mainListUri = "https://tvplay.tv3.lt/pramogines-laidos/tv3/"
            self.noImage = "tv3ltimage.png"
            self.channelId = (3000, 6503)

        elif self.channelCode == "tv6lt":
            self.mainListUri = "https://tvplay.tv3.lt/pramogines-laidos/tv6/"
            self.noImage = "tv6ltimage.png"
            self.channelId = (6501, )

        elif self.channelCode == "tv8lt":
            self.mainListUri = "https://tvplay.tv3.lt/pramogines-laidos/tv8/"
            self.noImage = "tv8seimage.png"
            self.channelId = (6502, )

        else:
            raise ValueError("Unknown channelcode {0}".format(self.channelCode))

        self.episodeItemRegex = '<a[^>*]+href="(?<url>[^"]+)"[^>]*>\W+<img[^>]+data-srcset="[^"]*' \
                                '(?<thumburl>http[^" ]+)[^"]+"[^>]+alt="(?<title>[^"]+)"'
        self.videoItemRegex = '{0}[\w\W]{{0,1000}}?site-thumb-info[^>]+>(?<description>[^<]+)'. \
            format(self.episodeItemRegex)

        self.folderItemRegex = '<option value="(?<url>[^"]+)"\W*>(?<title>[^<]+)</option>'

        self.episodeItemRegex = Regexer.from_expresso(self.episodeItemRegex)
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            preprocessor=self.AddSearch,
                            parser=self.episodeItemRegex, creator=self.CreateEpisodeItem)

        self.videoItemRegex = Regexer.from_expresso(self.videoItemRegex)
        self._AddDataParser("*", preprocessor=self.RemoveClips,
                            parser=self.videoItemRegex, creator=self.CreateVideoItem)

        self.folderItemRegex = Regexer.from_expresso(self.folderItemRegex)
        self._AddDataParser("*", parser=self.folderItemRegex, creator=self.CreateFolderItem)

        # Add an updater
        self._AddDataParser("*", updater=self.UpdateVideoItem)

        self.baseUrl = "{0}//{2}".format(*self.mainListUri.split("/", 3))
        self.searchInfo = {
            "se": ["sok", "S&ouml;k"],
            "ee": ["otsi", "Otsi"],
            "dk": ["sog", "S&oslash;g"],
            "no": ["sok", "S&oslash;k"],
            "lt": ["paieska", "Paie&scaron;ka"],
            "lv": ["meklet", "Mekl&#275;t"]
        }

    def RemoveClips(self, data):
        clipStart = data.find('<div class="secondary-content">')
        if clipStart > 0:
            data = data[:clipStart]
        return data, []

    def AddSearch(self, data):
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

        Logger.info("Performing Pre-Processing")
        items = []

        title = "\a.: %s :." % (self.searchInfo.get(self.language, self.searchInfo["se"])[1], )
        Logger.trace("Adding search item: %s", title)
        searchItem = mediaitem.MediaItem(title, "searchSite")
        searchItem.thumb = self.noImage
        searchItem.fanart = self.fanart
        searchItem.dontGroup = True
        items.append(searchItem)

        Logger.debug("Pre-Processing finished")
        return data, items

    def CreateVideoItem(self, resultSet):
        item = self.CreateEpisodeItem(resultSet)
        if item is None:
            return None

        altName = resultSet["description"]

        item.name = "{0} - {1}".format(item.name, altName)
        item.description = altName
        item.type = "video"
        item.complete = False
        return item

    def UpdateVideoItem(self, item):
        headers = {}
        if self.localIP:
            headers.update(self.localIP)

        data = UriHandler.open(item.url, proxy=self.proxy, additional_headers=headers)
        m3u8Url = Regexer.do_regex('data-file="([^"]+)"', data)[0]

        part = item.create_new_empty_media_part()
        if AddonSettings.use_adaptive_stream_add_on(with_encryption=False):
            stream = part.append_media_stream(m3u8Url, 0)
            M3u8.set_input_stream_addon_input(stream, proxy=self.proxy, headers=headers)
            item.complete = True
        else:
            for s, b, a in M3u8.get_streams_from_m3u8(m3u8Url, self.proxy,
                                                      headers=headers, map_audio=True):

                if a and "-audio" not in s:
                    videoPart = s.rsplit("-", 1)[-1]
                    videoPart = "-%s" % (videoPart,)
                    s = a.replace(".m3u8", videoPart)
                part.append_media_stream(s, b)
                item.complete = True

        return item

    def SearchSite(self, url=None):
        # https://tvplay.tv3.lt/paieska/Lietuvos%20talentai%20/
        # https://tvplay.tv3.ee/otsi/test%20test%20/
        url = self.__GetSearchUrl()
        url = "{0}/%s/".format(url)
        return chn_class.Channel.SearchSite(self, url)

    def __GetSearchUrl(self):
        searchInfo = self.searchInfo.get(self.language, None)
        if searchInfo is None:
            searchInfo = self.searchInfo["se"]
        return "%s/%s" % (self.baseUrl, searchInfo[0])
