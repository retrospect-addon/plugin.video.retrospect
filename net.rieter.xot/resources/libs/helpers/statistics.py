#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
# import threading
# import time
from datetime import datetime

from logger import Logger
from urihandler import UriHandler
from addonsettings import AddonSettings
from helpers.htmlentityhelper import HtmlEntityHelper
from config import Config


class Statistics:
    __STATISTICS = "Statistics"
    __ERRORS = "Errors"
    __ACTION_PLAY = "Play"
    __ACTION_LIST = "List"
    __ACTION_CHANNEL = "Channel"

    def __init__(self):
        """
        Category    Action          Label               Value           Referer
        ================================================================================
        Statistics  CDN             <cdn-url>           <bytes>         -
        Statistics  <channelname>   Channel             1               -
        Statistics  <channelname>   Play: <name>        1               <url>
        Errors      <channelname>   List: <name>        1               <url>
        Errors      <channelname>   Play: <name>        1               <url>
        """
        raise ValueError("Cannot and should not create an instance")

    @staticmethod
    def RegisterCdnBytes(totalBytes):
        """ Register the bytes transfered via CDN

        @param totalBytes: int - The total bytes transfered
        """

        Statistics.__RegisterHit(Statistics.__STATISTICS,
                                 "CDN", Config.TextureUrl, value=totalBytes)

    @staticmethod
    def RegisterError(channel, title="Channel", item=None):
        """ Register an empty list for a specific Channel and Title

        @param channel: Channel : The channel that had the error
        """

        referer = None

        if item is None:
            item = channel.parentItem

        if item is not None:
            if item.isPaid or item.isDrmProtected:
                Logger.Debug("Not registering error of item which is Paid or DRM Protected.")
                return

            title = item.name
            referer = item.url
            if item.IsPlayable():
                title = "%s: %s" % (Statistics.__ACTION_PLAY, title)
            else:
                title = "%s: %s" % (Statistics.__ACTION_LIST, title)

        Statistics.__RegisterHit(Statistics.__ERRORS, channel.channelName, title,
                                 value=1, referer=referer,
                                 appVersion=channel.version, appId=channel.id)

    @staticmethod
    def RegisterChannelOpen(channel, startTime=None):
        """ Register a Channel loading

        Arguments:
        channel  : String   - Name of the channel

        Keyword Arguments:
        starTime : datetime - The start time of the add-on
        """

        duration = None
        if startTime:
            timeDelta = (datetime.now() - startTime)
            duration = timeDelta.seconds * 1000 + (timeDelta.microseconds / (10 ** 3))

        Statistics.__RegisterHit(Statistics.__STATISTICS, channel.channelName,
                                 Statistics.__ACTION_CHANNEL,
                                 value=duration,
                                 appVersion=channel.version, appId=channel.id)

    @staticmethod
    def RegisterPlayback(channel, item, startTime=None, offset=0):
        """ Register a video playback

        Arguments:
        channel  : String    - Name of the channel
        item :     MediaItem - The item that is playing


        Keyword Arguments:
        starTime : datetime - The start time of the add-on
        offSet   : int      - Milli seconds to substract due to downloading

        """

        duration = offset
        timeDelta = None
        if startTime:
            timeDelta = (datetime.now() - startTime)
            duration = timeDelta.seconds * 1000 + (timeDelta.microseconds / (10 ** 3)) + offset
        Logger.Trace("Duration set to: %s (%s, offset=%s)", duration, timeDelta or "None", offset)

        action = "%s: %s" % (Statistics.__ACTION_PLAY, item.name)
        Statistics.__RegisterHit(Statistics.__STATISTICS, channel.channelName, action,
                                 value=duration, referer=item.url,
                                 appVersion=channel.version, appId=channel.id)

    @staticmethod
    def __RegisterHit(category, action, label, value=None, referer=None, appVersion=None, appId=None):
        """ Register an event with Google Analytics

        @param category:    String - Name of category to register
        @param action:      String - Name of action to register
        @param value:       String - Value of action to register
        @param label:       String - The label for the event
        @param value:       int    - The value for the event (Defaults to None)
        @param referer:     String - The referer (Defaults to None)
        @param appVersion:  String - Version of the channel
        @param appId:       String - ID of the channel

        See: https://ga-dev-tools.appspot.com/hit-builder/
        v=1&t=event&tid=UA-3902785-1&cid=3c8961be-6a53-48f6-bded-d136760ab55f&ec=Test&ea=Test%20Action&el=Test%20%5Blabel)&ev=100

        """

        try:
            if not AddonSettings.SendUsageStatistics():
                Logger.Debug("Not sending statistics because the configuration does not allow this.")
                return

            postData = {
                "v": 1,
                "t": "event",
                "tid": Config.googleAnalyticsId,
                "cid": AddonSettings.GetClientId(),
                "ec": HtmlEntityHelper.UrlEncode(category),
                # "ec": HtmlEntityHelper.UrlEncode("Test"),
                "ea": HtmlEntityHelper.UrlEncode(HtmlEntityHelper.ConvertHTMLEntities(action)),
                "el": HtmlEntityHelper.UrlEncode(HtmlEntityHelper.ConvertHTMLEntities(label)),
                "an": Config.appName
            }

            if value is not None:
                postData["ev"] = value
            if appVersion is not None and appId is not None:
                postData["av"] = appVersion
                postData["aid"] = appId

            if referer is not None:
                if "://" not in referer:
                    referer = "http://%s" % (referer,)
                postData["dr"] = HtmlEntityHelper.UrlEncode(referer)

            url = "https://www.google-analytics.com/collect"
            data = ""
            for k, v in postData.iteritems():
                data += "%s=%s&" % (k, v)
            data = data.rstrip("&")

            # url = "http://www.rieter.net/net.rieter.xot.usage/%s/%s/?rnd=%s" % (action, value, rnd)
            Logger.Debug("Sending statistics: %s", data)

            # now we need something async without caching
            userAgent = AddonSettings.GetUserAgent()
            if userAgent:
                result = UriHandler.Open(url, additionalHeaders={"User-Agent": userAgent}, params=data, noCache=True)
            else:
                result = UriHandler.Open(url, params=data, noCache=True)
            if len(result) > 0:
                Logger.Debug("Statistics were successfully sent. Content Length: %d", len(result))
            else:
                Logger.Warning("Statistics were not successfully sent")
        except:
            # we should never ever fail here
            Logger.Warning("Cannot send statistics", exc_info=True)
            return
