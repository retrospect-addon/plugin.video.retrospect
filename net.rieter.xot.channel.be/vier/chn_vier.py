import chn_class
import cookielib

from logger import Logger
from regexer import Regexer
from urihandler import UriHandler
from parserdata import ParserData
from streams.m3u8 import M3u8
from vault import Vault
from helpers.htmlentityhelper import HtmlEntityHelper
from addonsettings import AddonSettings
from xbmcwrapper import XbmcWrapper
from helpers.languagehelper import LanguageHelper

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

        # ==== Actual channel setup STARTS here and should be overwritten from derived classes =====
        self.noImage = "vierimage.png"

        # setup the urls
        self.mainListUri = "http://www.vier.be/volledige-afleveringen"
        self.baseUrl = "http://www.vier.be"
        # self.swfUrl = "http://www.canvas.be/sites/all/libraries/player/PolymediaShowFX16.swf"

        # setup the main parsing data
        episodeRegex = '<h1 class="brick-title">(?<title>[^<]+)</h1>\W*<div[^>]*>\W*<a href="(?<url>[^"]+)">A'
        episodeRegex = Regexer.FromExpresso(episodeRegex)
        self._AddDataParser(self.mainListUri, matchType=ParserData.MatchExact,
                            parser=episodeRegex,
                            creator=self.CreateEpisodeItem)

        videoRegex = '<div class="[^"]+date[^"]+">\W*(?<date>\d+/\d+/\d+)\W*</div>[\w\W]{0,1000}?<h3>\W*<a[^<]+href="(?<url>[^"]+)"[^>]*>(?<title>[^<]+)'
        videoRegex = Regexer.FromExpresso(videoRegex)
        self._AddDataParser("*", matchType=ParserData.MatchExact,
                            parser=videoRegex,
                            creator=self.CreateVideoItem, updater=self.UpdateVideoItem)

        # ==========================================================================================
        # Test cases:
        # Documentaire: pages (has http://www.canvas.be/tag/.... url)

        # ====================================== Actual channel setup STOPS here ===================
        return

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

        item = chn_class.Channel.CreateEpisodeItem(self, resultSet)
        if item is None:
            return item

        # All of vier.be video's seem GEO locked.
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

        if "date" in resultSet:
            day, month, year = resultSet["date"].split("/")
            item.SetDate(year, month, day)

        # All of vier.be video's seem GEO locked.
        item.isGeoLocked = True
        return item

    def UpdateVideoItem(self, item):
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

        Logger.Debug('Starting UpdateVideoItem for %s (%s)', item.name, self.channelName)

        cookieValue = self._GetSetting("cookie", None)
        data = ""
        if cookieValue:
            Logger.Info("Found Vier.be cookie in add-on settings: %s", cookieValue)
            # Or set the cookie and just load
            name, value, expires = cookieValue.split("|")
            cookie = cookielib.Cookie(version=0,
                                      name=name,
                                      value=value,
                                      port=None,
                                      port_specified=False,
                                      domain='.vier.be',
                                      domain_specified=True,
                                      domain_initial_dot=False,
                                      path='/',
                                      path_specified=True,
                                      secure=False,
                                      expires=int(expires),
                                      discard=False,
                                      comment=None,
                                      comment_url=None,
                                      rest={'HttpOnly': None})  # , rfc2109=False)
            # only continue if the cookie has not expired yet
            if cookie.is_expired():
                Logger.Warning("Vier.be cookie in add-on settings expired")
                cookieValue = None
            else:
                UriHandler.Instance().cookieJar.set_cookie(cookie)
                data = UriHandler.Open(item.url, proxy=self.proxy, additionalHeaders=item.HttpHeaders)

        # of no setting was found, or it has expired, retry
        if not cookieValue:
            Logger.Info("No valid Vier.be cookie found. Getting one")
            v = Vault()
            password = v.GetChannelSetting(self.guid, "password")
            password = HtmlEntityHelper.UrlEncode(password)
            username = self._GetSetting("username")
            if not username or not password:
                XbmcWrapper.ShowDialog(
                    title=None,
                    lines=LanguageHelper.GetLocalizedString(LanguageHelper.MissingCredentials),
                    # notificationType=XbmcWrapper.Error,
                    # displayTime=5000
                )
                return item
            username = HtmlEntityHelper.UrlEncode(username)

            # Let's log in, get the cookie and the data
            destination = item.url.rsplit("/")[-1]
            loginUrl = "http://www.vier.be/achterderug/user?destination=node/%s" % (destination, )
            data = UriHandler.Open(loginUrl, proxy=self.proxy,
                                   params="name=%s"
                                          "&pass=%s"
                                          "&op=Inloggen"
                                          "&form_id=user_login_block" % (username, password))

            # noinspection PyProtectedMember
            cookies = UriHandler.Instance().cookieJar._cookies
            if ".vier.be" in cookies:
                cookies = cookies['.vier.be']['/']
                for cookieName in cookies:
                    if cookieName.startswith("SESS"):
                        cookieValue = "%s|%s|%s" % (cookieName,
                                                    cookies[cookieName].value,
                                                    cookies[cookieName].expires)
                        Logger.Info("Found new Vier.be cookie: %s", cookieValue)
                        AddonSettings.SetSetting("channel_%s_cookie" % (self.guid, ), cookieValue)

        # data-filename="achterderug/s2/160503_aflevering7"
        # data-application="vier_vod_geo"
        regex = 'data-filename="([^"]+)\W+data-application="([^"]+)"'
        streamData = Regexer.DoRegex(regex, data)[-1]
        # http://vod.streamcloud.be/vier_vod_geo/mp4:_definst_/achterderug/s2/160503_aflevering7.mp4/playlist.m3u8
        m3u8Url = "http://vod.streamcloud.be/%s/mp4:_definst_/%s.mp4/playlist.m3u8" % (streamData[1], streamData[0])

        # Geo Locked?
        if "geo" in streamData[1].lower():
            # set it for the error statistics
            item.isGeoLocked = True

        part = item.CreateNewEmptyMediaPart()
        for s, b in M3u8.GetStreamsFromM3u8(m3u8Url, self.proxy):
            if b < 200:
                Logger.Info("Skipping stream of quality '%s' kbps", b)
                continue
            item.complete = True
            # s = self.GetVerifiableVideoUrl(s)
            part.AppendMediaStream(s, b)

        item.complete = True
        return item
