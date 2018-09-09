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
import sys
import os
import io
import shutil
import datetime
import time

import envcontroller

from addonsettings import AddonSettings
from regexer import Regexer
from environments import Environments
from xbmcwrapper import XbmcWrapper
from helpers.languagehelper import LanguageHelper
from config import Config
from channelinfo import ChannelInfo
from logger import Logger
from helpers.jsonhelper import JsonHelper
from textures import TextureHandler
from version import Version
from stopwatch import StopWatch


class ChannelIndex:
    """ Class that handles the deploying and loading of available channels."""

    __channelIndexer = None  # : Property to store the channel indexer in.

    @staticmethod
    def get_register():
        """ Returns the current active channel register.

        Used for backward compatibility with Xbox.

        """

        valid_for = datetime.timedelta(minutes=1)
        # In Kodi Leia the Python instance is not killed and the ChannelRegister stays alive.
        # This might cause some issues. So better to let it expire after some time. But to make it
        # not happen during a user's browsing session, we use sliding expiration of 1 minute.

        if not ChannelIndex.__channelIndexer:
            Logger.Debug("Creating a new ChannelIndex-er.")
            ChannelIndex.__channelIndexer = ChannelIndex()
        elif ChannelIndex.__channelIndexer.validAt + valid_for < datetime.datetime.now():
            Logger.Debug("Existing ChannelIndex-er expired. Creating a new ChannelIndex-er.")
            ChannelIndex.__channelIndexer = ChannelIndex()
        else:
            Logger.Debug("Using an existing %s.", ChannelIndex.__channelIndexer)
            # We are using a sliding expiration, so we should let the expiration slide.
            ChannelIndex.__channelIndexer.validAt = datetime.datetime.now()

        return ChannelIndex.__channelIndexer

    def __init__(self):
        """ Initialize the importer by reading the channels from the channel
        resource folder and will start the import of the channels

        It also deploys the channels from the retrospect\deploy folder.

        """

        self.__INTERNAL_CHANNEL_PATH = "channels"
        self.__CHANNEL_INDEX_CHANNEL_KEY = "channels"
        self.__CHANNEL_INDEX_ADD_ONS_KEY = "add-ons"
        self.__CHANNEL_INDEX_CHANNEL_INFO_KEY = "info"
        self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY = "version"
        self.__CHANNEL_INDEX = os.path.join(Config.profileDir, "channelindex.json")

        # initialise the collections
        self.__allChannels = []  # list of all available channels

        self.__reindexed = False
        self.__reindex = self.__deploy_new_channels()
        self.__channelIndex = self.__get_index()

        self.validAt = datetime.datetime.now()
        self.id = int(time.time())
        return

    def get_channel(self, class_name, channel_code, info_only=False):
        """ Fetches a single channel for a given className and channelCode

        If updated channels are found, the those channels are indexed and the
        channel index is rebuild.

        @param class_name:       the chn_<name> class name
        @param channel_code:     a possible channel code within the channel set
        @param info_only:        only return the ChannelInfo
        @return:                 a Channel object

        """

        channel_set = self.__channelIndex[self.__CHANNEL_INDEX_CHANNEL_KEY].get(class_name, None)
        if channel_set is None:
            Logger.Error("Could not find info for channelClass '%s'.", class_name)
            return None

        channel_set_info_path = channel_set[self.__CHANNEL_INDEX_CHANNEL_INFO_KEY]
        channel_set_version = channel_set[self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY]
        if not os.path.isfile(channel_set_info_path) and not self.__reindexed:
            Logger.Warning("Missing channel_set file: %s.", channel_set_info_path)
            self.__rebuild_index()
            return self.get_channel(class_name, channel_code)

        channel_infos = ChannelInfo.FromJson(channel_set_info_path, channel_set_version)
        if channel_code is None:
            channel_infos = filter(lambda ci: ci.channelCode is None, channel_infos)
        else:
            channel_infos = filter(lambda ci: ci.channelCode == channel_code, channel_infos)

        if len(channel_infos) != 1:
            Logger.Error("Found none or more than 1 matches for '%s' and '%s' in the channel index.",
                         class_name, channel_code or "None")
            return None
        else:
            Logger.Debug("Found single channel in the channel index: %s.", channel_infos[0])

        if self.__is_channel_set_updated(channel_infos[0]):
            # let's see if the index has already been updated this section, of not, do it and
            # restart the ChannelRetrieval.
            if not self.__reindexed:
                # rebuild and restart
                Logger.Warning("Re-index channel index due to channel_set update: %s.", channel_set_info_path)
                self.__rebuild_index()
            else:
                Logger.Warning("Found updated channel_set: %s.", channel_set_info_path)

            # new we should init all channels by loading them all, just to be shure that all is ok
            Logger.Debug("Going to fetching all channels to init them all.")
            self.get_channels()
            return self.get_channel(class_name, channel_code)

        if info_only:
            return channel_infos[0]

        return channel_infos[0].GetChannel()

    # noinspection PyUnusedLocal
    def get_channels(self, include_disabled=False, **kwargs):
        """ Retrieves all enabled channels within Retrospect.

        If updated channels are found, the those channels are indexed and the
        channel index is rebuild.

        @type include_disabled: boolean to indicate if we should include those channels that are
                               explicitly disabled from the settings

        @type kwargs: here for backward compatibility

        @return: a list of ChannelInfo objects of enabled channels.

        """

        sw = StopWatch("ChannelIndex.get_channels Importer", Logger.Instance())
        Logger.Info("Fetching all enabled channels.")

        self.__allChannels = []
        valid_channels = []

        # What platform are we
        platform = envcontroller.EnvController.GetPlatform()

        channels_updated = False
        country_visibility = {}

        for channel_set in self.__channelIndex[self.__CHANNEL_INDEX_CHANNEL_KEY]:
            channel_set = self.__channelIndex[self.__CHANNEL_INDEX_CHANNEL_KEY][channel_set]
            channel_set_info_path = channel_set[self.__CHANNEL_INDEX_CHANNEL_INFO_KEY]
            channel_set_version = channel_set[self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY]

            # Check if file exists. If not, rebuild index
            if not os.path.isfile(channel_set_info_path) and not self.__reindexed:
                Logger.Warning("Missing channelSet file: %s.", channel_set_info_path)
                self.__rebuild_index()
                return self.get_channels()

            channel_infos = ChannelInfo.FromJson(channel_set_info_path, channel_set_version)

            # Check if the channel was updated
            if self.__is_channel_set_updated(channel_infos[0]):
                # let's see if the index has already been updated this section, of not, do it and
                # restart the ChannelRetrieval.
                if not self.__reindexed:
                    # rebuild and restart
                    Logger.Warning("Re-index channel index due to channelSet update: %s.", channel_set_info_path)
                    self.__rebuild_index()
                    return self.get_channels()
                else:
                    Logger.Warning("Found updated channelSet: %s.", channel_set_info_path)

                if not channels_updated:
                    # this was the first update found (otherwise channelsUpdated was True) show a message:
                    title = LanguageHelper.GetLocalizedString(LanguageHelper.InitChannelTitle)
                    text = LanguageHelper.GetLocalizedString(LanguageHelper.InitChannelText)
                    XbmcWrapper.ShowNotification(title, text, displayTime=15000, logger=Logger.Instance())
                channels_updated |= True

                # Initialise the channelset.
                self.__initialise_channel_set(channel_infos[0])

                # And perform all first actions for the included channels in the set
                for channelInfo in channel_infos:
                    self.__initialise_channel(channelInfo)

            # Check the channel validity
            for channelInfo in channel_infos:
                if not self.__channel_is_correct(channelInfo):
                    continue
                self.__allChannels.append(channelInfo)

                # valid channel for this platform ?
                if not channelInfo.compatiblePlatforms & platform == platform:
                    Logger.Warning("Not loading: %s -> platform '%s' is not compatible.",
                                   channelInfo, Environments.Name(platform))
                    continue
                valid_channels.append(channelInfo)

                # was the channel hidden based on language settings? We do some caching to speed
                # things up.
                if channelInfo.language not in country_visibility:
                    country_visibility[channelInfo.language] = AddonSettings.ShowChannelWithLanguage(channelInfo.language)
                channelInfo.visible = country_visibility[channelInfo.language]

                # was the channel explicitly disabled from the settings?
                channelInfo.enabled = AddonSettings.GetChannelVisibility(channelInfo)

                Logger.Debug("Found channel: %s", channelInfo)

        if channels_updated:
            Logger.Info("New or updated channels found. Updating add-on configuration for all channels and user agent.")
            AddonSettings.UpdateAddOnSettingsWithChannels(valid_channels, Config)
            AddonSettings.UpdateUserAgent()
        else:
            Logger.Debug("No channel changes found. Skipping add-on configuration for channels.")
            # TODO: perhaps we should check that the settings.xml is correct and not broken?

        valid_channels.sort()
        visible_channels = filter(lambda c: c.visible and c.enabled, valid_channels)
        Logger.Info("Fetch a total of %d channels of which %d are visible.",
                    len(valid_channels),
                    len(visible_channels))

        sw.Stop()

        if include_disabled:
            return valid_channels

        return visible_channels

    def get_categories(self):
        # type: () -> set
        """ Retrieves the available categories from the channels """

        categories = set()
        channels = self.get_channels()
        map(lambda c: categories.add(c.category), channels)
        Logger.Debug("Found these categories: %s", ", ".join(categories))
        return categories

    def __deploy_new_channels(self):
        # type: () -> bool
        """ Checks the deploy folder for new channels, if present, deploys them

        The last part of the folders in the deploy subfolder are considered the
        channel names. The other part is replaced with the <addon base name>.
        So if the deploy has a folder temp.channelOne and the addon is called
        net.rieter.xot it will be deployed to net.rieter.xot.channel.channelOne.

        The folders are intially removed and then re-created. If the folder in
        the deploy does not have a addon.xml it will not be imported.

        """

        Logger.Debug("Checking for new channels to deploy")

        # location of new channels and list of subfolders
        deploy_path = os.path.join(Config.rootDir, "deploy")
        to_deploy = os.listdir(deploy_path)

        # addons folder, different for XBMC and XBMC4Xbox
        if envcontroller.EnvController.IsPlatform(Environments.Xbox):
            target_folder = os.path.abspath(
                os.path.join(Config.rootDir, self.__INTERNAL_CHANNEL_PATH))
            if not os.path.exists(target_folder):
                os.mkdir(target_folder)
        else:
            target_folder = os.path.abspath(os.path.join(Config.rootDir, ".."))

        deployed = False
        for deploy in to_deploy:
            if deploy.startswith("."):
                continue
            source_path = os.path.join(deploy_path, deploy)

            # find out if the scriptname is not net.rieter.xot and update
            deploy_parts = deploy.split(".")
            dest_deploy = "%s.channel.%s" % (Config.addonDir, deploy_parts[-1])
            destination_path = os.path.join(target_folder, dest_deploy)
            Logger.Info("Deploying Channel Addon '%s' to '%s'", deploy, destination_path)

            if os.path.exists(destination_path):
                Logger.Info("Removing old channel at %s", dest_deploy)
                shutil.rmtree(destination_path)

            # only update if there was a real addon
            if os.path.exists(os.path.join(source_path, "addon.xml")):
                shutil.move(source_path, destination_path)
            else:
                shutil.rmtree(source_path)
            deployed = True

        return deployed

    def __get_index(self):
        # type: () -> dict
        """ Loads the channel index and if there is none, makes sure one is created.

        Checks:
        1. Existence of the index
        2. Channel add-ons in the index vs actual add-ons

        @return:
        """

        # if it was not already re-index and the bit was set
        if self.__reindex:
            if self.__reindexed:
                Logger.Warning("Forced re-index set, but a re-index was already done previously. Not Rebuilding.")
            else:
                Logger.Info("Forced re-index set. Rebuilding.")
                return self.__rebuild_index()

        if not os.path.isfile(self.__CHANNEL_INDEX):
            Logger.Info("No index file found at '%s'. Rebuilding.", self.__CHANNEL_INDEX)
            return self.__rebuild_index()

        try:
            with io.open(self.__CHANNEL_INDEX, 'r', encoding='utf-8') as fd:
                data = fd.read()

            index_json = JsonHelper(data, logger=Logger.Instance())
            Logger.Debug("Loaded index from '%s'.", self.__CHANNEL_INDEX)

            if not self.__is_index_consistent(index_json.json):
                return self.__rebuild_index()
            return index_json.json
        except:
            Logger.Critical("Error reading channel index. Rebuilding.", exc_info=True)
            return self.__rebuild_index()

    def __rebuild_index(self):
        # type: () -> dict
        """ Rebuilds the channel index that contains all channels and performs all necessary steps:

        1. Find all channel add-on paths and determine the version of the channel add-on
        2. For all channel sets in the add-on:
            a. See if it is a new channel set (pyo and pyc check)
            b. If so, initialise the channel set and then perform the first time actions on
               the included channels.
            c. Add all channels within the channel set to the channelIndex

        @return: the new channel index dictionary object.

        Remark: this method only generates the index of the channels, it does not import at all!

        """

        if self.__reindexed:
            Logger.Error("Channel index was already re-indexed this run. Not doing it again.")
            return self.__channelIndex

        Logger.Info("Rebuilding the channel index.")
        index = {
            self.__CHANNEL_INDEX_ADD_ONS_KEY: [],
            self.__CHANNEL_INDEX_CHANNEL_KEY: {}
        }

        # iterate all Retrospect Video Add-ons
        addon_path = self.__get_addon_path()
        channel_path_start = "%s.channel" % (Config.addonDir,)
        add_ons = filter(lambda x: channel_path_start in x and "BUILD" not in x, os.listdir(addon_path))
        for addOnDir in add_ons:
            index[self.__CHANNEL_INDEX_ADD_ONS_KEY].append(addOnDir)

            channel_add_on_path = os.path.join(addon_path, addOnDir)
            channel_add_on_id, channel_add_on_version = self.__validate_add_on_version(channel_add_on_path)
            if channel_add_on_id is None:
                continue

            channel_sets = os.listdir(channel_add_on_path)
            for channelSet in channel_sets:
                if not os.path.isdir(os.path.join(channel_add_on_path, channelSet)):
                    continue

                channel_set_id = "chn_%s" % (channelSet,)
                Logger.Debug("Found channel set '%s'", channel_set_id)
                index[self.__CHANNEL_INDEX_CHANNEL_KEY][channel_set_id] = {
                    self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY: str(channel_add_on_version),
                    self.__CHANNEL_INDEX_CHANNEL_INFO_KEY: os.path.join(channel_add_on_path, channelSet, "%s.json" % (channel_set_id,))
                }

        with io.open(self.__CHANNEL_INDEX, 'w+b') as f:
            f.write(JsonHelper.dump(index))

        # now we marked that we already re-indexed.
        self.__reindexed = True
        self.__channelIndex = index
        Logger.Info("Rebuilding channel index completed with %d channelSets and %d add-ons: %s.",
                    len(index[self.__CHANNEL_INDEX_CHANNEL_KEY]),
                    len(index[self.__CHANNEL_INDEX_ADD_ONS_KEY]),
                    index)

        envcontroller.EnvController.UpdateLocalAddons()
        return index

    def __validate_add_on_version(self, path):
        """ Parses the addon.xml file and checks if all is OK.

        @param path: path to load the addon from
        @return: the AddonId-Version

        """

        addon_file = os.path.join(path, "addon.xml")

        # continue if no addon.xml exists
        if not os.path.isfile(addon_file):
            Logger.Info("No addon.xml found at %s.", addon_file)
            return None, None

        with io.open(addon_file, 'r+', encoding='utf-8') as f:
            addon_xml = f.read()

        pack_version = Regexer.DoRegex('id="([^"]+)"\W+version="([^"]+)"', addon_xml)
        if len(pack_version) > 0:
            # Get the first match
            pack_version = pack_version[0]
            package_id = pack_version[0]
            package_version = Version(version=pack_version[1])
            if Config.version.EqualBuilds(package_version):
                Logger.Info("Adding %s version %s", package_id, package_version)
                return package_id, package_version
            else:
                Logger.Warning("Skipping %s version %s: Versions do not match.",
                               package_id, package_version)
                return None, None
        else:
            Logger.Critical("Cannot determine Channel Add-on version. Not loading Add-on @ '%s'.",
                            path)
            return None, None

    def __get_addon_path(self):
        # type: () -> str
        """ Returns the path that holds all the XBMC add-ons. It differs for Xbox and other platforms.

        @return: The add-on base path

        """

        # different paths for XBMC and XBMC4Xbox
        if envcontroller.EnvController.IsPlatform(Environments.Xbox):
            addon_path = os.path.abspath(os.path.join(Config.rootDir, self.__INTERNAL_CHANNEL_PATH))
            pass
        else:
            addon_path = os.path.abspath(os.path.join(Config.rootDir, ".."))

        return addon_path

    def __is_channel_set_updated(self, channel_info):
        # type: (ChannelInfo) -> bool
        """ Checks whether a channel set was updated.

        @param channel_info: the channelInfo for a channel from the set
        @rtype : boolean indicating if the channel was updated or not.

        """

        compiled_name = "%s.pyc" % (channel_info.moduleName,)
        optimized_name = "%s.pyo" % (channel_info.moduleName,)

        # show the first time message when no Optimezed (.pyo) and no Compiled (.pyc) files are there
        if os.path.isfile(os.path.join(channel_info.path, compiled_name)) or os.path.isfile(
                os.path.join(channel_info.path, optimized_name)):
            return False

        return True

    def __channel_is_correct(self, channel_info):
        # type: (ChannelInfo) -> bool
        """ Validates if the given channel with channelInfo is correct

        @param channel_info: The channelInfo to use to validate the channel
        @return:            True/False if valid or not.

        """

        if not channel_info.guid:
            Logger.Error("Not loading: %s -> No guid present.", channel_info)
            return False

        if channel_info in self.__allChannels:
            existing_channel = self.__allChannels[self.__allChannels.index(channel_info)]
            Logger.Error("Not loading: %s -> a channel with the same guid already exist:\n%s.",
                         channel_info, existing_channel)
            return False

        return True

    def __initialise_channel_set(self, channel_info):
        # type: (ChannelInfo) -> None
        """ Initialises a channelset (.py file)

        WARNING: these actions are done ONCE per python file, not per channel.

        Arguments:
        channelInfo : ChannelInfo - The channelinfo

        Keyword Arguments:
        abortOnNew  : Boolean - If set to true, channel initialisation will not continue if a new channel was found.
                                This will have to be done later.

        Returns True if any operations where executed

        """

        Logger.Info("Initialising channel set at: %s.", channel_info.path)

        # now import (required for the PerformFirstTimeActions
        sys.path.append(channel_info.path)

        # make sure a pyo or pyc exists
        # __import__(channelInfo.moduleName)
        # The debugger won't compile if __import__ is used. So let's use this one.
        import py_compile
        py_compile.compile(os.path.join(channel_info.path, "%s.py" % (channel_info.moduleName,)))

        # purge the texture cache.
        if TextureHandler.Instance():
            TextureHandler.Instance().PurgeTextureCache(channel_info)
        else:
            Logger.Warning("Could not PurgeTextureCache: no TextureHandler available")
        return

    def __initialise_channel(self, channel_info):
        # type: (ChannelInfo) -> None
        """ Performs the first time channel actions for a given channel.

        Arguments:
        channelInfo : ChannelInfo - The channelinfo
        """

        Logger.Info("Performing first time channel actions for: %s.", channel_info)

        self.__show_first_time_message(channel_info)
        return

    def __show_first_time_message(self, channel_info):
        # type: (ChannelInfo) -> None
        """ Checks if it is the first time a channel is executed
        and if a first time message is available it will be shown

        Arguments:
        channelName : string - Name of the channelfile that is loaded
        channelPath : string - Path of the channelfile

        Shows a message dialog if the message should be shown.

        Make sure that each line fits in a single line of a XBMC Dialog box (50 chars)

        """

        hide_first_time = AddonSettings.HideFirstTimeMessages()
        if channel_info.firstTimeMessage:
            if not hide_first_time:
                Logger.Info("Showing first time message '%s' for channel chn_%s.",
                            channel_info.firstTimeMessage, channel_info.moduleName)

                title = LanguageHelper.GetLocalizedString(LanguageHelper.ChannelMessageId)
                XbmcWrapper.ShowDialog(title, channel_info.firstTimeMessage.split("|"))
            else:
                Logger.Debug("Not showing first time message due to add-on setting set to '%s'.",
                             hide_first_time)
        return

    def __is_index_consistent(self, index):
        """ A quick check if a given Channel Index is correct.

        @param index: a index with Channel information
        @return:      an indication (True/False) if the index is consistent.
        """

        if self.__CHANNEL_INDEX_CHANNEL_KEY not in index:
            Logger.Warning("Channel Index Inconsistent: missing '%s' key.", self.__CHANNEL_INDEX_CHANNEL_INFO_KEY)
            return False

        if self.__CHANNEL_INDEX_ADD_ONS_KEY not in index:
            Logger.Warning("Channel Index Inconsistent: missing '%s' key.", self.__CHANNEL_INDEX_ADD_ONS_KEY)
            return False

        # verify if the channels add-ons match, otherwise it is invalid anyways
        indexed_channel_add_ons = index[self.__CHANNEL_INDEX_ADD_ONS_KEY]
        addon_path = self.__get_addon_path()
        channel_path_start = "%s.channel" % (Config.addonDir,)
        add_ons = filter(lambda x: x.startswith(channel_path_start), os.listdir(addon_path))

        # see if the numbers match
        if len(indexed_channel_add_ons) != len(add_ons):
            Logger.Warning("Channel Index Inconsistent: add-on count is not up to date (index=%s vs actual=%s).",
                           len(indexed_channel_add_ons), len(add_ons))
            return False
        # cross reference by putting them on a big pile and then get the distinct values (set) and
        # compare the length of the distinct values.
        if len(set(indexed_channel_add_ons + add_ons)) != len(add_ons):
            Logger.Warning("Channel Index Inconsistent: add-on content is not up to date.")
            return False

        # Validate the version of the add-on and the channel-sets
        channels = index[self.__CHANNEL_INDEX_CHANNEL_KEY]
        first_version = channels[channels.keys()[0]][self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY]
        first_version = Version(first_version)
        if not Config.version.EqualBuilds(first_version):
            Logger.Warning("Inconsisten version 'index' vs 'add-on': %s vs %s", first_version, Config.version)
            return False

        return True

    def __str__(self):
        # type: () -> str
        return "ChannelIndex for %s (id=%s)" % (Config.profileDir, self.id)
