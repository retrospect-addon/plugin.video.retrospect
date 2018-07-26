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
import shutil

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
    def GetRegister():
        """ Returns the current active channel register.

        Used for backward compatibility with Xbox.

        """

        if not ChannelIndex.__channelIndexer:
            Logger.Debug("Creating a new ChannelIndex-er.")
            ChannelIndex.__channelIndexer = ChannelIndex()
        else:
            Logger.Debug("Fetching an existing %s.", ChannelIndex.__channelIndexer)

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
        self.__reindex = self.__DeployNewChannels()
        self.__channelIndex = self.__GetIndex()

        return

    def GetChannel(self, className, channelCode, infoOnly=False):
        """ Fetches a single channel for a given className and channelCode

        If updated channels are found, the those channels are indexed and the
        channel index is rebuild.

        @param className:       the chn_<name> class name
        @param channelCode:     a possible channel code within the channel set
        @param infoOnly:        only return the ChannelInfo
        @return:                a Channel object

        """

        channelSet = self.__channelIndex[self.__CHANNEL_INDEX_CHANNEL_KEY].get(className, None)
        if channelSet is None:
            Logger.Error("Could not find info for channelClass '%s'.", className)
            return None

        channelSetInfoPath = channelSet[self.__CHANNEL_INDEX_CHANNEL_INFO_KEY]
        channelSetVersion = channelSet[self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY]
        if not os.path.isfile(channelSetInfoPath) and not self.__reindexed:
            Logger.Warning("Missing channelSet file: %s.", channelSetInfoPath)
            self.__RebuildIndex()
            return self.GetChannel(className, channelCode)

        channelInfos = ChannelInfo.FromJson(channelSetInfoPath, channelSetVersion)
        if channelCode is None:
            channelInfos = filter(lambda ci: ci.channelCode is None, channelInfos)
        else:
            channelInfos = filter(lambda ci: ci.channelCode == channelCode, channelInfos)

        if len(channelInfos) != 1:
            Logger.Error("Found none or more than 1 matches for '%s' and '%s' in the channel index.",
                         className, channelCode or "None")
            return None
        else:
            Logger.Debug("Found single channel in the channel index: %s.", channelInfos[0])

        if self.__IsChannelSetUpdated(channelInfos[0]):
            # let's see if the index has already been updated this section, of not, do it and
            # restart the ChannelRetrieval.
            if not self.__reindexed:
                # rebuild and restart
                Logger.Warning("Re-index channel index due to channelSet update: %s.", channelSetInfoPath)
                self.__RebuildIndex()
            else:
                Logger.Warning("Found updated channelSet: %s.", channelSetInfoPath)

            # new we should init all channels by loading them all, just to be shure that all is ok
            Logger.Debug("Going to fetching all channels to init them all.")
            self.GetChannels()
            return self.GetChannel(className, channelCode)

        if infoOnly:
            return channelInfos[0]

        return channelInfos[0].GetChannel()

    # noinspection PyUnusedLocal
    def GetChannels(self, includeDisabled=False, **kwargs):
        """ Retrieves all enabled channels within Retrospect.

        If updated channels are found, the those channels are indexed and the
        channel index is rebuild.

        @type includeDisabled: boolean to indicate if we should include those channels that are
                               explicitly disabled from the settings

        @type kwargs: here for backward compatibility

        @return: a list of ChannelInfo objects of enabled channels.

        """

        sw = StopWatch("ChannelIndex.GetChannels Importer", Logger.Instance())
        Logger.Info("Fetching all enabled channels.")

        self.__allChannels = []
        validChannels = []

        # What platform are we
        platform = envcontroller.EnvController.GetPlatform()

        channelsUpdated = False
        for channelSet in self.__channelIndex[self.__CHANNEL_INDEX_CHANNEL_KEY]:
            channelSet = self.__channelIndex[self.__CHANNEL_INDEX_CHANNEL_KEY][channelSet]
            channelSetInfoPath = channelSet[self.__CHANNEL_INDEX_CHANNEL_INFO_KEY]
            channelSetVersion = channelSet[self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY]

            # Check if file exists. If not, rebuild index
            if not os.path.isfile(channelSetInfoPath) and not self.__reindexed:
                Logger.Warning("Missing channelSet file: %s.", channelSetInfoPath)
                self.__RebuildIndex()
                return self.GetChannels()

            channelInfos = ChannelInfo.FromJson(channelSetInfoPath, channelSetVersion)

            # Check if the channel was updated
            if self.__IsChannelSetUpdated(channelInfos[0]):
                # let's see if the index has already been updated this section, of not, do it and
                # restart the ChannelRetrieval.
                if not self.__reindexed:
                    # rebuild and restart
                    Logger.Warning("Re-index channel index due to channelSet update: %s.", channelSetInfoPath)
                    self.__RebuildIndex()
                    return self.GetChannels()
                else:
                    Logger.Warning("Found updated channelSet: %s.", channelSetInfoPath)

                if not channelsUpdated:
                    # this was the first update found (otherwise channelsUpdated was True) show a message:
                    title = LanguageHelper.GetLocalizedString(LanguageHelper.InitChannelTitle)
                    text = LanguageHelper.GetLocalizedString(LanguageHelper.InitChannelText)
                    XbmcWrapper.ShowNotification(title, text, displayTime=15000, logger=Logger.Instance())
                channelsUpdated |= True

                # Initialise the channelset.
                self.__InitialiseChannelSet(channelInfos[0])

                # And perform all first actions for the included channels in the set
                for channelInfo in channelInfos:
                    self.__InitialiseChannel(channelInfo)

            # Check the channel validity
            for channelInfo in channelInfos:
                if not self.__ChannelIsCorrect(channelInfo):
                    continue
                self.__allChannels.append(channelInfo)

                # valid channel for this platform ?
                if not channelInfo.compatiblePlatforms & platform == platform:
                    Logger.Warning("Not loading: %s -> platform '%s' is not compatible.",
                                   channelInfo, Environments.Name(platform))
                    continue
                validChannels.append(channelInfo)

                # was the channel disabled?
                if not AddonSettings.GetChannelVisibility(channelInfo):
                    Logger.Warning("Not loading: %s -> Channel was explicitly disabled from settings.", channelInfo)
                    continue

                # from this point on the channel was enabled, but it could be hidden due to country
                # of origin settings.
                channelInfo.enabled = True
                if not AddonSettings.ShowChannelWithLanguage(channelInfo.language):
                    Logger.Warning("Not loading: %s -> Channel country of origin was disabled from settings.", channelInfo)
                    continue

                channelInfo.visible = True
                Logger.Debug("Loading: %s", channelInfo)

        if channelsUpdated:
            Logger.Info("New or updated channels found. Updating add-on configuration for all channels and user agent.")
            AddonSettings.UpdateAddOnSettingsWithChannels(validChannels, Config)
            AddonSettings.UpdateUserAgent()
        else:
            Logger.Debug("No channel changes found. Skipping add-on configuration for channels.")
            # TODO: perhaps we should check that the settings.xml is correct and not broken?

        validChannels.sort()
        visibleChannels = filter(lambda c: c.visible, validChannels)
        Logger.Info("Fetch a total of %d channels of which %d are visible.",
                    len(validChannels),
                    len(visibleChannels))

        sw.Stop()

        if includeDisabled:
            return validChannels

        return visibleChannels

    def GetCategories(self):
        # type: () -> set
        """ Retrieves the available categories from the channels """

        categories = set()
        channels = self.GetChannels(infoOnly=True)
        map(lambda c: categories.add(c.category), channels)
        Logger.Debug("Found these categories: %s", ", ".join(categories))
        return categories

    def __DeployNewChannels(self):
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
        deployPath = os.path.join(Config.rootDir, "deploy")
        toDeploy = os.listdir(deployPath)

        # addons folder, different for XBMC and XBMC4Xbox
        if envcontroller.EnvController.IsPlatform(Environments.Xbox):
            targetFolder = os.path.abspath(
                os.path.join(Config.rootDir, self.__INTERNAL_CHANNEL_PATH))
            if not os.path.exists(targetFolder):
                os.mkdir(targetFolder)
        else:
            targetFolder = os.path.abspath(os.path.join(Config.rootDir, ".."))

        deployed = False
        for deploy in toDeploy:
            if deploy.startswith("."):
                continue
            sourcePath = os.path.join(deployPath, deploy)

            # find out if the scriptname is not net.rieter.xot and update
            deployParts = deploy.split(".")
            destDeploy = "%s.channel.%s" % (Config.addonDir, deployParts[-1])
            destinationPath = os.path.join(targetFolder, destDeploy)
            Logger.Info("Deploying Channel Addon '%s' to '%s'", deploy, destinationPath)

            if os.path.exists(destinationPath):
                Logger.Info("Removing old channel at %s", destDeploy)
                shutil.rmtree(destinationPath)

            # only update if there was a real addon
            if os.path.exists(os.path.join(sourcePath, "addon.xml")):
                shutil.move(sourcePath, destinationPath)
            else:
                shutil.rmtree(sourcePath)
            deployed = True

        return deployed

    def __GetIndex(self):
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
                return self.__RebuildIndex()

        if not os.path.isfile(self.__CHANNEL_INDEX):
            Logger.Info("No index file found at '%s'. Rebuilding.", self.__CHANNEL_INDEX)
            return self.__RebuildIndex()

        fd = None
        try:
            fd = open(self.__CHANNEL_INDEX)
            data = fd.read()
            indexJson = JsonHelper(data, logger=Logger.Instance())
            Logger.Debug("Loaded index from '%s'.", self.__CHANNEL_INDEX)

            if not self.__IsIndexConsistent(indexJson.json):
                return self.__RebuildIndex()
            return indexJson.json
        except:
            Logger.Critical("Error reading channel index. Rebuilding.", exc_info=True)
            return self.__RebuildIndex()
        finally:
            if fd is not None and not fd.closed:
                fd.close()

    def __RebuildIndex(self):
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
        addonPath = self.__GetAddonPath()
        channelPathStart = "%s.channel" % (Config.addonDir,)
        addOns = filter(lambda x: channelPathStart in x and "BUILD" not in x, os.listdir(addonPath))
        for addOnDir in addOns:
            index[self.__CHANNEL_INDEX_ADD_ONS_KEY].append(addOnDir)

            channelAddOnPath = os.path.join(addonPath, addOnDir)
            channelAddOnId, channelAddOnVersion = self.__ValidateAddOnVersion(channelAddOnPath)
            if channelAddOnId is None:
                continue

            channelSets = os.listdir(channelAddOnPath)
            for channelSet in channelSets:
                if not os.path.isdir(os.path.join(channelAddOnPath, channelSet)):
                    continue

                channelSetId = "chn_%s" % (channelSet,)
                Logger.Debug("Found channel set '%s'", channelSetId)
                index[self.__CHANNEL_INDEX_CHANNEL_KEY][channelSetId] = {
                    self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY: str(channelAddOnVersion),
                    self.__CHANNEL_INDEX_CHANNEL_INFO_KEY: os.path.join(channelAddOnPath, channelSet, "%s.json" % (channelSetId,))
                }

        f = None
        try:
            f = open(self.__CHANNEL_INDEX, 'w+')
            f.write(JsonHelper.Dump(index))
        finally:
            if f is not None:
                f.close()

        # now we marked that we already re-indexed.
        self.__reindexed = True
        self.__channelIndex = index
        Logger.Info("Rebuilding channel index completed with %d channelSets and %d add-ons: %s.",
                    len(index[self.__CHANNEL_INDEX_CHANNEL_KEY]),
                    len(index[self.__CHANNEL_INDEX_ADD_ONS_KEY]),
                    index)

        envcontroller.EnvController.UpdateLocalAddons()
        return index

    def __ValidateAddOnVersion(self, path):
        """ Parses the addon.xml file and checks if all is OK.

        @param path: path to load the addon from
        @return: the AddonId-Version

        """

        addonFile = os.path.join(path, "addon.xml")

        # continue if no addon.xml exists
        if not os.path.isfile(addonFile):
            Logger.Info("No addon.xml found at %s.", addonFile)
            return None, None

        f = open(addonFile, 'r+')
        addonXml = f.read()
        f.close()

        packVersion = Regexer.DoRegex('id="([^"]+)"\W+version="([^"]+)"', addonXml)
        if len(packVersion) > 0:
            # Get the first match
            packVersion = packVersion[0]
            packageId = packVersion[0]
            packageVersion = Version(version=packVersion[1])
            if Config.version.EqualBuilds(packageVersion):
                Logger.Info("Adding %s version %s", packageId, packageVersion)
                return packageId, packageVersion
            else:
                Logger.Warning("Skipping %s version %s: Versions do not match.", packageId,
                               packageVersion)
                return None, None
        else:
            Logger.Critical("Cannot determine Channel Add-on version. Not loading Add-on @ '%s'.",
                            path)
            return None, None

    def __GetAddonPath(self):
        # type: () -> str
        """ Returns the path that holds all the XBMC add-ons. It differs for Xbox and other platforms.

        @return: The add-on base path

        """

        # different paths for XBMC and XBMC4Xbox
        if envcontroller.EnvController.IsPlatform(Environments.Xbox):
            addonPath = os.path.abspath(os.path.join(Config.rootDir, self.__INTERNAL_CHANNEL_PATH))
            pass
        else:
            addonPath = os.path.abspath(os.path.join(Config.rootDir, ".."))

        return addonPath

    def __IsChannelSetUpdated(self, channelInfo):
        # type: (ChannelInfo) -> bool
        """ Checks whether a channel set was updated.

        @param channelInfo: the channelInfo for a channel from the set
        @rtype : boolean indicating if the channel was updated or not.

        """

        compiledName = "%s.pyc" % (channelInfo.moduleName,)
        optimizedName = "%s.pyo" % (channelInfo.moduleName,)

        # show the first time message when no Optimezed (.pyo) and no Compiled (.pyc) files are there
        if os.path.isfile(os.path.join(channelInfo.path, compiledName)) or os.path.isfile(
                os.path.join(channelInfo.path, optimizedName)):
            return False

        return True

    def __ChannelIsCorrect(self, channelInfo):
        # type: (ChannelInfo) -> bool
        """ Validates if the given channel with channelInfo is correct

        @param channelInfo: The channelInfo to use to validate the channel
        @return:            True/False if valid or not.

        """

        if not channelInfo.guid:
            Logger.Error("Not loading: %s -> No guid present.", channelInfo)
            return False

        if channelInfo in self.__allChannels:
            existingChannel = self.__allChannels[self.__allChannels.index(channelInfo)]
            Logger.Error("Not loading: %s -> a channel with the same guid already exist:\n%s.",
                         channelInfo, existingChannel)
            return False

        return True

    def __InitialiseChannelSet(self, channelInfo):
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

        Logger.Info("Initialising channel set at: %s.", channelInfo.path)

        # now import (required for the PerformFirstTimeActions
        sys.path.append(channelInfo.path)

        # make sure a pyo or pyc exists
        # __import__(channelInfo.moduleName)
        # The debugger won't compile if __import__ is used. So let's use this one.
        import py_compile
        py_compile.compile(os.path.join(channelInfo.path, "%s.py" % (channelInfo.moduleName,)))

        # purge the texture cache.
        if TextureHandler.Instance():
            TextureHandler.Instance().PurgeTextureCache(channelInfo)
        else:
            Logger.Warning("Could not PurgeTextureCache: no TextureHandler available")
        return

    def __InitialiseChannel(self, channelInfo):
        # type: (ChannelInfo) -> None
        """ Performs the first time channel actions for a given channel.

        Arguments:
        channelInfo : ChannelInfo - The channelinfo
        """

        Logger.Info("Performing first time channel actions for: %s.", channelInfo)

        self.__ShowFirstTimeMessage(channelInfo)
        return

    def __ShowFirstTimeMessage(self, channelInfo):
        # type: (ChannelInfo) -> None
        """ Checks if it is the first time a channel is executed
        and if a first time message is available it will be shown

        Arguments:
        channelName : string - Name of the channelfile that is loaded
        channelPath : string - Path of the channelfile

        Shows a message dialog if the message should be shown.

        Make sure that each line fits in a single line of a XBMC Dialog box (50 chars)

        """

        hideFirstTime = AddonSettings.HideFirstTimeMessages()
        if channelInfo.firstTimeMessage:
            if not hideFirstTime:
                Logger.Info("Showing first time message '%s' for channel chn_%s.",
                            channelInfo.firstTimeMessage, channelInfo.moduleName)

                title = LanguageHelper.GetLocalizedString(LanguageHelper.ChannelMessageId)
                XbmcWrapper.ShowDialog(title, channelInfo.firstTimeMessage.split("|"))
            else:
                Logger.Debug("Not showing first time message due to add-on setting set to '%s'.",
                             hideFirstTime)
        return

    def __IsIndexConsistent(self, index):
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
        indexedChannelAddOns = index[self.__CHANNEL_INDEX_ADD_ONS_KEY]
        addonPath = self.__GetAddonPath()
        channelPathStart = "%s.channel" % (Config.addonDir,)
        addOns = filter(lambda x: x.startswith(channelPathStart), os.listdir(addonPath))

        # see if the numbers match
        if len(indexedChannelAddOns) != len(addOns):
            Logger.Warning("Channel Index Inconsistent: add-on count is not up to date (index=%s vs actual=%s).",
                           len(indexedChannelAddOns), len(addOns))
            return False
        # cross reference by putting them on a big pile and then get the distinct values (set) and
        # compare the length of the distinct values.
        if len(set(indexedChannelAddOns + addOns)) != len(addOns):
            Logger.Warning("Channel Index Inconsistent: add-on content is not up to date.")
            return False

        # Validate the version of the add-on and the channel-sets
        channels = index[self.__CHANNEL_INDEX_CHANNEL_KEY]
        firstVersion = channels[channels.keys()[0]][self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY]
        firstVersion = Version(firstVersion)
        if not Config.version.EqualBuilds(firstVersion):
            Logger.Warning("Inconsisten version 'index' vs 'add-on': %s vs %s", firstVersion, Config.version)
            return False

        return True

    def __str__(self):
        # type: () -> str
        return "ChannelIndex for %s" % (Config.profileDir, )
