#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
from __builtin__ import staticmethod

import os
import xbmc

#===============================================================================
# Make global object available
#===============================================================================
from logger import Logger                               # this has not further references
from proxyinfo import ProxyInfo                         # this has not further references
from config import Config                               # this has not further references
# from regexer import Regexer                             # this has not further references
from helpers.htmlentityhelper import HtmlEntityHelper   # Only has Logger as reference


class AddonSettings:
    """ Static Class for retrieving XBMC Addon settings """

    # these are static properties that store the settings. Creating them each time is causing major slow-down
    __settings = None
    __UserAgent = None

    __SORTING_ALGORITHM = "sorting_algorithm"
    __STREAM_BITRATE = "stream_bitrate"
    __STREAM_AUTOBITRATE = "stream_autobitrate"
    __SUBTITLE_MODE = "subtitle_mode"
    __CACHE_ENABLED = "http_cache"
    __CHANNEL_SETTINGS_PATTERN = "channel_%s_visible"
    __PROXY_SETTING_PATTERN = "channel_%s_proxy"
    __FOLDER_PREFIX = "folder_prefix"
    __EMPTY_FOLDER = "empty_folder"
    # __HIDE_GEOLOCKED = "hide_geolocked"
    __GEO_REGION = "geo_region"
    __LOG_LEVEL = "log_level"
    __UZG_CACHE = "uzg_cache_new"
    __RPI_PLAYER = "rpi_player_type"
    __UZG_CACHE_PATH = "uzg_cache_path"
    __SEND_STATISTICS = "send_statistics"
    __SHOW_CATEGORIES = "show_categories"
    __USER_AGENT_SETTING = "user_agent"
    __MD5_HASH_VALUE = "md_hash_value"
    __HIDE_FIRST_TIME_MESSAGE = "hide_first_time_message"
    __LIST_LIMIT = "list_limit"
    __DRM_WARNING = "show_drm_warning"
    __DRM_HIDE_ITEMS = "hide_drm"
    __PREMIUM_HIDE_ITEMS = "hide_premium"
    __HIDE_TYPES = "hide_types"
    __HIDE_FANART = "hide_fanart"

    def __init__(self):
        """Initialisation of the AddonSettings class. """

        raise NotImplementedError("Static class cannot be constructed")

    @staticmethod
    def ClearCachedAddonSettingsObject():
        """ Clears the cached add-on settings. This will force a reload for the next INSTANCE
        of an AddonSettings class. """

        AddonSettings.__settings = None

    @staticmethod
    def GetChannelSetting(channelGuid, settingId, valueForNone=None):
        """ Retrieves channel settings for the given channel

        @param channelGuid: The channel object to get the channels for
        @param settingId:   The setting to retrieve
        @type valueForNone: Value that is considered as None
        @rtype : the configured value
        """

        fullSettingId = "channel_%s_%s" % (channelGuid, settingId)
        setting = AddonSettings.__GetSetting(fullSettingId)

        if setting == "":
            setting = None
        elif setting == valueForNone:
            setting = None

        Logger.Trace("Found channel [%s] setting '%s'='%s'", channelGuid, settingId, setting or "<none>")
        return setting

    @staticmethod
    def GetPlayer(textOnly=False):
        """ Get's the default player. this is only used for raspberry pi. """

        try:
            settingIndex = int(AddonSettings.__GetSetting(AddonSettings.__RPI_PLAYER) or 0)
            if textOnly:
                return ["Auto", "DVDPlayer"][settingIndex]
            else:
                return [xbmc.PLAYER_CORE_AUTO, xbmc.PLAYER_CORE_DVDPLAYER][settingIndex]
        except Exception, e:
            Logger.Warning("Error determining the Player Core in Kodi, falling back to PLAYER_CORE_AUTO:\n%s", e.message)
            return xbmc.PLAYER_CORE_AUTO

    @staticmethod
    def GetProxyGroupIds(asString=False, asCountryCodes=False):
        """ returns the all available ProxyGroupId's in order """

        proxyIds = [30025, 30059, 30056, 30057, 30058]
        proxyCodes = [None, "other", "nl", "uk", "se"]

        if asString:
            return map(lambda i: str(i), proxyIds)

        if asCountryCodes:
            return proxyCodes

        return proxyIds

    @staticmethod
    def ShowCategories():
        """ Returns the localized category names. """

        return AddonSettings.__GetBooleanSetting(AddonSettings.__SHOW_CATEGORIES)

    # @staticmethod
    # def HideGeoLocked():
    #     """ Returs the config value that indicates of GeoLocked
    #     items should be hidden.
    #
    #     """
    #
    #     return AddonSettings.__GetBooleanSetting(AddonSettings.__HIDE_GEOLOCKED)

    @staticmethod
    def ShowDrmWarning():
        """ Should we show a DRM warning on DRM protected (^) items?

        @return: Yes or No (boolean).

        """

        return AddonSettings.__GetBooleanSetting(AddonSettings.__DRM_WARNING)

    @staticmethod
    def HideFanart():
        """ Should we hide Fanart?

        @return: Yes or No
        """
        return AddonSettings.__GetBooleanSetting(AddonSettings.__HIDE_FANART)

    @staticmethod
    def HideDrmItems():
        """ Returns whether or not to hide DRM protected items.

        @return: True/False
        """
        return AddonSettings.__GetBooleanSetting(AddonSettings.__DRM_HIDE_ITEMS)

    @staticmethod
    def HidePremiumItems():
        """ Returns whether or not to hide Premium/Paid items.

        @return: True/False
        """
        return AddonSettings.__GetBooleanSetting(AddonSettings.__PREMIUM_HIDE_ITEMS)

    @staticmethod
    def HideRestrictedFolders():
        values = [True, False]
        value = int(AddonSettings.__GetSetting(AddonSettings.__HIDE_TYPES) or 0)
        return values[value]

    @staticmethod
    def HideGeoLockedItemsForLocation(channelRegion, valueOnly=False):
        """ Returs the config value that indicates what if we should hide items that are geografically
        locked to the region of the channel (indicated by the channel language).

        @param channelRegion:  the channel region (actually the channel language)
        @param valueOnly:      if set to True, it will return the settings value

        """

        # 30074    |30024|30047|30044|30027|30007|30008|30005|30015|30006
        # Disabled |be   |de   |ee   |en-gb|lt   |lv   |nl   |no   |se
        values = [None, "be", "de", "ee", "en-gb", "lt", "lv", "nl", "no", "se"]
        valueIndex = int(AddonSettings.__GetSetting(AddonSettings.__GEO_REGION) or 0)
        currentGeografficalRegion = values[valueIndex]

        if valueOnly:
            return currentGeografficalRegion

        if currentGeografficalRegion is None:
            return False

        return not currentGeografficalRegion == channelRegion

    @staticmethod
    def GetLocalizedString(stringId):
        """ returns a localized string for this id

        Arguments:
        stringId - int - The ID for the string

        """

        return AddonSettings.__CachedSettings().getLocalizedString(stringId)

    @staticmethod
    def SendUsageStatistics():
        """ returns true if the user allows usage statistics sending """

        return AddonSettings.__GetBooleanSetting(AddonSettings.__SEND_STATISTICS)

    @staticmethod
    def HideFirstTimeMessages():
        """
        @return: returns true if the first time messages should be shown.
        """

        return AddonSettings.__GetBooleanSetting(AddonSettings.__HIDE_FIRST_TIME_MESSAGE)

    @staticmethod
    def GetCurrentAddonXmlMd5():
        return AddonSettings.__GetSetting(AddonSettings.__MD5_HASH_VALUE)

    @staticmethod
    def UpdateCurrentAddonXmlMd5(hashValue):
        AddonSettings.__settings.setSetting(AddonSettings.__MD5_HASH_VALUE, hashValue)

    @staticmethod
    def UpdateUserAgent():
        """ Creates a user agent for this instance of XOT

        this is a very slow action on lower end systems (ATV and rPi) so we minimize the number of runs

        @return: Nothing

        Actual
        User-Agent: XBMC/12.2 Git:20130502-32b1a5e (Windows NT 6.1;WOW64;Win64;x64; http://www.xbmc.org)
        Retro:
        User-Agent: XBMC/12.2 Git:20130502-32b1a5e (Windows 7;x86; http://www.xbmc.org)

        Actual:
        User-Agent: XBMC/13.0-ALPHA3 Git:e8fe5cf (Linux; Ubuntu 11.10 - XBMCbuntu; 3.0.0-17-generic i686; http://www.xbmc.org)
        Retro:
        User-Agent: XBMC/13.0-ALPHA3 Git:e8fe5cf (Linux 3.0.0-17-generic;i686; http://www.xbmc.org)

        """

        # there are slow imports, so only do them here
        import platform
        from envcontroller import EnvController

        version = xbmc.getInfoLabel("system.buildversion")

        # UriHandler.__UserAgent = "XBMC/%s (%s;%s;%s;%s, http://www.xbmc.org)" % (version, kernel, machine, windows, "")
        try:
            # The platform.<method> are not working on rPi and IOS
            # kernel = platform.architecture()
            # Logger.Trace(kernel)

            # machine = platform.machine()
            # Logger.Trace(machine)

            uname = platform.uname()
            Logger.Trace(uname)
            userAgent = "Kodi/%s (%s %s;%s; http://www.xbmc.org)" % (version, uname[0], uname[2], uname[4])
        except:
            Logger.Warning("Error setting user agent", exc_info=True)
            currentEnv = EnvController.GetPlatform(True)
            # Kodi/14.2 (Windows NT 6.1; WOW64) App_Bitness/32 Version/14.2-Git:20150326-7cc53a9
            userAgent = "Kodi/%s (%s; <unknown>; http://www.xbmc.org)" % (version, currentEnv)

        # now we store it
        AddonSettings.__settings.setSetting(AddonSettings.__USER_AGENT_SETTING, userAgent)
        AddonSettings.__UserAgent = userAgent
        Logger.Info("User agent set to: %s", userAgent)
        return

    @staticmethod
    def GetUserAgent():
        """ Retrieves a user agent string for this XBMC instance.

        @return: a user-agent string
        """

        if not AddonSettings.__UserAgent:
            # load and cache
            AddonSettings.__UserAgent = AddonSettings.__GetSetting(AddonSettings.__USER_AGENT_SETTING) or None

            # double check if the version of XBMC is still OK
            if AddonSettings.__UserAgent:
                version = xbmc.getInfoLabel("system.buildversion")

                if version not in AddonSettings.__UserAgent:
                    old = AddonSettings.__UserAgent
                    # a new XBMC version was installed, update the User-agent
                    AddonSettings.UpdateUserAgent()
                    Logger.Info("User agent updated due to Kodi version change from\n%s to\n%s",
                                old, AddonSettings.__UserAgent)
            else:
                AddonSettings.UpdateUserAgent()
                Logger.Info("Set initial User agent version because it was missing.")

        Logger.Debug("User agent retrieved from cache: %s", AddonSettings.__UserAgent)
        return AddonSettings.__UserAgent

    @staticmethod
    def CacheHttpResponses():
        """ Returns True if the HTTP responses need to be cached """

        return AddonSettings.__GetBooleanSetting(AddonSettings.__CACHE_ENABLED)

    @staticmethod
    def GetMaxStreamBitrate():
        """Returns the maximum bitrate (kbps) for streams specified by the user"""

        setting = AddonSettings.__GetSetting(AddonSettings.__STREAM_BITRATE)
        return int(setting)

    @staticmethod
    def GetStreamAutoBitrate():
        """ Returns true if XBMC should determine the bitrate if possible. """

        return AddonSettings.__GetBooleanSetting(AddonSettings.__STREAM_AUTOBITRATE)

    @staticmethod
    def GetFolderPrefix():
        """ returns the folder prefix """

        setting = AddonSettings.__GetSetting(AddonSettings.__FOLDER_PREFIX)
        return setting

    @staticmethod
    def GetEmptyListBehaviour():
        """
        @return: returns the behaviour for empty lists:

        0 = Error
        1 = Empty List
        2 = Dummy

        """

        setting = int(AddonSettings.__GetSetting(AddonSettings.__EMPTY_FOLDER))
        if setting == 0:
            return "error"
        elif setting == 1:
            return "empty"
        else:
            return "dummy"

    @staticmethod
    def UseSubtitle():
        """Returns whether to show subtitles or not"""

        setting = AddonSettings.__GetSetting(AddonSettings.__SUBTITLE_MODE)

        if setting == "0":
            return True
        else:
            return False

    @staticmethod
    def GetSortAlgorithm():
        """Retrieves the sorting mechanism from the settings

        Returns:
         * date - If sorting should be based on timestamps
         * name - If sorting should be based on names

        """

        setting = AddonSettings.__GetSetting(AddonSettings.__SORTING_ALGORITHM)
        if setting == "0":
            return "name"
        elif setting == "1":
            return "date"
        else:
            return "none"

    @staticmethod
    def GetUzgCacheDuration():
        """ Returns the UZG cache duration """

        cacheTime = AddonSettings.__GetSetting(AddonSettings.__UZG_CACHE)
        if cacheTime.lower() == "true":
            # kept for backwards compatibility
            cacheTime = 5
        elif cacheTime.lower() == "false":
            # kept for backwards compatibility
            cacheTime = 0
        else:
            cacheTime = int(cacheTime or 0)

        return cacheTime

    @staticmethod
    def GetUzgCachePath():
        """ returns the cachepath for UZG or None if not set """

        path = AddonSettings.__GetSetting(AddonSettings.__UZG_CACHE_PATH)
        if path.startswith("smb://"):
            path = path.replace("smb://", "\\\\").replace("/", "\\")
        return path

    @staticmethod
    def GetListLimit():
        """ Retrieves the limit for a list before it is grouped alphabetically.


        @return: an integer with the limit
        """

        limit = AddonSettings.__GetSetting(AddonSettings.__LIST_LIMIT)
        if limit == "":
            limit = -1
        else:
            limit = int(limit)

        return [-1, 50, 75, 100, 150, 200, 1000][limit]

    @staticmethod
    def GetLogLevel():
        """ Returns True if the add-on should do trace logging """

        level = AddonSettings.__GetSetting(AddonSettings.__LOG_LEVEL)
        if level == "":
            return 10

        # the return value is zero based. 0 -> Trace , 1=Debug (10), 2 -> Info (20)
        return int(level) * 10

    @staticmethod
    def ShowChannel(channel):
        """Check if the channel should be shown

        Arguments:
        channel : Channel - The channel to check.

        """

        settingId = AddonSettings.__CHANNEL_SETTINGS_PATTERN % (channel.guid, )
        setting = AddonSettings.__GetSetting(settingId)

        if setting == "":
            return True
        else:
            return setting == "true"

    @staticmethod
    def ShowChannelSettings(channel):
        """ Show the add-on settings and pre-selects the channel settings tab with the correct channel
        selected.

        @param channel: The channel to display settings for.
        """

        channelName = channel.safeName

        # remove some HTML chars
        channelName = HtmlEntityHelper.ConvertHTMLEntities(channelName)
        Logger.Debug("Showing channel settings for channel: %s (%s)", channelName, channel.channelName)

        # Set the channel to be the preselected one
        AddonSettings.__settings.setSetting("config_channel", channelName)

        # show settings and focus on the channel settings tab
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % (Config.addonId,))

        # the 100 range are the tabs
        # the 200 range are the controls in a tab
        xbmc.executebuiltin('SetFocus(%i)' % 102)

    @staticmethod
    def ShowSettings():
        """Shows the settings dialog"""

        AddonSettings.__CachedSettings().openSettings()  # this will open settings window

        # reload the cache because stuff might have changed
        AddonSettings.__LoadSettings()
        Logger.Info("Clearing Settings cache because settings dialog was shown.")
        return

    @staticmethod
    def ShowChannelWithLanguage(languageCode):
        """Checks if the channel with a certain languageCode should be loaded.

        Arguments:
        languageCode : string - one of these language strings:
                                 * nl    - Dutch
                                 * se    - Swedish
                                 * lt    - Lithuanian
                                 * lv    - Latvian
                                 * ca-fr - French Canadian
                                 * ca-en - English Canadian
                                 * be    - Belgium
                                 * en-gb - British
                                 * ee    - Estonia
                                 * dk    - Danish
                                 * None  - Other languages

        Returns:
        True if the channels should be shown. If the lookup does not match
        a NotImplementedError is thrown.

        """
        (settingsId, settingsLabel) = AddonSettings.__GetLanguageSettingsIdAndLabel(languageCode)  # @UnusedVariables
        return AddonSettings.__GetSetting(settingsId) == "true"

    @staticmethod
    def GetProxyForChannel(channelInfo):
        """ returns the proxy for a specific channel

        Arguments:
        channelInfo : ChannelInfo - The channel to get proxy info for

        """

        proxies = AddonSettings.GetProxyGroupIds(asCountryCodes=True)

        proxyId = AddonSettings.GetProxyIdForChannel(channelInfo)
        if proxyId == 0:
            Logger.Debug("No proxy configured for %s", channelInfo)
            return None

        prefix = proxies[proxyId]
        server = AddonSettings.__GetSetting("%s_proxy_server" % (prefix,))
        port = int(AddonSettings.__GetSetting("%s_proxy_port" % (prefix,)) or 0)
        proxyType = AddonSettings.__GetSetting("%s_proxy_type" % (prefix,)) or "http"
        username = AddonSettings.__GetSetting("%s_proxy_username" % (prefix,))
        password = AddonSettings.__GetSetting("%s_proxy_password" % (prefix,))
        pInfo = ProxyInfo(server, port, scheme=proxyType.lower(), username=username, password=password)
        Logger.Debug("Found proxy for channel %s:\n%s", channelInfo, pInfo)
        return pInfo

    @staticmethod
    def GetProxyIdForChannel(channelInfo):
        """ returns the proxy for a specific channel

        Arguments:
        channelInfo : ChannelInfo - The channel to get proxy info for

        """

        settingId = AddonSettings.__PROXY_SETTING_PATTERN % (channelInfo.guid,)
        proxyId = int(AddonSettings.__GetSetting(settingId) or 0)
        return proxyId

    @staticmethod
    def SetProxyIdForChannel(channelInfo, proxyIndex):
        """ Sets the ProxyId for a channel

        Arguments:
        channelInfo : ChannelInfo - The channel
        proxyIndex  : Integer     - The Proxy Index

        """

        settingId = AddonSettings.__PROXY_SETTING_PATTERN % (channelInfo.guid,)
        AddonSettings.__CachedSettings().setSetting(settingId, str(proxyIndex))
        return

    #noinspection PyUnresolvedReferences
    @staticmethod
    def UpdateAddOnSettingsWithChannels(channels, config):
        """ updats the settings.xml to include all the channels


        Arguments:
        channels : List<channels> - The channels to add to the settings.xml
        config   : Config         - The configuration object

        """

        # sort the channels
        channels.sort()

        # Then we read the original file
        filenameTemplate = os.path.join(config.rootDir, "resources", "settings_template.xml")
        settingsXml = open(filenameTemplate, "r")
        contents = settingsXml.read()
        settingsXml.close()

        newContents = AddonSettings.__UpdateAddOnSettingsWithLanguages(contents, channels)
        newContents = AddonSettings.__UpdateAddOnSettingsWithChannelSelection(newContents, channels)
        newContents, settingsOffsetForVisibility = \
            AddonSettings.__UpdateAddOnSettingsWithChannelSettings(newContents, channels)
        newContents = AddonSettings.__UpdateAddOnSettingsWithProxies(newContents, channels, settingsOffsetForVisibility)

        # Finally we insert the new XML into the old one
        filename = os.path.join(config.rootDir, "resources", "settings.xml")
        try:
            Logger.Trace(newContents)
            settingsXml = open(filename, "w+")
            settingsXml.write(newContents)
            settingsXml.close()
        except:
            Logger.Error("Something went wrong trying to update the settings.xml", exc_info=True)
            try:
                settingsXml.close()
            except:
                pass
            # restore original settings
            settingsXml = open(filename, "w+")
            settingsXml.write(contents)
            settingsXml.close()
            return

        Logger.Info("Settings.xml updated succesfully. Reloading settings.")
        AddonSettings.__LoadSettings()
        return

    @staticmethod
    def __UpdateAddOnSettingsWithChannelSelection(contents, channels):
        """ Adds the settings part that allows the selection of the channel for which the channel settings should
        be displayed.

        @param contents: The current settings
        @param channels: The available channels
        @return: updated contents

        """

        if "<!-- start of active channels -->" not in contents:
            Logger.Error("No '<!-- start of active channels -->' found in settings.xml. Stopping updating.")
            return

        channelSelectionXml = '        <!-- start of active channels -->\n' \
                              '        <setting id="config_channel" type="select" label="30040" values="'
        for channel in channels:
            # we need to make sure we don't have any ( or ) in the names, as it won't work with the eq(,) in the XML
            channelName = channel.safeName
            channelSelectionXml = "%s%s|" % (channelSelectionXml, channelName)

        # now finish up the settings
        channelSelectionXml = '%s" />' % (channelSelectionXml.rstrip("|"),)

        begin = contents[:contents.find('<!-- start of active channels -->')].strip()
        end = contents[contents.find('<!-- end of active channels -->'):].strip()
        contents = "%s\n%s\n        %s" % (begin, channelSelectionXml, end)

        return contents

    @staticmethod
    def __UpdateAddOnSettingsWithChannelSettings(contents, channels):
        """ Adds the channel specific settings

        @param contents: The current settings
        @param channels: The available channels
        @return: updated contents and the offset in visibility

        This method first aggregates the settings and then adds them.

        """

        if "<!-- begin of channel settings -->" not in contents:
            Logger.Error("No '<!-- begin of channel settings -->' found in settings.xml. Stopping updating.")
            return

        settings = dict()

        # There are 2 settings between the selector list and the channel settings in the settings_template.xml
        settingOffsetForVisibility = 2

        # Let's make sure they are sorted by channel module. So we first go through them all and then create
        # the XML.
        for channel in channels:
            if not channel.settings:
                continue

            if channel.moduleName not in settings:
                settings[channel.moduleName] = []

            # Sort the settings so they are really in the correct order, because this is not guaranteed by the
            # json parser
            channel.settings.sort(lambda a, b: cmp(a["order"], b["order"]))
            for channelSettings in channel.settings:
                settingId = channelSettings["id"]
                settingValue = channelSettings["value"]
                Logger.Debug("Adding setting: '%s' with value '%s'", settingId, settingValue)

                if settingValue.startswith("id="):
                    settingXml = "<setting %s visible=\"eq(-%%s,%s)\" />" % \
                                 (settingValue, channel.safeName)
                else:
                    settingXml = '<setting id="channel_%s_%s" %s visible=\"eq(-%%s,%s)\" />' % \
                                 (channel.guid, settingId, settingValue, channel.safeName)
                settings[channel.moduleName].append(settingXml)

        xmlContent = '\n        <!-- begin of channel settings -->\n'
        # Sort them to make the result more consistent
        settingKeys = settings.keys()
        settingKeys.sort()
        for module in settingKeys:
            xmlContent = '%s        <!-- %s.py -->\n' % (xmlContent, module)
            for setting in settings[module]:
                settingOffsetForVisibility += 1
                xmlContent = "%s        %s\n" % (xmlContent, setting % settingOffsetForVisibility)

        begin = contents[:contents.find('<!-- begin of channel settings -->')].strip()
        end = contents[contents.find('<!-- end of channel settings -->'):]

        Logger.Trace("Generated channel settings:\n%s", xmlContent)
        contents = "%s\n%s\n        %s" % (begin, xmlContent.rstrip(), end)
        return contents, settingOffsetForVisibility

    @staticmethod
    def __UpdateAddOnSettingsWithProxies(contents, channels, settingsOffsetForVisibility):
        """ Updates the settings.xml with the proxy settings for each channel.

        @param contents: The current settings
        @param channels: The available channels
        @param settingsOffsetForVisibility: the offset used to determine the visibility setting.
        @return: updated contents and the offset in visibility

        """

        if "<!-- start of proxy selection -->" not in contents:
            Logger.Error("No '<!-- start of proxy selection -->' found in settings.xml. Stopping updating.")
            return

        proxyIds = "|".join(AddonSettings.GetProxyGroupIds(asString=True))
        # settingOffset = int(Regexer.DoRegex("<!-- settings offset = (\d+)", contents)[-1])
        # Logger.Debug("Settings offset = %s", settingOffset)
        settingsOffsetForVisibility += 1  # there is a seperator in the settings file.

        channelProxyXml = '        <!-- start of proxy selection -->\n'
        for channel in channels:
            settingsOffsetForVisibility += 1
            # we need to make sure we don't have any ( or ) in the names, as it won't work with the eq(,) in the XML
            channelName = channel.safeName
            channelProxyXml = '%s        <setting id="%s" type="select" label="%s" lvalues="%s" default="0" visible="eq(-%s,%s)" />\n' \
                              % (channelProxyXml, AddonSettings.__PROXY_SETTING_PATTERN % (channel.guid,),
                                 30064, proxyIds, settingsOffsetForVisibility, channelName)

        # replace proxy selection
        begin = contents[:contents.find('<!-- start of proxy selection -->')].strip()
        end = contents[contents.find('<!-- end of proxy selection -->'):].strip()
        contents = "%s\n    \n%s        %s" % (begin, channelProxyXml, end)
        return contents

    @staticmethod
    def __UpdateAddOnSettingsWithLanguages(contents, channels):
        """ Adds the channel showing/hiding to the settings.xml

        @param contents: The current settings
        @param channels: The available channels
        @return: updated contents and the offset in visibility

        """

        if "<!-- start of channel selection -->" not in contents:
            Logger.Error("No '<!-- start of channel selection -->' found in settings.xml. Stopping updating.")
            return

        # First we create a new bit of settings file.
        channelXml = '        <!-- start of channel selection -->\n'

        # the distinct list of languages from the channels
        languages = map(lambda c: c.language, channels)
        languages = list(set(languages))
        languages.sort()
        Logger.Debug("Found languages: %s", languages)

        # get the labels and setting identifiers for those languages
        languageLookup = dict()
        for language in languages:
            languageLookup[language] = AddonSettings.__GetLanguageSettingsIdAndLabel(language)

        languageLookupSortedKeys = languageLookup.keys()
        languageLookupSortedKeys.sort()

        # create a list of labels
        languageLabels = map(lambda l: str(languageLookup[l][1]), languageLookupSortedKeys)
        channelXml = '%s        <setting type="lsep" label="30060" />\n' % (channelXml,)
        channelXml = '%s        <setting id="channel_selected" label="30061" type="labelenum" lvalues="30025|%s" />\n' % (channelXml, "|".join(languageLabels),)

        # we need to keep track of the number of lines, because we have
        # relative visible and enable settings.
        currentLine = 0  # the current line we are writing
        channelXml = '%s        <setting type="sep" />\n' % (channelXml,)
        currentLine += 1

        # first add the overall language settings
        for language in languageLookupSortedKeys:
            currentLine += 1
            languageIndex = languageLookupSortedKeys.index(language) + 1  # correct of the None label
            channelXml = '%s        <setting id="%s" type="bool" label="30042" default="true" visible="eq(-%s,%s)" /><!-- %s -->\n' % (channelXml, languageLookup[language][0], currentLine, languageIndex, languageLookup[language][1])

        # then the channels
        for channel in channels:
            currentLine += 1
            name = channel.channelName
            languageIndex = languageLookupSortedKeys.index(channel.language) + 1  # correct of the None label
            channelXml = '%s        <setting id="%s" type="bool" label="- %s" default="true" visible="eq(-%s,%s)" enable="eq(-%s,True)" />\n' % (channelXml, AddonSettings.__CHANNEL_SETTINGS_PATTERN % (channel.guid,), name, currentLine, languageIndex, currentLine - languageIndex - 1)

        begin = contents[:contents.find('<!-- start of channel selection -->')].strip()
        end = contents[contents.find('<!-- end of channel selection -->'):].strip()
        contents = "%s\n    \n%s        %s" % (begin, channelXml, end)
        return contents

    @staticmethod
    def __CachedSettings():
        """
        @return: a cached XBMC settings object
        """

        if not AddonSettings.__settings:
            AddonSettings.__LoadSettings()

        return AddonSettings.__settings

    @staticmethod
    def __GetLanguageSettingsIdAndLabel(languageCode):
        """ returns the settings xml part for this language

        Arguments:
        languageCode - String - The language string

        Returns:
        A tupple with the label and the settingsId.

        """

        if languageCode == "nl":
            return "show_dutch", 30005
        elif languageCode == "se":
            return "show_swedish", 30006
        elif languageCode == "lt":
            return "show_lithuanian", 30007
        elif languageCode == "lv":
            return "show_latvian", 30008
        elif languageCode == "ca-fr":
            return "show_cafr", 30013
        elif languageCode == "ca-en":
            return "show_caen", 30014
        elif languageCode == "en-gb":
            return "show_engb", 30027
        elif languageCode == "no":
            return "show_norwegian", 30015
        elif languageCode == "be":
            return "show_belgium", 30024
        elif languageCode == "ee":
            return "show_estonia", 30044
        elif languageCode == "dk":
            return "show_danish", 30045
        elif languageCode == "de":
            return "show_german", 30047
        elif languageCode is None:
            return "show_other", 30012
        else:
            raise NotImplementedError("Language code not supported: '%s'" % (languageCode, ))

    @staticmethod
    def __LoadSettings():
        # the settings object
        Logger.Info("Loading Settings into static object")
        try:
            import xbmcaddon  # @Reimport
            try:
                # first try the version without the ID
                AddonSettings.__settings = xbmcaddon.Addon()
            except:
                Logger.Warning("Settings :: Cannot use xbmcaddon.Addon() as settings. Falling back to  xbmcaddon.Addon(id)")
                AddonSettings.__settings = xbmcaddon.Addon(id=Config.addonId)
        except:
            Logger.Error("Settings :: Cannot use xbmcaddon.Addon() as settings. Falling back to xbmc.Settings(path)", exc_info=True)
            import xbmc  # @Reimport
            AddonSettings.__settings = xbmc.Settings(path=Config.rootDir)

    @staticmethod
    def __GetSetting(settingId):
        """Returns the setting for the requested ID, from the cached settings.

        Arguments:
        settingId - string - the ID of the settings

        Returns:
        The configured XBMC add-on values for that <id>.

        """

        value = AddonSettings.__CachedSettings().getSetting(settingId)

        # Logger.Trace("Settings: %s = %s", settingId, value)
        return value

    @staticmethod
    def __SortChannels(x, y):
        """ compares 2 channels based on language and then sortorder """

        value = cmp(x.language, y.language)
        if value == 0:
            return cmp(x.sortOrder, y.sortOrder)
        else:
            return value

    @staticmethod
    def __GetBooleanSetting(settingId):
        """ Arguments:
        id - string - the ID of the settings

        Returns:
        The configured XBMC add-on values for that <id>.

        """

        setting = AddonSettings.__GetSetting(settingId)
        return setting == "true"

    @staticmethod
    def PrintSettingValues():
        """Prints the settings"""

        pattern = "%s\n%s: %s"
        value = "%s: %s" % ("MaxStreamBitrate", AddonSettings.GetMaxStreamBitrate())
        value = pattern % (value, "SortingAlgorithm", AddonSettings.GetSortAlgorithm())
        value = pattern % (value, "UseSubtitle", AddonSettings.UseSubtitle())
        value = pattern % (value, "Player", AddonSettings.GetPlayer(textOnly=True))
        value = pattern % (value, "CacheHttpResponses", AddonSettings.CacheHttpResponses())
        value = pattern % (value, "Folder Prefx", "'%s'" % AddonSettings.GetFolderPrefix())
        value = pattern % (value, "Empty List Behaviour", AddonSettings.GetEmptyListBehaviour())
        value = pattern % (value, "ListLimit", AddonSettings.GetListLimit())
        value = pattern % (value, "Loglevel", AddonSettings.GetLogLevel())
        value = pattern % (value, "Geo Location", AddonSettings.HideGeoLockedItemsForLocation(None, valueOnly=True))
        value = pattern % (value, "Filter Folders", AddonSettings.HideRestrictedFolders())
        value = pattern % (value, "DRM Warning", AddonSettings.ShowDrmWarning())
        # value = pattern % (value, "Hide DRM Items", AddonSettings.HideDrmItems())
        value = pattern % (value, "Hide Premium Items", AddonSettings.HidePremiumItems())
        value = pattern % (value, "Show Dutch", AddonSettings.ShowChannelWithLanguage("nl"))
        value = pattern % (value, "Show Swedish", AddonSettings.ShowChannelWithLanguage("se"))
        value = pattern % (value, "Show Lithuanian", AddonSettings.ShowChannelWithLanguage("lt"))
        value = pattern % (value, "Show Latvian", AddonSettings.ShowChannelWithLanguage("lv"))
        # value = pattern % (value, "Show French Canadian", AddonSettings.ShowChannelWithLanguage("ca-fr"))
        # value = pattern % (value, "Show English Canadian", AddonSettings.ShowChannelWithLanguage("ca-en"))
        value = pattern % (value, "Show British", AddonSettings.ShowChannelWithLanguage("en-gb"))
        value = pattern % (value, "Show German", AddonSettings.ShowChannelWithLanguage("de"))
        value = pattern % (value, "Show Other languages", AddonSettings.ShowChannelWithLanguage(None))
        value = pattern % (value, "UZG Cache Path", AddonSettings.GetUzgCachePath())
        value = pattern % (value, "UZG Cache Time", AddonSettings.GetUzgCacheDuration())

        try:
            proxies = ["NL", "UK", "SE", "Other"]
            for proxy in proxies:
                value = pattern % (value, "%s Proxy" % (proxy, ),
                                   AddonSettings.__GetSetting("%s_proxy_server" % (proxy.lower(), )) or "Not Set")

                value = pattern % (value, "%s Proxy Port" % (proxy, ),
                                   AddonSettings.__GetSetting("%s_proxy_port" % (proxy.lower(), )) or 0)
        except:
            Logger.Error("Error", exc_info=True)
        return value
