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
        self.__enabledChannels = []  # list of all loaded channels (after checking languages and so)
        self.__validChannels = []  # list of all channels that are available on the current platform and thus are loadable
        self.__allChannels = []  # list of all available channels

        self.__reindexed = False
        self.__reindex = self.__DeployNewChannels()
        self.__channelIndex = self.__GetIndex()

        return

    def GetChannel(self, className, channelCode):
        # type: (str, str) -> ChannelInfo
        """ Fetches a single channel for a given className and channelCode

        If updated channels are found, the those channels are indexed and the
        channel index is rebuild.

        @param className:       the chn_<name> class name
        @param channelCode:     a possible channel code within the channel set
        @return:                a ChannelInfo object

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

        return channelInfos[0].GetChannel()

    # noinspection PyUnusedLocal
    def GetChannels(self, **kwargs):
        # type: (object) -> list
        """ Retrieves all enabled channels within Retrospect.

        If updated channels are found, the those channels are indexed and the
        channel index is rebuild.

        @type kwargs: here for backward compatibility

        @return: a list of ChannelInfo objects of enabled channels.

        """

        Logger.Info("Fetching all enabled channels.")

        self.__enabledChannels = []
        self.__allChannels = []
        self.__validChannels = []

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
                    XbmcWrapper.ShowNotification(title, text, displayTime=15000)
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
                self.__validChannels.append(channelInfo)

                # was the channel disabled?
                if not (AddonSettings.ShowChannel(
                        channelInfo) and AddonSettings.ShowChannelWithLanguage(
                        channelInfo.language)):
                    Logger.Warning("Not loading: %s -> Channel was disabled from settings.",
                                   channelInfo)
                    continue
                self.__enabledChannels.append(channelInfo)

                Logger.Debug("Loading: %s", channelInfo)

        if channelsUpdated:
            Logger.Info("New or updated channels found. Updating add-on configuration for all channels and user agent.")
            AddonSettings.UpdateAddOnSettingsWithChannels(self.__validChannels, Config)
            AddonSettings.UpdateUserAgent()
        else:
            Logger.Debug("No channel changes found. Skipping add-on configuration for channels.")

        self.__enabledChannels.sort()
        Logger.Info("Fetch a total of %d channels of which %d are enabled.",
                    len(self.__allChannels),
                    len(self.__enabledChannels))
        return self.__enabledChannels

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
        finally:
            if fd is not None and not fd.closed:
                fd.close()
        indexJson = JsonHelper(data)
        Logger.Debug("Loaded index from '%s'.", self.__CHANNEL_INDEX)

        if not self.__IsIndexConsistent(indexJson.json):
            return self.__RebuildIndex()
        return indexJson.json

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
            channelAddOnId, channelAddOnVersion = self.__ParseVideoAddOnVersion(channelAddOnPath)
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
        return index

    def __ParseVideoAddOnVersion(self, path):
        # type: (str) -> Version
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

        packVersion = Regexer.DoRegex('id="([^"]+)"\W+version="([^"]{5,10})"', addonXml)
        if len(packVersion) > 0:
            # Get the first match
            packVersion = packVersion[0]

            packageId = packVersion[0]
            packageVersion = Version(version=packVersion[1])
            # channelAddon = os.path.split(path)[-1]
            # packVersion = packVersion.
            if Config.version.EqualRevisions(packageVersion):
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
        # type: (ChannelInfo) -> ()
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
        TextureHandler.Instance().PurgeTextureCache(channelInfo)
        return

    def __InitialiseChannel(self, channelInfo):
        # type: (ChannelInfo) -> ()
        """ Performs the first time channel actions for a given channel.

        Arguments:
        channelInfo : ChannelInfo - The channelinfo
        """

        Logger.Info("Performing first time channel actions for: %s.", channelInfo)

        self.__ShowFirstTimeMessage(channelInfo)
        return

    def __ShowFirstTimeMessage(self, channelInfo):
        # type: (ChannelInfo) -> ()
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
        # type: (dict) -> boolean
        """ A quick check if a given Channel Index is correct.

        @param index: a index with Channel information
        @return:      an indication (True/False) if the index is consistent.
        """
        if self.__CHANNEL_INDEX_CHANNEL_KEY not in index or self.__CHANNEL_INDEX_ADD_ONS_KEY not in index:
            Logger.Warning("Channel Index Inconsistent: missing '%s' key.", self.__CHANNEL_INDEX_CHANNEL_INFO_KEY)
            return False

        # verify if the channels add-ons match, otherwise it is invalid anyways
        indexedChannelAddOns = index[self.__CHANNEL_INDEX_ADD_ONS_KEY]
        addonPath = self.__GetAddonPath()
        channelPathStart = "%s.channel" % (Config.addonDir,)
        addOns = filter(lambda x: channelPathStart in x and "BUILD" not in x, os.listdir(addonPath))

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

        return True

    def __str__(self):
        # type: () -> str
        return "ChannelIndex for %s" % (Config.profileDir, )


class ChannelImporter:
    """Class that handles the deploying and loading of available channels."""

    __channelImporter = None  # : Property to store the channel importer in.

    @staticmethod
    def GetRegister():
        """Returns the current active channel register.

        Used for backward compatibility with Xbox.

        """

        if not ChannelImporter.__channelImporter:
            Logger.Debug("Creating a new ChannelImporter")
            ChannelImporter()

        Logger.Debug("Fetching an existing channelImporter: %s", ChannelImporter.__channelImporter)

        return ChannelImporter.__channelImporter

    def __init__(self):
        """Initialize the importer by reading the channels from the channel
        resource folder and will start the import of the channels

        It also deploys the channels from the retrospect\deploy folder.

        """

        self.__INTERNAL_CHANNEL_PATH = "channels"
        self.__CHANNEL_INDEX = os.path.join(Config.profileDir, "channelindex.json")

        # initialise the collections
        self.__enabledChannels = []  # list of all loaded channels (after checking languages and so)
        self.__validChannels = []  # list of all channels that are available on the current platform and thus are loadable
        self.__allChannels = []  # list of all available channels

        self.__channelVersions = []  # list of channelname+version that were found

        self.__updateChannelPath = "_updates"

        self.__DeployNewChannels()

        # set it to the Singleton property
        ChannelImporter.__channelImporter = self
        return

    def GetCategories(self):
        """ Retrieves the available categories from the channels """

        # now get the categories
        categories = set()
        channels = self.GetChannels(infoOnly=True)
        map(lambda c: categories.add(c.category), channels)
        Logger.Debug("Found these categories: %s", ", ".join(categories))
        return categories

    def GetChannels(self, includeDisabled=False, infoOnly=False):
        """Retrieves the available channels. If the channels were not already
        loaded, it will import them.

        Keyword Arguments:
        includeDisabled : boolean - If set to true, all channels are loaded
                                    including those that were disabled due to
                                    language restrictions or incompatible
                                    operating systems.
        infoOnly        : boolean - Only return the Metadata objects

        Returns:
        A list of <Channel> objects

        """
        if not self.__enabledChannels:
            self.__ImportChannels()

        if includeDisabled:
            result = self.__allChannels
        else:
            result = self.__enabledChannels

        if not infoOnly:
            # create the actual objects
            result = map(lambda c: c.GetChannel(), result)
            result = filter(lambda c: c is not None, result)

        if len(result) > 0:
            return result
        else:
            return []

    def GetChannel(self, className, channelCode):
        """Imports a single channel

        Arguments:
        className : string - class name of the channel to import.

        Returns:
        The channels in the requested class. So that could be more, but they
        can be distinguished using the channelcode.

        Returns an empty list if no channels were found.

        """

        if not className:
            raise ValueError("className should be specified.")

        Logger.Info("Loading channels for class '%s' and channelCode '%s'", className, channelCode)

        self.__enabledChannels = []
        self.__allChannels = []
        self.__validChannels = []
        self.__channelVersions = []

        # noinspection PyUnusedLocal
        classPath = None
        channelPath = None
        classBaseName = className[4:]
        if os.path.isfile(self.__CHANNEL_INDEX):
            Logger.Debug("Using ChannelIndex for channel lookup: %s", self.__CHANNEL_INDEX)
            fd = None
            try:
                fd = open(self.__CHANNEL_INDEX)
                data = fd.read()
            finally:
                if fd is not None and not fd.closed:
                    fd.close()
            channelIndex = JsonHelper(data)
            classPath = channelIndex.GetValue(className, channelCode or "null")
            if classPath is not None:
                if not os.path.isdir(classPath):
                    Logger.Warning(
                        "Missing channel class path '%s' found. Rebuilding the ChannelIndex.",
                        classPath)
                    # remove the old one
                    os.remove(self.__CHANNEL_INDEX)
                    # return self.GetSingleChannel(className, channelCode)
                    return self.__ImportChannel(className, channelCode)
                channelPath = os.path.join(classPath, "..")
        else:
            Logger.Warning("Missing ChannelIndex. Rebuilding the ChannelIndex.")
            return self.__ImportChannel(className, channelCode)

            # Logger.Warning("Falling back to classic find pattern")
            #
            # # walk the channel dirs to find the one that has the channel
            # addonPath = self.__GetAddonPath()
            # channelPathStart = "%s.channel" % (Config.addonDir,)
            #
            # # list all add-ons
            # for directory in os.listdir(addonPath):
            #     # find the xot ones
            #     if channelPathStart in directory and "BUILD" not in directory:
            #         channelPath = os.path.join(addonPath, directory)
            #
            #         # list the subfolders for the requested folder to find the one we need
            #         if classBaseName not in os.listdir(channelPath):
            #             continue
            #
            #         # we perhaps found it.
            #         classPath = os.path.join(channelPath, classBaseName)

        if classPath is None:
            Logger.Error("No Channel found for class '%s' and channelCode '%s'",
                         className, channelCode)
            return None

        Logger.Debug("Found possible channel folder in %s", classPath)

        # check the addon.xml with self.__ParseChannelVersionInfo(path)
        channelVersion = self.__ParseChannelVersionInfo(channelPath)
        if channelVersion:
            self.__channelVersions.append(channelVersion)
        else:
            # no info was returned, so we will not include the channel
            Logger.Error("Match in %s has incorrect version", classPath)
            return None

        # create ChannelInfo objects from the xml file and get the correct ChannelInfo object. It coulde that none
        # is found and we might need to continue (in case there were duplicate channel names
        fileName = os.path.join(classPath, "chn_" + classBaseName + ".json")

        Logger.Debug("Loading info for chn_%s @ %s", classBaseName, fileName)
        if not os.path.isfile(fileName):
            Logger.Error("Could not load %s", fileName)
            return None

        cis = ChannelInfo.FromJson(fileName)
        ci = filter(lambda c: c.moduleName == className and (c.channelCode == channelCode or
                                                             c.channelCode is channelCode), cis)
        if not ci or len(ci) > 1:
            Logger.Error("Could not load channel with className=%s and channelCode=%s from %s",
                         className, channelCode, fileName)
            return None

        ci = ci[0]
        if self.__IsChannelSetUpdated(ci):
            # apparently a new channel was found, so we need to do it all
            Logger.Info("Found a new channel, we need to reload all channels")
            return self.__ImportChannel(className, channelCode)

        # What platform are we
        platform = envcontroller.EnvController.GetPlatform()

        # check if it is enabled or not
        if self.__ValidateChannelInfo(ci, platform):
            return ci.GetChannel()
        else:
            Logger.Error("Invalid Channel found for class '%s' and channelCode '%s'",
                         className, channelCode)
            return None

    def IsChannelInstalled(self, zipFileName):
        """Checks if the requested channel in the zipfile is already installed"""

        return zipFileName.replace(".zip", "") in self.__channelVersions

    def __DeployNewChannels(self):
        """Checks the deploy folder for new channels, if present, deploys them

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

        for deploy in toDeploy:
            if deploy.startswith("."):
                continue
            sourcePath = os.path.join(deployPath, deploy)

            # find out if the scriptname is not net.rieter.xot and update
            deployParts = deploy.split(".")
            # channels addons always end with .channel.name
            # if (deployParts[-1] == "autoupdate"):
            #    destDeploy = "%s.%s" % (Config.addonDir, deployParts[-1])
            # else:
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

        return

    def __IsChannelSetUpdated(self, channelInfo):
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

    def __FirstTimeChannelActions(self, channelInfo):
        """ Performs the first time channel actions for a given channel.

        Arguments:
        channelInfo : ChannelInfo - The channelinfo
        """

        Logger.Info("Performing first time channel actions for: %s", channelInfo)

        self.__ShowFirstTimeMessage(channelInfo)
        return

    def __InitialiseChannelSet(self, channelInfo):
        """ Initialises a channelset (.py file)

        WARNING: these actions are done ONCE per python file, not per channel.

        Arguments:
        channelInfo : ChannelInfo - The channelinfo

        Keyword Arguments:
        abortOnNew  : Boolean - If set to true, channel initialisation will not continue if a new channel was found.
                                This will have to be done later.

        Returns True if any operations where executed

        """

        Logger.Info("Initialising channel set at: %s", channelInfo.path)

        # now import (required for the PerformFirstTimeActions
        sys.path.append(channelInfo.path)

        # make sure a pyo or pyc exists
        # __import__(channelInfo.moduleName)
        # The debugger won't compile if __import__ is used. So let's use this one.
        import py_compile
        py_compile.compile(os.path.join(channelInfo.path, "%s.py" % (channelInfo.moduleName,)))

        # see if the channel included XOT updates
        self.__DeployUpdates(channelInfo.path)

        # purge the texture cache.
        TextureHandler.Instance().PurgeTextureCache(channelInfo)
        return True

    def __DeployUpdates(self, channelPath, cleanup=False):
        """ checks if there are updates to be deployed. If updates are found, they
        are deployed, only if it is a newer version.

        Arguments:
        channelPath : String  - the path to look for the _update folder

        Keyword Arguments:
        cleanup     : Boolean - should the _update folder be deleted.

        The naming of the files should be in the form of:

            the.path.with.slashes.replaced.with.dots.filename.extension-version

        So it could be:

            resources.libs.helpers.jsonhelper.py-3.3.2.1

        """

        updatePath = os.path.abspath(os.path.join(channelPath, "..", self.__updateChannelPath))

        if os.path.exists(updatePath):
            Logger.Info("Deploying updates from path: %s", updatePath)

            # do all the files
            for update in os.listdir(updatePath):
                # split the filename on - to get the version
                updateParts = update.split("-")
                versionNumber = Version(updateParts[-1])

                if versionNumber < Config.version:
                    Logger.Info(
                        "Skipping updated file: %s. A higher version of %s was already installed: %s",
                        update, Config.appName, Config.version)
                    break

                # split the other part on the dots and create a new path
                updateParts = updateParts[0].split(".")
                targetPath = os.path.sep.join(updateParts[:-2])
                targetPath = os.path.join(Config.rootDir, targetPath)

                # and determine the filename and extension
                fileName = ".".join(updateParts[-2:])

                # now check existing files and updates
                for existing in os.listdir(targetPath):
                    if fileName in existing and "-" in existing:
                        # update that was already installed found, check version
                        existingVersion = Version(existing.split("-")[-1])
                        if existingVersion >= versionNumber:
                            # stop, a newer version was already detected
                            Logger.Info(
                                "Skipping updated file: %s. Newer (or same) version already installed: %s",
                                update, existingVersion)
                            break
                else:  # executed if the loop ended normally (no break)
                    # if we get here, either no update was found, or this one is newer
                    Logger.Info("Deploying updated file: %s", update)

                    # construct the sources and destinations
                    targetFile = os.path.join(targetPath, fileName)
                    targetFileVersion = os.path.join(targetPath,
                                                     "%s-%s" % (fileName, versionNumber))
                    sourceFile = os.path.join(updatePath, update)
                    # actually copy them
                    shutil.copy(sourceFile, targetFileVersion)
                    shutil.copy(sourceFile, targetFile)

            if cleanup:
                Logger.Info("Cleaning update path: %s", updatePath)
                shutil.rmtree(updatePath)

    def __ShowFirstTimeMessage(self, channelInfo):
        """ Checks if it is the first time a channel is executed
        and if a first time message is available it will be shown

        Arguments:
        channelName : string - Name of the channelfile that is loaded
        channelPath : string - Path of the channelfile

        Shows a message dialog if the message should be shown.

        Make sure that each line fits in a single line of a XBMC Dialog box (50 chars)

        """

        hideFirstTime = AddonSettings.HideFirstTimeMessages()
        if channelInfo.firstTimeMessage and not hideFirstTime:
            Logger.Info("Showing first time message '%s' for channel chn_%s",
                        channelInfo.firstTimeMessage, channelInfo.moduleName)

            title = LanguageHelper.GetLocalizedString(LanguageHelper.ChannelMessageId)
            XbmcWrapper.ShowDialog(title, channelInfo.firstTimeMessage.split("|"))

        if hideFirstTime:
            Logger.Debug("Not showing first time message due to add-on setting set to '%s'.",
                         hideFirstTime)

        return

    def __ImportChannels(self):  # , className = None):
        """Import the available channels

        This method will:
         - iterate through the Addons folder and find all the folders name
           <basename>.channel.<channelname>.
         - then adds all the subfolders into a list (with paths).
         - then all paths are added to the system path, so they can be imported.
         - then read all the chn_<name>.xml metadata files and add the ChannelInfo
           objects to the self.__channelsToImport
         - then the channels in the self.__channelsToImport list are instantiated
           into the self.channels list.

        """

        Logger.Debug("Importing available channels")
        # import each channelPath. On import, the channelPath will call the RegisterChannel Method
        try:
            # clear a possible previous import
            self.__enabledChannels = []
            self.__allChannels = []
            self.__validChannels = []
            self.__channelVersions = []

            # first find all folders with channels that we might need to import
            channelImport = []
            # importTimer = StopWatch("ChannelImporter :: importing channels", Logger.Instance())

            addonPath = self.__GetAddonPath()

            channelPathStart = "%s.channel" % (Config.addonDir,)
            for directory in os.listdir(addonPath):
                if channelPathStart in directory and "BUILD" not in directory:
                    path = os.path.join(addonPath, directory)

                    channelVersion = self.__ParseChannelVersionInfo(path)
                    if channelVersion:
                        self.__channelVersions.append(channelVersion)
                    else:
                        # no info was returned, so we will not include the channel
                        continue

                    # get all nested channels
                    subDirs = os.listdir(path)
                    channelImport.extend(
                        [os.path.abspath(os.path.join(path, weapon)) for weapon in subDirs])

            channelImport.sort()
            # importTimer.Lap("Directories scanned for .channel")

            # we need to make sure we don't load multiple channel classes and track if we found updates
            channelsUpdated = False
            loadedChannels = []
            channelsToImport = []

            # now import the channels
            for channelPath in channelImport:
                if not os.path.isdir(channelPath):
                    continue

                # determine channelname
                channelName = os.path.split(channelPath)[-1]
                if channelName == self.__updateChannelPath:
                    Logger.Trace("Update path found and skipping: %s", channelName)
                    continue

                # if loadedChannels.count(channelName) > 0:
                if channelName in loadedChannels:
                    Logger.Warning(
                        "Not loading: chn_%s.xml in %s because there is already a path with "
                        "name '%s' that name loaded", channelName, channelPath, channelName)
                    continue

                if channelName.startswith("."):
                    continue

                # now we can continue
                loadedChannels.append(channelName)

                fileName = os.path.join(channelPath, "chn_" + channelName + ".json")
                Logger.Trace("Loading info for chn_%s @ %s", channelName, fileName)
                if os.path.isfile(fileName):
                    try:
                        ci = ChannelInfo.FromJson(fileName)
                        if len(ci) <= 0:
                            Logger.Warning("No channels found in '%s'", fileName)
                            continue

                        # Add them to the list to import
                        channelsToImport += ci

                        if self.__IsChannelSetUpdated(ci[0]):
                            if not channelsUpdated:
                                # this was the first update found (otherwise channelsUpdated was True) show a message:
                                title = LanguageHelper.GetLocalizedString(
                                    LanguageHelper.InitChannelTitle)
                                text = LanguageHelper.GetLocalizedString(
                                    LanguageHelper.InitChannelText)
                                XbmcWrapper.ShowNotification(title, text, displayTime=15000)

                            # set the updates found bit
                            channelsUpdated |= True

                            # Initialise the channelset.
                            self.__InitialiseChannelSet(ci[0])

                            # And perform all first actions for the included channels in the set
                            for channelInfo in ci:
                                self.__FirstTimeChannelActions(channelInfo)
                    except:
                        Logger.Error("Error import chn_%s.json", channelName, exc_info=True)

            # importTimer.Lap()

            # What platform are we
            platform = envcontroller.EnvController.GetPlatform()

            # instantiate the registered channels
            for channelInfo in channelsToImport:
                # noinspection PyUnusedLocal
                isValid = self.__ValidateChannelInfo(channelInfo, platform)

            # sort the channels
            self.__enabledChannels.sort()

            if channelsUpdated:
                Logger.Info("New or updated channels found. Updating add-on configuration for all "
                            "channels and user agent")
                AddonSettings.UpdateAddOnSettingsWithChannels(self.__validChannels, Config)
                AddonSettings.UpdateUserAgent()
            else:
                Logger.Debug("No channel changes found. Skipping add-on configuration for channels")

            # Should we update the channel index?
            if channelsUpdated or not os.path.isfile(self.__CHANNEL_INDEX):
                self.__CreateChannelIndex()

            Logger.Info("Imported %s channels from which %s are enabled",
                        len(self.__allChannels), len(self.__enabledChannels))
            # importTimer.Stop()
        except:
            Logger.Critical("Error loading channel modules", exc_info=True)

    def __ImportChannel(self, className, channelCode):
        """ Imports a single channel by first importing all others

        @param className: the class to import
        @param channelCode: the channel code within the class

        @return: a Channel object

        """

        if not self.__enabledChannels:
            self.__ImportChannels()

        # now we filter the channels
        results = filter(lambda c: c.moduleName == className and (
            c.channelCode == channelCode or c.channelCode is channelCode
        ), self.__enabledChannels)

        # Order them by channelName MUST Also sort the buttons
        Logger.Info("ImportChannel resulted in %s channel(s)", len(results))
        if len(results) == 1:
            Logger.Info("ImportChannel found: %s", results[0])
            return results[0].GetChannel()
        else:
            return None

    def __ValidateChannelInfo(self, channelInfo, platform):
        """ Checks if the value is valid for the current environment, if it is enabled and so on.

        @param channelInfo: The channel info meta data to check
        @param platform:    The platform to validate against

        @rtype : Boolean indicating the channel is valid. It might still be disabled from the settings.

        """

        if not channelInfo.guid:
            Logger.Error("Not loading: %s -> No guid present", channelInfo)
            return False

        if channelInfo in self.__allChannels:
            existingChannel = self.__allChannels[self.__allChannels.index(channelInfo)]
            Logger.Error("Not loading: %s -> a channel with the same guid already exist:\n%s.",
                         channelInfo, existingChannel)
            return False

        # store all the channels except the out of date and duplicate ones, we might need them somewhere
        self.__allChannels.append(channelInfo)

        if not channelInfo.compatiblePlatforms & platform == platform:
            Logger.Warning("Not loading: %s -> platform '%s' is not compatible", channelInfo,
                           Environments.Name(platform))
            return False

        # now it is a valid channel for this platform.
        self.__validChannels.append(channelInfo)

        if not (AddonSettings.ShowChannel(channelInfo) and AddonSettings.ShowChannelWithLanguage(
                channelInfo.language)):
            Logger.Warning("Not loading: %s -> Channel was disabled from settings.", channelInfo)
            return True

        Logger.Debug("Loading: %s", channelInfo)

        # add to channelPath list
        self.__enabledChannels.append(channelInfo)
        return True

    def __GetAddonPath(self):
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

    def __ParseChannelVersionInfo(self, path):
        """ Parses the addon.xml file and checks if all is OK.

        @param path: path to load the addon from
        @return: the AddonId-Version
        """

        addonFile = os.path.join(path, "addon.xml")

        # continue if no addon.xml exists
        if not os.path.isfile(addonFile):
            Logger.Info("No addon.xml found at %s", addonFile)
            return None

        f = open(addonFile, 'r+')
        addonXml = f.read()
        f.close()

        packVersion = Regexer.DoRegex('id="([^"]+)"\W+version="([^"]{5,10})"', addonXml)
        if len(packVersion) > 0:
            # Get the first match
            packVersion = packVersion[0]

            packageId = packVersion[0]
            packageVersion = Version(version=packVersion[1])
            # channelAddon = os.path.split(path)[-1]
            # packVersion = packVersion.
            if Config.version.EqualRevisions(packageVersion):
                Logger.Info("Loading %s version %s", packageId, packageVersion)

                # save to the list of present items, for querying in the
                # future (xbox updates)
                channelVersionID = "%s-%s" % (packVersion[0], packVersion[1])
                return channelVersionID
            else:
                Logger.Warning("Skipping %s version %s: Versions do not match.", packageId,
                               packageVersion)
                return None
        else:
            Logger.Critical("Cannot determine channel version. Not loading channel @ '%s'", path)
            return None

    def __CreateChannelIndex(self):
        """ Creates a channel index file for lookups purposes """

        indexPath = self.__CHANNEL_INDEX
        Logger.Info("Generating channel index at '%s'", indexPath)
        channels = dict()
        for channel in self.__allChannels:
            if channel.moduleName not in channels:
                channels[channel.moduleName] = dict()
            if channel.channelCode in channels[channel.moduleName]:
                Logger.Error("Cannot create duplicate channelCode for channel:\n'%s'", channel)
            else:
                channels[channel.moduleName][channel.channelCode] = channel.path

        data = JsonHelper.Dump(channels)
        fd = None
        try:
            fd = file(indexPath, mode='w')
            fd.write(data)
        finally:
            if fd is not None and not fd.closed:
                fd.close()
        return


# ChannelIndex = ChannelImporter
