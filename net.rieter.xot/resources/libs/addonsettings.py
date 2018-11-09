#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import os
import uuid
import shutil
import threading
import xbmc

from logger import Logger                               # this has not further references
from proxyinfo import ProxyInfo                         # this has not further references
from config import Config                               # this has not further references
from helpers.htmlentityhelper import HtmlEntityHelper   # Only has Logger as reference
from settings import localsettings, kodisettings, settingsstore

# Theoretically we could add a remote settings store too!
KODI = "kodi"
LOCAL = "local"


class AddonSettings(object):
    """ Static Class for retrieving XBMC Addon settings """

    __NoProxy = True

    # these are static properties that store the settings. Creating them each time is causing major slow-down
    __UserAgent = None
    __KodiVersion = None

    __PROXY_SETTING = "proxy"
    __LOCAL_IP_SETTING = "local_ip"
    __USER_AGENT_SETTING = "user_agent"
    __MD5_HASH_VALUE = "md_hash_value"

    #region Setting-stores properties and intialization
    __setting_stores = {}
    __settings_lock = threading.Lock()

    __language_strings = {}
    __language_current = None

    @staticmethod
    def store(store_location):
        """ Returns the Singleton store object for the given type

        :param store_location: Either the Kodi (KODI) store or in the Retrospect (LOCAL) store
        :type store_location:  str

        :return: An instance of the setting store
        :rtype:  settingsstore.SettingsStore

        """

        store = AddonSettings.__setting_stores.get(store_location, None)
        if store is not None:
            return store

        with AddonSettings.__settings_lock:
            # Just a double check in case there was a race condition??
            store = AddonSettings.__setting_stores.get(store_location, None)
            if store is not None:
                return store

            if store_location == KODI:
                store = kodisettings.KodiSettings(Logger.Instance())
            elif store_location == LOCAL:
                store = localsettings.LocalSettings(Config.profileDir, Logger.Instance())
            else:
                raise IndexError("Cannot find Setting store type: {0}".format(store_location))

            AddonSettings.__setting_stores[store_location] = store
            return store

    @staticmethod
    def __refresh(store_location):
        """ Removes the instance of the settings store causing a reload.

        :param store_location: Either the Kodi (KODI) store or in the Retrospect (LOCAL) store
        :type store_location:  str

        """

        store = AddonSettings.__setting_stores.pop(store_location, None)
        if store is None:
            return

        # this really only works if no reference to the <store> object is kept somewhere.
        del store

    def __init__(self):
        """Initialisation of the AddonSettings class. """

        raise NotImplementedError("Static class cannot be constructed")

    @staticmethod
    def clear_cached_addon_settings_object():
        """ Clears the cached add-on settings. This will force a reload for the next INSTANCE
        of an AddonSettings class. """

        for storeType in (KODI, LOCAL):
            store = AddonSettings.__setting_stores.pop(storeType, None)
            if store:
                del store

    #endregion

    #region Kodi version stuff
    @staticmethod
    def get_kodi_version():
        """ Retrieves the Kodi version we are running on.

        :return: the full string of the Kodi version. E.g.: 16.1 Git:20160424-c327c53
        :rtype: str

        """

        if AddonSettings.__KodiVersion is None:
            AddonSettings.__KodiVersion = xbmc.getInfoLabel("system.buildversion")

        return AddonSettings.__KodiVersion

    @staticmethod
    def is_min_version(min_value):
        """ Checks whether the version of Kodi is higher or equal to the given version.

        :param min_value: the minimum Kodi version
        :type min_value: int

        :return: True if higher or equal, False otherwise.
        :rtype: bool

        """

        version = int(AddonSettings.get_kodi_version().split(".")[0])
        return version >= min_value
    #endregion

    #region Generic Access to Settings from other modules
    @staticmethod
    def get_setting(setting_id, store=KODI):
        """Returns the setting for the requested ID, from the cached settings.

        Arguments:
        settingId - string - the ID of the settings

        Returns:

        :type setting_id:   str
        :param setting_id:  The ID of the setting to retrieve.

        :type store:        str
        :param store:       Whether to retrieve it from the Kodi (KODI) or in the Retrospect (LOCAL) store

        :rtype:             str
        :return:            The configured Kodi add-on values for that <id>.

        """

        value = AddonSettings.store(store).get_setting(setting_id)
        return value

    @staticmethod
    def set_setting(setting_id, value, store=KODI):
        """Sets the value for the setting with requested ID, from the cached settings.

        :type setting_id:  str
        :param setting_id: The ID of the setting to store.

        :type value:       str
        :param value:      The value to store.

        :type store:       str
        :param store:      Whether to store in Kodi (KODI) or in the Retrospect (LOCAL) store

        :return: The configured Kodi add-on values for that <id>.
        :rtype:  str

        """

        AddonSettings.store(store).set_setting(setting_id, value)
        return value

    @staticmethod
    def get_channel_setting(channel, setting_id, value_for_none=None, store=KODI):
        """ Retrieves channel settings for the given channel

        :param channel:       The channel object to get the channels for

        :type setting_id:       str
        :param setting_id:      The ID of the setting to retrieve.

        :type value_for_none:   str
        :param value_for_none:  What value should we interpret as None?

        :type store:            str
        :param store:           Whether to retrieve it from the Kodi (KODI) or in the Retrospect
                                (LOCAL) store.

        :return: the setting with the given <id> for within the <channel>
        :rtype: str

        """

        return AddonSettings.store(store).get_setting(setting_id, channel, value_for_none)

    @staticmethod
    def set_channel_setting(channel, setting_id, value, store=KODI):
        """ Retrieves channel settings for the given channel

        :param channel:         The channel object to get the channels for
        :param str setting_id:  The ID of the setting to store.
        :param str value:      The value to store.
        :param str store:       Whether to store in Kodi (KODI) or in the Retrospect (LOCAL) store

        :return: The configured Kodi add-on values for that <id>.
        :rtype:  str

        """

        return AddonSettings.store(store).set_setting(setting_id, value, channel)
    #endregion

    #region Showing and hiding of items
    @staticmethod
    def show_cloaked_items():
        """ Should we show cloaked items?

        :return: Indication weheter or not to show cloaked items.
        :rtype: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("show_cloaked_items")

    @staticmethod
    def show_categories():
        """ Returns an indication whether channels should be nested under categories or not.

        :rtype: bool
        :return: Indication if we should show categories.

        """

        return AddonSettings.store(KODI).get_boolean_setting("show_categories")

    @staticmethod
    def show_drm_paid_warning():
        """ Should we show a DRM warning on DRM protected (^) items?

        :return: Yes or No.
        :rtype: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("show_drm_warning")

    @staticmethod
    def hide_fanart():
        """ Should we hide Fanart?

        :return: Yes or No
        :type: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("hide_fanart")

    @staticmethod
    def hide_drm_items():
        """ Returns whether or not to hide DRM protected items.

        :return: True/False
        :type: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("hide_drm")

    @staticmethod
    def hide_premium_items():
        """ Returns whether or not to hide Premium/Paid items.

        :return: True/False
        :type: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("hide_premium")

    @staticmethod
    def hide_restricted_folders():
        """ Should we hide restricted folders?

        :return: Indaction if the restricted folders should be hidden
        :rtype: bool

        """

        values = [True, False]
        value = AddonSettings.store(KODI).get_integer_setting("hide_types", default=0)
        return values[value]

    @staticmethod
    def hide_first_time_messages():
        """ Indication if we should show or hide the channel initialization messages

        :return: returns true if the first time messages should be shown.
        :rtype: bool

        """

        return AddonSettings.store(KODI).\
            get_boolean_setting("hide_first_time_message", default=False)
    #endregion

    #region Geo and region stuff
    @staticmethod
    def get_available_countries(as_string=False, as_country_codes=False):
        """ returns the all available ProxyGroupId's in order. The countries are:

             :param bool as_country_codes:  Returns alls the actual country codes values.
             :param bool as_string:         Returns the translation ID for all the possible country
                                            codes as strings.

             :return: List[str] A list of either country codes or translation ID's

             * other - Other languages
             * uk    - United Kingdom
             * nl    - The Netherlands
             * se    - Sweden
             * no    - Norway
             * de    - Germany
             * be    - Belgium
             * ee    - Estonia
             * lt    - Lithuani
             * lv    - Latvia
             * dk    - Danish

        """

        proxy_ids = [30025, 30300, 30301, 30307, 30302, 30305, 30309, 30306, 30308, 30303, 30304]
        proxy_codes = [None, "other", "nl", "uk", "se", "no", "de", "be", "ee", "lt", "lv"]

        if as_string:
            return map(lambda i: str(i), proxy_ids)

        if as_country_codes:
            return proxy_codes

        return proxy_ids

    @staticmethod
    def hide_geo_locked_items_for_location(channel_region, value_only=False):
        """ Returs the config value that indicates what if we should hide items that are geografically
        locked to the region of the channel (indicated by the channel language).

        :param str|None channel_region:  the channel region (actually the channel language)
        :param bool value_only:     if set to True, it will return the settings value

        :return: Indication if Retrospect should hide the items that are geo-locked to the given
                 reason.

        """

        # This list is taken from the settings_templates.xml: geo_region
        # 30074    |30306|30309|30308|30307|30303|30304|30301|30305|30302
        # Disabled |be   |de   |ee   |en-gb|lt   |lv   |nl   |no   |se
        values = [None, "be", "de", "ee", "en-gb", "lt", "lv", "nl", "no", "se"]
        value_index = AddonSettings.store(KODI).get_integer_setting("geo_region", default=0)
        current_geograffical_region = values[value_index]

        if value_only:
            return current_geograffical_region

        # if no geo region is selected, always show everything.
        if current_geograffical_region is None:
            return False

        # only hide if the regions don't match
        return not current_geograffical_region == channel_region
    #endregion

    #region Language caching
    @staticmethod
    def set_language():
        """ Sets the language of the current Plugin run. The value is taken from the Kodi API """

        language = xbmc.getLanguage()
        if AddonSettings.__language_current != language:
            AddonSettings.__language_strings = {}
            Logger.Info("Setting language from %s to %s", AddonSettings.__language_current, language)
            AddonSettings.__language_current = language

        return

    @staticmethod
    def get_localized_string(string_id):
        """ returns a localized string for this id

        Arguments:
        :param int string_id: The ID for the string

        :return: the localized string for this ID.
        :rtype: str

        """

        translation = AddonSettings.__language_strings.get(string_id, None)
        if translation is None:
            translation = AddonSettings.store(KODI).get_localized_string(string_id)
            AddonSettings.__language_strings[string_id] = translation

        return translation
    #endregion

    @staticmethod
    def send_usage_statistics():
        """ returns true if the user allows usage statistics sending

        :return: Indication if sending GA statistics is allowed.
        :rtype: bool

        """

        return AddonSettings.store(KODI).get_boolean_setting("send_statistics", default=True)

    @staticmethod
    def get_current_addon_xml_md5():
        """ Retrieves the current addons.xml.md5 content that was cached in the settings.

        :return: the curreent addons.xml.md5 content
        :rtype: str

        """

        return AddonSettings.store(LOCAL).get_setting(AddonSettings.__MD5_HASH_VALUE)

    @staticmethod
    def update_current_addon_xml_md5(hash_value):
        """ Update the local cache with a new addons.xml.md5 hash value

        :param str hash_value: The MD5 Hash value

        """

        AddonSettings.store(LOCAL).set_setting(AddonSettings.__MD5_HASH_VALUE, hash_value)

    @staticmethod
    def GetClientId():
        CLIENT_ID = "client_id"
        clientId = AddonSettings.store(LOCAL).get_setting(CLIENT_ID)
        if not clientId:
            clientId = AddonSettings.store(KODI).get_setting(CLIENT_ID)
            if clientId:
                Logger.Info("Moved ClientID to local storage")
                AddonSettings.store(LOCAL).set_setting(CLIENT_ID, clientId)
                return clientId

            clientId = str(uuid.uuid1())
            Logger.Debug("Generating new ClientID: %s", clientId)
            AddonSettings.store(LOCAL).set_setting(CLIENT_ID, clientId)
        return clientId

    @staticmethod
    def UseAdaptiveStreamAddOn(withEncryption=False):
        """ Should we use the Adaptive Stream add-on?

        :param withEncryption: do we need to decrypte script
        :return: boolean

        """

        # check the Retrospect add-on setting perhaps?
        useAddOn = \
            AddonSettings.store(KODI).get_boolean_setting("use_adaptive_addon", default=True)
        if not useAddOn:
            Logger.Info("Adaptive Stream add-on disabled from Retrospect settings")
            return useAddOn

        # we should use it, so if we can't find it, it is not so OK.
        adaptiveAddOnId = "inputstream.adaptive"
        adaptiveAddOnInstalled = \
            xbmc.getCondVisibility('System.HasAddon("{0}")'.format(adaptiveAddOnId)) == 1

        if not adaptiveAddOnInstalled:
            Logger.Warning("Adaptive Stream add-on '%s' is not installed/enabled.", adaptiveAddOnId)
            return False

        kodiLeia = AddonSettings.is_min_version(18)
        Logger.Info("Adaptive Stream add-on '%s' %s decryption support was found.",
                    adaptiveAddOnId, "with" if kodiLeia else "without")

        if withEncryption:
            return kodiLeia

        return adaptiveAddOnInstalled

    @staticmethod
    def UpdateUserAgent():
        """ Creates a user agent for this instance of XOT

        this is a very slow action on lower end systems (ATV and rPi) so we minimize the number of runs

        :return: Nothing

        Actual:
        User-Agent: Kodi/16.1 (Windows NT 10.0; WOW64) App_Bitness/32 Version/16.1-Git:20160424-c327c53
        Retro:
        User-Agent: Kodi/16.1 Git:20160424-c327c53 (Windows 10;AMD64; http://kodi.tv)

        Firefox:
        User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0
        """

        # there are slow imports, so only do them here
        import platform
        from envcontroller import EnvController

        # noinspection PyNoneFunctionAssignment
        version = AddonSettings.get_kodi_version()
        Logger.Debug("Found Kodi version: %s", version)
        git = ""
        try:
            # noinspection PyNoneFunctionAssignment
            if "Git:" in version:
                version, git = version.split("Git:", 1)
            version = version.rstrip()

            # The platform.<method> are not working on rPi and IOS
            # kernel = platform.architecture()
            # Logger.Trace(kernel)

            # machine = platform.machine()
            # Logger.Trace(machine)

            uname = platform.uname()
            Logger.Trace(uname)
            if git:
                userAgent = "Kodi/%s (%s %s; %s; http://kodi.tv) Version/%s Git:%s" % \
                            (version, uname[0], uname[2], uname[4], version, git)
            else:
                userAgent = "Kodi/%s (%s %s; %s; http://kodi.tv) Version/%s" % \
                            (version, uname[0], uname[2], uname[4], version)
        except:
            Logger.Warning("Error setting user agent", exc_info=True)
            currentEnv = EnvController.GetPlatform(True)
            # Kodi/14.2 (Windows NT 6.1; WOW64) App_Bitness/32 Version/14.2-Git:20150326-7cc53a9
            userAgent = "Kodi/%s (%s; <unknown>; http://kodi.tv)" % (version, currentEnv)

        # now we store it
        AddonSettings.store(LOCAL).set_setting(AddonSettings.__USER_AGENT_SETTING, userAgent)
        AddonSettings.__UserAgent = userAgent
        Logger.Info("User agent set to: %s", userAgent)
        return

    @staticmethod
    def GetUserAgent():
        """ Retrieves a user agent string for this XBMC instance.

        :return: a user-agent string
        """

        if not AddonSettings.__UserAgent:
            # load and cache
            userAgent = AddonSettings.store(LOCAL).get_setting(AddonSettings.__USER_AGENT_SETTING)
            AddonSettings.__UserAgent = userAgent

            # double check if the version of XBMC is still OK
            if AddonSettings.__UserAgent:
                # noinspection PyNoneFunctionAssignment
                version = AddonSettings.get_kodi_version()

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

        return AddonSettings.store(KODI).get_boolean_setting("http_cache", default=True)

    @staticmethod
    def IgnoreSslErrors():
        """ Returns True if SSL errors should be ignored from Python """

        return AddonSettings.store(KODI).get_boolean_setting("ignore_ssl_errors", default=False)

    @staticmethod
    def GetMaxStreamBitrate(channel=None):
        """Returns the maximum bitrate (kbps) for streams specified by the user
        :type channel: Channel for which the stream needs to play.
        """

        setting = "Retrospect"
        if channel is not None:
            setting = AddonSettings.GetMaxChannelBitrate(channel)

        if setting == "Retrospect":
            setting = AddonSettings.store(KODI).get_setting("stream_bitrate")
            Logger.Debug("Using the Retrospect Default Bitrate: %s", setting)
        else:
            Logger.Debug("Using the Channel Specific Bitrate: %s", setting)
        return int(setting or 8000)

    @staticmethod
    def GetMaxChannelBitrate(channel):
        """ Get the maximum channel bitrate configured for the channel. Keep in mind that if
        'Retrospect' was selected, the actual maximum stream bitrate is set by the overall settings.

        :param channel:     The channel to set the bitrate for
        :return:            The bitrate for the channel as a string!
        """
        return AddonSettings.store(LOCAL).get_setting("bitrate", channel, default="Retrospect")

    @staticmethod
    def SetMaxChannelBitrate(channel, bitrate):
        """ Set the maximum channel bitrate

        :param channel:     The channel to set the bitrate for
        :param bitrate:     the maximum bitrate

        """
        AddonSettings.store(LOCAL).set_setting("bitrate", bitrate, channel=channel)

    @staticmethod
    def GetFolderPrefix():
        """ returns the folder prefix """

        setting = AddonSettings.store(KODI).get_setting("folder_prefix", default="")
        return setting

    @staticmethod
    def MixFoldersAndVideos():
        """ Should we treat Folders and Videos alike """

        return AddonSettings.store(KODI).get_boolean_setting("folders_as_video", default=False)

    @staticmethod
    def GetEmptyListBehaviour():
        """
        :return: returns the behaviour for empty lists:

        0 = Error
        1 = Empty List
        2 = Dummy

        """

        setting = AddonSettings.store(KODI).\
            get_integer_setting("empty_folder", default=2)

        if setting == 0:
            return "error"
        elif setting == 1:
            return "empty"
        else:
            return "dummy"

    @staticmethod
    def UseSubtitle():
        """Returns whether to show subtitles or not"""

        setting = AddonSettings.store(KODI).get_setting("subtitle_mode", default="0")

        if setting == "0":
            return True
        else:
            return False

    @staticmethod
    def GetListLimit():
        """ Retrieves the limit for a list before it is grouped alphabetically.


        :return: an integer with the limit
        """

        limit = AddonSettings.store(KODI).get_integer_setting("list_limit", default=5)
        return [-1, 10, 50, 75, 100, 150, 200, 1000][limit]

    @staticmethod
    def GetLogLevel():
        """ Returns True if the add-on should do trace logging """

        level = AddonSettings.store(KODI).get_integer_setting("log_level", default=2)

        # the return value is zero based. 0 -> Trace , 1=Debug (10), 2 -> Info (20)
        return int(level) * 10

    @staticmethod
    def SetChannelVisiblity(channel, visible):
        """ Sets the visibility for the give channel.

        :param channel: the ChannelInfo object
        :param visible: indication for visibility

        """

        AddonSettings.store(LOCAL).set_setting("visible", visible, channel)

    @staticmethod
    def GetChannelVisibility(channel):
        """Check if the channel should be shown

        Arguments:
        channel : Channel - The channel to check.

        """

        return AddonSettings.store(LOCAL).get_boolean_setting("visible", channel, default=True)

    @staticmethod
    def ShowChannelSettings(channel):
        """ Show the add-on settings and pre-selects the channel settings tab with the correct channel
        selected.

        :param channel: The channel to display settings for.
        """

        channelName = channel.safeName

        # remove some HTML chars
        channelName = HtmlEntityHelper.convert_html_entities(channelName)
        Logger.Debug("Showing channel settings for channel: %s (%s)", channelName, channel.channelName)

        # Set the channel to be the preselected one
        AddonSettings.store(KODI).set_setting("config_channel", channelName)

        # show settings and focus on the channel settings tab
        if AddonSettings.is_min_version(18):
            return AddonSettings.ShowSettings(-98)
        else:
            return AddonSettings.ShowSettings(102)

    @staticmethod
    def ShowSettings(tabId=None, settingId=None):
        """Shows the settings dialog
        :param tabId:       what tab should have focus in the settings?
        :param settingId:   what control should have focus in the settings tab?

        """

        if tabId is None:
            # shows the settings and blocks:
            AddonSettings.store(KODI).open_settings()  # this will open settings window
            # reload the cache because stuff might have changed

            Logger.Info("Clearing Settings cache because settings dialog was shown.")
            AddonSettings.__refresh(KODI)
        else:
            # show settings and focus on a tab
            xbmc.executebuiltin('Addon.OpenSettings(%s)' % (Config.addonId,))

            if tabId:
                # the 100 range are the tabs
                # the 200 range are the controls in a tab
                xbmc.executebuiltin('SetFocus(%i)' % int(tabId))
                if settingId:
                    xbmc.executebuiltin('SetFocus(%s)' % int(settingId))

            Logger.Info("Settings shown with focus on %s-%s", tabId, settingId or "<none>")
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
                                 * be    - Belgium
                                 * en-gb - British
                                 * ee    - Estoniam
                                 * no    - Norwegian
                                 * dk    - Danish
                                 * None  - Other languages

        Returns:
        True if the channels should be shown. If the lookup does not match
        a NotImplementedError is thrown.

        """
        (settingsId, settingsLabel) = AddonSettings.__GetLanguageSettingsIdAndLabel(languageCode)
        return AddonSettings.store(KODI).get_boolean_setting(settingsId, default=True)

    @staticmethod
    def get_local_ip_header_for_channel(channel_info):
        """ returns the local IP for a specific channel

        :param channel_info: ChannelInfo - The channel to get proxy info for

        :return: The LocalIP related x-forwarded-for HTTP Header
        :rtype: dict

        """

        if AddonSettings.__NoProxy:
            return None

        prefix = AddonSettings.GetLocalIPHeaderCountryCodeForChannel(channel_info)
        if prefix is None:
            Logger.Debug("No Local IP configured for %s", channel_info)
            return None

        Logger.Debug("Country settings '%s' configured for Local IP for %s", prefix, channel_info)

        server = AddonSettings.store(KODI).get_setting("%s_local_ip" % (prefix,), default=None)
        if not server:
            Logger.Debug("No Local IP found for country '%s'", prefix)
            return None

        Logger.Debug("Found Local IP for channel %s:\nLocal IP: %s", channel_info, server)
        return {"X-Forwarded-For": server}

    @staticmethod
    def GetLocalIPHeaderCountryCodeForChannel(channelInfo):
        """ Returns the Country code for the LocalIP that is configured for this channel

        :param channelInfo:  The ChannelInfo object
        :return:             2 character ISO country code

        """
        if AddonSettings.__NoProxy:
            return None

        countryCode = AddonSettings.store(LOCAL).\
            get_setting(AddonSettings.__LOCAL_IP_SETTING, channelInfo)
        return countryCode

    @staticmethod
    def SetLocalIPForChannel(channelInfo, countryCode):
        """ Sets the country code for the local IP for a channel

        Arguments:
        channelInfo : ChannelInfo - The channel
        proxyIndex  : Integer     - The Proxy Index

        """

        if countryCode == "other":
            Logger.Warning("LocalIP updating to 'other' which is invalid. Setting it to None.")
            countryCode = None

        AddonSettings.store(LOCAL).\
            set_setting(AddonSettings.__LOCAL_IP_SETTING, countryCode, channel=channelInfo)
        return

    # noinspection PyUnusedLocal
    @staticmethod
    def GetProxyForChannel(channelInfo):
        """ returns the proxy for a specific channel

        Arguments:
        channelInfo : ChannelInfo - The channel to get proxy info for

        """

        if AddonSettings.__NoProxy:
            return None

        prefix = AddonSettings.GetProxyCountryCodeForChannel(channelInfo)
        if prefix is None:
            Logger.Debug("No proxy configured for %s", channelInfo)
            return None

        Logger.Debug("Country settings '%s' configured for Proxy for %s", prefix, channelInfo)

        server = AddonSettings.store(KODI).get_setting("%s_proxy_server" % (prefix,))
        port = AddonSettings.store(KODI).get_integer_setting("%s_proxy_port" % (prefix,), default=0)
        proxyType = AddonSettings.store(KODI).get_setting("%s_proxy_type" % (prefix,))

        if not proxyType or proxyType.lower() not in ('dns', 'http') or not server:
            Logger.Debug("No proxy found for country '%s'", prefix)
            return None

        username = AddonSettings.store(KODI).\
            get_setting("%s_proxy_username" % (prefix,), default="")
        password = AddonSettings.store(KODI).\
            get_setting("%s_proxy_password" % (prefix,), default="")

        pInfo = ProxyInfo(server, port, scheme=proxyType.lower(), username=username, password=password)
        Logger.Debug("Found proxy for channel %s:\n%s", channelInfo, pInfo)
        return pInfo

    @staticmethod
    def GetProxyCountryCodeForChannel(channelInfo):
        """ Returns the Country code for the proxy that is configured for this channel

        :param channelInfo:  The ChannelInfo object
        :return:             2 character ISO country code

        """

        if AddonSettings.__NoProxy:
            return None

        countryCode = AddonSettings.store(LOCAL).\
            get_setting(AddonSettings.__PROXY_SETTING, channelInfo)
        return countryCode

    @staticmethod
    def SetProxyIdForChannel(channelInfo, countryCode):
        """ Sets the country code for the proxy for a channel

        Arguments:
        channelInfo : ChannelInfo - The channel
        proxyIndex  : Integer     - The Proxy Index

        """

        AddonSettings.store(LOCAL).\
            set_setting(AddonSettings.__PROXY_SETTING, countryCode, channelInfo)
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
        # noinspection PyArgumentEqualDefault
        settingsXml = open(filenameTemplate, "r")
        contents = settingsXml.read()
        settingsXml.close()

        newContents = AddonSettings.__UpdateAddOnSettingsWithCountrySettings(contents, channels)
        newContents, settingsOffsetForVisibility, channelsWithSettings = \
            AddonSettings.__UpdateAddOnSettingsWithChannelSettings(newContents, channels)
        newContents = AddonSettings.__UpdateAddOnSettingsWithChannelSelection(newContents, channelsWithSettings)

        # Now fill the templates, we only import here due to performance penalties of the
        # large number of imports.
        from helpers.templatehelper import TemplateHelper
        th = TemplateHelper(Logger.Instance(), template=newContents)
        newContents = th.Transform()

        # Finally we insert the new XML into the old one
        filename = os.path.join(config.rootDir, "resources", "settings.xml")
        filenameTemp = os.path.join(config.rootDir, "resources", "settings.tmp.xml")
        try:
            # Backup the user profile settings.xml because sometimes it gets reset. Because in some
            # concurrency situations, Kodi might decide to think we have no settings and just
            # erase all user settings.
            userSettings = os.path.join(Config.profileDir, "settings.xml")
            userSettingsBackup = os.path.join(Config.profileDir, "settings.old.xml")
            Logger.Debug("Backing-up user settings: %s", userSettingsBackup)
            if os.path.isfile(userSettings):
                shutil.copy(userSettings, userSettingsBackup)
            else:
                Logger.Warning("No user settings found at: %s", userSettings)

            # Update the addonsettings.xml by first updating a temp xml file.
            Logger.Debug("Creating new settings.xml file: %s", filenameTemp)
            Logger.Trace(newContents)
            settingsXml = open(filenameTemp, "w+")
            settingsXml.write(newContents)
            settingsXml.close()
            Logger.Debug("Replacing existing settings.xml file: %s", filename)
            shutil.move(filenameTemp, filename)

            # restore the user profile settings.xml file when needed
            if os.path.isfile(userSettings) and os.stat(userSettings).st_size != os.stat(userSettingsBackup).st_size:
                Logger.Critical("User settings.xml was overwritten during setttings update. Restoring from %s", userSettingsBackup)
                shutil.copy(userSettingsBackup, userSettings)
        except:
            Logger.Error("Something went wrong trying to update the settings.xml", exc_info=True)
            try:
                settingsXml.close()
            except:
                pass

            #  clean up time file
            if os.path.isfile(filenameTemp):
                os.remove(filenameTemp)

            # restore original settings
            settingsXml = open(filenameTemp, "w+")
            settingsXml.write(contents)
            settingsXml.close()
            shutil.move(filenameTemp, filename)
            return

        Logger.Info("Settings.xml updated succesfully. Reloading settings.")
        AddonSettings.__refresh(KODI)
        return

    @staticmethod
    def __UpdateAddOnSettingsWithChannelSelection(contents, channels):
        """ Adds the settings part that allows the selection of the channel for which the channel settings should
        be displayed.

        :param contents: The current settings
        :param channels: The available channels
        :return: updated contents

        """

        if "<!-- start of active channels -->" not in contents:
            Logger.Error("No '<!-- start of active channels -->' found in settings.xml. Stopping updating.")
            return

        # Create new XML
        channelSelectionXml = '        <!-- start of active channels -->\n' \
                              '        <setting id="config_channel" type="select" label="30040" values="'
        channelSafeNames = "|".join(map(lambda c: c.safeName, channels))
        channelSelectionXml = "%s%s" % (channelSelectionXml, channelSafeNames)
        channelSelectionXml = '%s" />' % (channelSelectionXml.rstrip("|"),)

        # replace the correct parts
        begin = contents[:contents.find('<!-- start of active channels -->')].strip()
        end = contents[contents.find('<!-- end of active channels -->'):].strip()
        contents = "%s\n%s\n        %s" % (begin, channelSelectionXml, end)
        return contents

    @staticmethod
    def __UpdateAddOnSettingsWithChannelSettings(contents, channels):
        """ Adds the channel specific settings

        :param contents: The current settings
        :param channels: The available channels
        :return: updated contents and the offset in visibility

        This method first aggregates the settings and then adds them.

        """

        if "<!-- begin of channel settings -->" not in contents:
            Logger.Error("No '<!-- begin of channel settings -->' found in settings.xml. Stopping updating.")
            return

        settings = dict()
        channelsWithSettings = []

        # There are 2 settings between the selector list and the channel settings in the settings_template.xml
        settingOffsetForVisibility = 2

        # Let's make sure they are sorted by channel module. So we first go through them all and then create
        # the XML.
        for channel in channels:
            if channel.moduleName not in settings:
                settings[channel.moduleName] = []

            # First any specific settings
            if channel.settings:
                # Sort the settings so they are really in the correct order, because this is not guaranteed by the
                # json parser
                channel.settings.sort(lambda a, b: cmp(a["order"], b["order"]))
                for channelSettings in channel.settings:
                    settingId = channelSettings["id"]
                    settingValue = channelSettings["value"]
                    Logger.Debug("Adding setting: '%s' with value '%s'", settingId,
                                 settingValue)

                    if settingValue.startswith("id="):
                        settingXmlId = settingValue[4:settingValue.index('"', 4)]
                        settingXml = "<setting %s visible=\"eq(-{0},%s)\" />" % \
                                     (settingValue, channel.safeName)
                    else:
                        settingXmlId = "channel_{0}_{1}".format(channel.guid, settingId)
                        settingXml = '<setting id="%s" %s visible=\"eq(-{0},%s)\" />' % \
                                     (settingXmlId, settingValue, channel.safeName)

                    # existingSettingXmlIndex = []
                    # for i, elem in enumerate(settings[channel.moduleName]):
                    #     if 'aa' in elem:
                    #         existingSettingXmlIndex.append(i)
                    #
                    # Alternatively, as a list comprehension:
                    #
                    # indices = [i for i, elem in enumerate(settings[channel.moduleName]) if 'aa' in elem]

                    existingSettingXmlIndex = [i for i, s in
                                               enumerate(settings[channel.moduleName]) if
                                               settingXmlId in s]
                    if not existingSettingXmlIndex:
                        settings[channel.moduleName].append((settingXmlId, settingXml))
                    else:
                        xmlIndex = existingSettingXmlIndex[0]
                        # we need to OR the visibility
                        settingTuple = settings[channel.moduleName][xmlIndex]
                        setting = settingTuple[1].replace(
                            'visible="', 'visible="eq(-{0},%s)|' % (channel.safeName,))
                        settings[channel.moduleName][xmlIndex] = (settingTuple[0], setting)

            # remove if no settings else, add them to the list with settings
            if len(settings[channel.moduleName]) == 0:
                settings.pop(channel.moduleName)
            else:
                channelsWithSettings.append(channel)

        xmlContent = '\n        <!-- begin of channel settings -->\n'
        # Sort them to make the result more consistent
        # noinspection PyUnresolvedReferences
        settingKeys = settings.keys()
        settingKeys.sort()
        for pyModule in settingKeys:
            xmlContent = '%s        <!-- %s.py -->\n' % (xmlContent, pyModule)
            for settingXmlId, setting in settings[pyModule]:
                settingOffsetForVisibility += 1
                xmlContent = "%s        %s\n" % (xmlContent, setting.format(settingOffsetForVisibility))

        begin = contents[:contents.find('<!-- begin of channel settings -->')].strip()
        end = contents[contents.find('<!-- end of channel settings -->'):]

        Logger.Trace("Generated channel settings:\n%s", xmlContent)
        contents = "%s\n%s\n        %s" % (begin, xmlContent.rstrip(), end)
        return contents, settingOffsetForVisibility, channelsWithSettings

    @staticmethod
    def __UpdateAddOnSettingsWithCountrySettings(contents, channels):
        """ Adds the channel showing/hiding to the settings.xml

        :param contents: The current settings
        :param channels: The available channels
        :return: updated contents and the offset in visibility

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

        for language in languageLookupSortedKeys:
            channelXml = '%s        <setting id="%s" type="bool" label="%s" subsetting="false" default="true" />\n' \
                         % (channelXml, languageLookup[language][0], languageLookup[language][1])

        begin = contents[:contents.find('<!-- start of channel selection -->')].strip()
        end = contents[contents.find('<!-- end of channel selection -->'):].strip()
        contents = "%s\n    \n%s        %s" % (begin, channelXml, end)
        return contents

    @staticmethod
    def __GetLanguageSettingsIdAndLabel(languageCode):
        """ returns the settings xml part for this language

        Arguments:
        languageCode - String - The language string

        Returns:
        A tupple with the label and the settingsId.

        """

        if languageCode == "nl":
            return "show_dutch", 30301
        elif languageCode == "fi":
            return "show_finnish", 30302
        elif languageCode == "se":
            return "show_swedish", 30302
        elif languageCode == "lt":
            return "show_lithuanian", 30303
        elif languageCode == "lv":
            return "show_latvian", 30304
        elif languageCode == "en-gb":
            return "show_engb", 30307
        elif languageCode == "no":
            return "show_norwegian", 30305
        elif languageCode == "be":
            return "show_belgium", 30306
        elif languageCode == "ee":
            return "show_estonia", 30308
        elif languageCode == "dk":
            return "show_danish", 30310
        elif languageCode == "de":
            return "show_german", 30309
        elif languageCode is None:
            return "show_other", 30300
        else:
            raise NotImplementedError("Language code not supported: '%s'" % (languageCode, ))

    @staticmethod
    def __SortChannels(x, y):
        """ compares 2 channels based on language and then sortorder """

        value = cmp(x.language, y.language)
        if value == 0:
            return cmp(x.sortOrder, y.sortOrder)
        else:
            return value

    @staticmethod
    def PrintSettingValues():
        """Prints the settings"""

        pattern = "%s\n%s: %s"
        value = "%s: %s" % ("ClientId", AddonSettings.GetClientId())
        value = pattern % (value, "MaxStreamBitrate", AddonSettings.GetMaxStreamBitrate())
        value = pattern % (value, "UseSubtitle", AddonSettings.UseSubtitle())
        value = pattern % (value, "CacheHttpResponses", AddonSettings.CacheHttpResponses())
        value = pattern % (value, "Folder Prefx", "'%s'" % AddonSettings.GetFolderPrefix())
        value = pattern % (value, "Mix Folders & Videos", AddonSettings.MixFoldersAndVideos())
        value = pattern % (value, "Empty List Behaviour", AddonSettings.GetEmptyListBehaviour())
        value = pattern % (value, "ListLimit", AddonSettings.GetListLimit())
        value = pattern % (value, "Loglevel", AddonSettings.GetLogLevel())
        value = pattern % (value, "Ignore SSL Errors", AddonSettings.IgnoreSslErrors())
        value = pattern % (value, "Geo Location", AddonSettings.hide_geo_locked_items_for_location(None, value_only=True))
        value = pattern % (value, "Filter Folders", AddonSettings.hide_restricted_folders())
        value = pattern % (value, "DRM/Paid Warning", AddonSettings.show_drm_paid_warning())
        value = pattern % (value, "Hide DRM Items", AddonSettings.hide_drm_items())
        value = pattern % (value, "Hide Premium Items", AddonSettings.hide_premium_items())
        value = pattern % (value, "Show Cloaked Items", AddonSettings.show_cloaked_items())
        value = pattern % (value, "Show Dutch", AddonSettings.ShowChannelWithLanguage("nl"))
        value = pattern % (value, "Show Swedish", AddonSettings.ShowChannelWithLanguage("se"))
        value = pattern % (value, "Show Lithuanian", AddonSettings.ShowChannelWithLanguage("lt"))
        value = pattern % (value, "Show Latvian", AddonSettings.ShowChannelWithLanguage("lv"))
        value = pattern % (value, "Show British", AddonSettings.ShowChannelWithLanguage("en-gb"))
        value = pattern % (value, "Show German", AddonSettings.ShowChannelWithLanguage("de"))
        value = pattern % (value, "Show Finnish", AddonSettings.ShowChannelWithLanguage("fi"))
        value = pattern % (value, "Show Other languages", AddonSettings.ShowChannelWithLanguage(None))

        if AddonSettings.__NoProxy:
            return value

        try:
            proxies = AddonSettings.get_available_countries(as_country_codes=True)
            for country in proxies:
                if country is None:
                    continue
                elif country == "other":
                    country = country.title()
                else:
                    country = country.upper()

                proxyTitle = "{0} Proxy".format(country)
                proxyValue = "{0} ({1})".format(
                    AddonSettings.store(KODI).get_setting(
                        "{0}_proxy_server".format(country.lower()), default="Not Set"),
                    AddonSettings.store(KODI).get_setting(
                        "{0}_proxy_type".format(country.lower()), default="Not Set"))
                value = pattern % (value, proxyTitle, proxyValue)

                proxyPortTitle = "{0} Proxy Port".format(country)
                proxyPortValue = \
                    AddonSettings.store(KODI).get_integer_setting(
                        "{0}_proxy_port".format(country.lower()), default=0)
                value = pattern % (value, proxyPortTitle, proxyPortValue)

                localIpTitle = "{0} Local IP".format(country)
                localIpValue = AddonSettings.store(KODI). \
                    get_setting("{0}_local_ip".format(country.lower()), default="Not Set")
                value = pattern % (value, localIpTitle, localIpValue)
        except:
            Logger.Error("Error", exc_info=True)
        return value
