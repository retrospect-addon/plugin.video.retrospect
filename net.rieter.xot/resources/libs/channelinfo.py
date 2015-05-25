#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

#===============================================================================
# Import the default modules
#===============================================================================
import os
import sys

import xbmcgui

from environments import Environments
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.jsonhelper import JsonHelper
from logger import Logger
from urihandler import UriHandler
from config import Config
import textures


class ChannelInfo:

    def __init__(self, guid, name, description, icon, category, path,
                 channelCode=None, sortOrder=255, language=None, compatiblePlatforms=Environments.All, fanart=None):
        """ Creates a ChannelInfo object with basic information for a channel

        Arguments:
        guid        : String - A unique GUID
        name        : String - The channel name
        description : String - The channel description
        icon        : String - Name of the icon
        path        : String - Path of the channel

        Keyword Arguments:
        channelCode         : String       - A code that distinguishes a channel
                                             within a module. Default is None
        sortOrder           : Int          - The sortorder (0-255). Default is 255
        language            : String       - The language of the channel. Default is None
        compatiblePlatforms : Environments - The supported platforms. Default is Environments.All
        fanart              : String       - A fanart url/path

        """

        # set the path info
        self.path = os.path.dirname(path)
        self.moduleName = os.path.splitext(os.path.basename(path))[0]

        self.channelName = name
        self.channelCode = channelCode
        self.guid = guid
        self.channelDescription = description

        self.category = category
        self.compatiblePlatforms = compatiblePlatforms
        self.sortOrder = sortOrder  # max 255 channels
        self.language = language
        self.firstTimeMessage = None

        self.settings = []

        self.textureManager = textures.GetTextureHandler(self, Config,
                                                         logger=Logger.Instance(),
                                                         uriHandler=UriHandler.Instance())
        # Should be called from channelimporter.py:299
        # self.textureManager.PurgeTextureCache()

        self.icon = self.__GetImagePath(icon)            # : The icon path or url
        self.fanart = None
        if fanart is not None:
            self.fanart = self.__GetImagePath(fanart)    # : The path or url
        return

    def GetChannel(self):
        """ Instantiates a channel from a ChannelInfo object """

        Logger.Trace("Importing module %s from path %s", self.moduleName, self.path)

        sys.path.append(self.path)
        exec ("import %s" % (self.moduleName,))

        channelCommand = '%s.Channel(self)' % (self.moduleName,)
        try:
            Logger.Trace("Running command: %s", channelCommand)
            channel = eval(channelCommand)
        except:
            Logger.Error("Cannot Create channel for %s", self, exc_info=True)
            return None
        return channel

    @property
    def safeName(self):
        """ Returns the channel name in a format that can be safely be used in the Kodi settings and will not cause
        any issues with the boolean expressions there.
        """

        return self.channelName.replace("(", "[").replace(")", "]")

    def GetXBMCItem(self):
        """ Creates an Xbmc ListItem object for this channel """

        name = HtmlEntityHelper.ConvertHTMLEntities(self.channelName)
        description = HtmlEntityHelper.ConvertHTMLEntities(self.channelDescription)

        item = xbmcgui.ListItem(name, description, self.icon, self.icon)
        item.setInfo("video", {"tracknumber": self.sortOrder, "Tagline": description, "Plot": description})
        if self.fanart is not None:
            item.setProperty('fanart_image', self.fanart)
        return item

    def __str__(self):
        """Returns a string representation of the current channel."""

        if self.channelCode is None:
            return "%s [%s, %s, %s] (Order: %s)" % (self.channelName, self.language, self.category,
                                                    self.guid, self.sortOrder)
        else:
            return "%s (%s) [%s, %s, %s] (Order: %s)" % (self.channelName, self.channelCode, self.language,
                                                         self.category, self.guid, self.sortOrder)

    def __repr__(self):
        """ Technical representation """

        return "%s @ %s\nmoduleName: %s\nicon: %s\ncompatiblePlatforms: %s" % (self, self.path, self.moduleName,
                                                                               self.icon, self.compatiblePlatforms)

    def __eq__(self, other):
        """Compares to channel objects for equality

        Arguments:
        other : Channel - the other channel to compare to

        The comparison is based only on the self.guid of the channels.

        """

        if other is None:
            return False

        return self.guid == other.guid

    def __cmp__(self, other):
        """Compares to channels

        Arguments:
        other : Channel - the other channel to compare to

        Returns:
        The return value is negative if self < other, zero if self == other and strictly positive if self > other

        """

        if other is None:
            return 1

        compVal = cmp(self.sortOrder, other.sortOrder)
        if compVal == 0:
            compVal = cmp(self.channelName, other.channelName)

        return compVal

    def __GetImagePath(self, image):
        """ Tries to determine the path of an image

        Arguments:
        image : String - The filename (not path) of the image

        Returns the path of the image. In case of a XBMC skin image it will
        return just the filename, else the full path.

        """

        # if Config.CdnUrl is None:
        #     return os.path.join(self.path, image)
        #
        # return "%s%s" % (Config.CdnUrl, image)
        return self.textureManager.GetTextureUri(image)

    @staticmethod
    def FromJson(path):
        channelInfos = []
        # Logger.Trace("Using JSON reader for %s", path)

        jsonFile = open(path)
        jsonData = jsonFile.read()
        jsonFile.close()

        json = JsonHelper(jsonData, logger=Logger.Instance())
        channels = json.GetValue("channels")

        if "settings" in json.json:
            settings = json.GetValue("settings")
        else:
            settings = []
        Logger.Debug("Found %s channels and %s settings", len(channels), len(settings))

        for channel in channels:
            channelInfo = ChannelInfo(channel["guid"],
                                      channel["name"],
                                      channel["description"],
                                      channel["icon"],
                                      channel["category"],
                                      path,

                                      # none required items
                                      channel.get("channelcode", None),
                                      int(channel.get("sortorder", "255")),
                                      channel.get("language", None),
                                      eval(channel.get("compatible", "Environments.All")),
                                      channel.get("fanart", None))
            channelInfo.firstTimeMessage = channel.get("message", None)
            channelInfo.settings = settings

            # validate a bit
            if channelInfo.channelCode == "None":
                raise Exception("'None' as channelCode")
            if channelInfo.language == "None":
                raise Exception("'None' as language")

            channelInfos.append(channelInfo)

        return channelInfos

    @staticmethod
    def __GetText(channel, name):
        """ retrieves the text from a XML node with a specific Name

        Arguments:
        parent : XML Element - The element to search
        name   : String      - The name to search for

        Returns an Byte Encoded string

        """
        text = channel[name]
        if not text:
            return text

        return text

if __name__ == "__main__":
    ci = ChannelInfo("",
                     "",
                     "",
                     "offloneicon.png",
                     "Geen",
                     __file__,
                     "CODE",
                     - 1,
                     "NL",
                     Environments.Android)
    print ci
    print repr(ci)
