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


class Statistics:
    def __init__(self):
        raise ValueError("Cannot and should not create an instance")

    @staticmethod
    def RegisterChannelOpen(channel, startTime=None):
        """ Register a Channel loading

        Arguments:
        channel  : String   - Name of the channel

        Keyword Arguments:
        starTime : datetime - The start time of the add-on

        """

        return Statistics.__RegisterHit("Channel", Statistics.__GetSafeString(channel.channelName), startTime)

    @staticmethod
    def RegisterPlayback(channel, startTime=None, offset=0):
        """ Register a video playback

        Arguments:
        channel  : String   - Name of the channel

        Keyword Arguments:
        starTime : datetime - The start time of the add-on
        offSet   : int      - Milli seconds to substract due to downloading

        """

        return Statistics.__RegisterHit("Playback", Statistics.__GetSafeString(channel.channelName), startTime, offset)

    @staticmethod
    def __RegisterHit(action, value, startTime=None, offset=0):
        """ Register a hit

        Arguments:
        action   : String   - Name of action to register
        value    : String   - Value of action to register

        Keyword Arguments:
        starTime : datetime - The start time of the add-on
        offSet   : int      - Milli seconds to substract due to downloading

        """

        try:
            if not AddonSettings.SendUsageStatistics():
                Logger.Debug("Not sending statistics because the configuration does not allow this.")
                return

            duration = None
            if startTime:
                timeDelta = (datetime.now() - startTime)
                duration = timeDelta.seconds * 1000 + (timeDelta.microseconds / (10 ** 3)) + offset
                Logger.Trace("Duration set to: %s (%s, offset=%s)", duration, timeDelta, offset)

            value = HtmlEntityHelper.UrlEncode(value)
            action = HtmlEntityHelper.UrlEncode(action)
            # now = datetime.datetime.now()
            # rnd = time.mktime(now.timetuple())
            url = "http://www.rieter.net/net.rieter.xot.usage/%s/%s/%s" % (action, value, duration or "")
            # url = "http://www.rieter.net/net.rieter.xot.usage/%s/%s/?rnd=%s" % (action, value, rnd)
            Logger.Debug("Sending statistics: %s", url)

            # now we need something async without caching
            userAgent = AddonSettings.GetUserAgent()
            if userAgent:
                UriHandler.Open(url, additionalHeaders={"User-Agent": userAgent}, noCache=True)
            else:
                UriHandler.Open(url)
        except:
            # we should never ever fail here
            Logger.Warning("Cannot send statistics", exc_info=True)
            return

    @staticmethod
    def __GetSafeString(name):
        """ HTML encodes and replaces brackets (seems a bug in GA)

        Arguments:
        name : String - The text to prep.

        """

        if ")" in name:
            name = name.replace(")", "]").replace("(", "[")

        return HtmlEntityHelper.ConvertHTMLEntities(name)
