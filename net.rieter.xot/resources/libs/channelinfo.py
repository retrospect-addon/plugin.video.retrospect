# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

# ===============================================================================
# Import the default modules
# ===============================================================================
import os
import sys
import xbmcgui
from environments import Environments
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.jsonhelper import JsonHelper
from logger import Logger
from config import Config
from addonsettings import AddonSettings
from helpers.languagehelper import LanguageHelper
from textures import TextureHandler


class ChannelInfo:
    def __init__(self, guid, name, description, icon, category, path,
                 channelCode=None, sortOrder=255, language=None,
                 compatiblePlatforms=Environments.All, fanart=None):
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
        pathParts = path.split(os.sep)
        self.moduleName = os.path.splitext(pathParts[-1])[0]

        self.id = ("%s.%s.%s" % (pathParts[-3], pathParts[-2], channelCode or "")).rstrip(".")
        # TODO: the GUID could be replaced by the self.id in the future.
        self.guid = guid
        self.channelName = name
        self.channelCode = channelCode
        self.channelDescription = description

        self.category = category
        self.compatiblePlatforms = compatiblePlatforms
        self.language = language
        self.sortOrder = sortOrder
        # I am Dutch, sorry about that
        if language == "nl":
            self.sortOrderPerCountry = "#_%s.%04d" % (language or "zz", sortOrder)
        else:
            self.sortOrderPerCountry = "#%s.%04d" % (language or "zz", sortOrder)
        self.firstTimeMessage = None

        self.settings = []
        self.localIPSupported = False

        self.icon = icon
        self.fanart = fanart
        self.version = "x.x.x.x"
        self.enabled = False                # enabled from the settings
        self.visible = False                # hidden/visible due to country settings
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

        self.icon = self.__GetImagePath(self.icon)
        item = xbmcgui.ListItem(name, description)
        try:
            item.setIconImage(self.icon)
        except:
            # it was deprecated
            pass
        item.setArt({'thumb': self.icon, 'icon': self.icon})

        # http://mirrors.kodi.tv/docs/python-docs/14.x-helix/xbmcgui.html#ListItem-setInfo
        item.setInfo("video", {"Title": name,
                               # "Count": self.sortOrderPerCountry,
                               # "TrackNumber": self.sortOrder,
                               "Genre": LanguageHelper.GetFullLanguage(self.language),
                               # "Tagline": description,
                               "Plot": description})

        if AddonSettings.HideFanart():
            return item

        if self.fanart is not None:
            self.fanart = self.__GetImagePath(self.fanart)
        else:
            self.fanart = os.path.join(Config.rootDir, "fanart.jpg")
        item.setArt({'fanart': self.fanart})
        return item

    def __str__(self):
        """Returns a string representation of the current channel."""

        if self.channelCode is None:
            return "%s [%s-%s, %s, %s, %s] (Order: %s)" % (
                self.channelName, self.id, self.version, self.language, self.category,
                self.guid, self.sortOrderPerCountry
            )
        else:
            return "%s (%s) [%s-%s, %s, %s, %s] (Order: %s)" % (
                self.channelName, self.channelCode, self.id, self.version, self.language,
                self.category, self.guid, self.sortOrderPerCountry
            )

    def __repr__(self):
        """ Technical representation """

        return "%s @ %s\nmoduleName: %s\nicon: %s\ncompatiblePlatforms: %s" % (
            self, self.path, self.moduleName,
            self.icon, self.compatiblePlatforms
        )

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

        compVal = cmp(self.sortOrderPerCountry, other.sortOrderPerCountry)
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
        return TextureHandler.Instance().GetTextureUri(self, image)

    @staticmethod
    def FromJson(path, version="x.x.x.x"):
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
        Logger.Debug("Found %s channels and %s settings in %s", len(channels), len(settings), path)

        for channel in channels:
            channelInfo = ChannelInfo(channel["guid"],
                                      channel["name"],
                                      channel["description"],
                                      channel["icon"],
                                      channel["category"],
                                      path,

                                      # none required items
                                      channel.get("channelcode", None),
                                      channel.get("sortorder", 255),
                                      channel.get("language", None),
                                      eval(channel.get("compatible", "Environments.All")),
                                      channel.get("fanart", None))
            channelInfo.firstTimeMessage = channel.get("message", None)
            # Disable spoofing for the moment
            # channelInfo.localIPSupported = channel.get("localIPSupported", False)
            channelInfo.settings = settings
            channelInfo.version = version

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
