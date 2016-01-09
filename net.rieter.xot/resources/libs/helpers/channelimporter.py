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
import version

from addonsettings import AddonSettings
from regexer import Regexer
from environments import Environments
from stopwatch import StopWatch
from xbmcwrapper import XbmcWrapper
from helpers.languagehelper import LanguageHelper
from config import Config
from channelinfo import ChannelInfo
from logger import Logger
from helpers.jsonhelper import JsonHelper


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

    def GetSingleChannel_old(self, className, channelCode):
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

        channel = None

        # walk the channel dirs to find the one that has the channel
        addonPath = self.__GetAddonPath()
        channelPathStart = "%s.channel" % (Config.addonDir, )
        folderToFind = className[4:]

        # list all add-ons
        for directory in os.listdir(addonPath):
            # find the xot ones
            if channelPathStart in directory and "BUILD" not in directory:
                channelPath = os.path.join(addonPath, directory)

                # list the subfolders for the requested folder to find the one we need
                if folderToFind not in os.listdir(channelPath):
                    continue

                # we perhaps found it.
                classPath = os.path.join(channelPath, folderToFind)
                Logger.Debug("Found possible channel folder in %s", classPath)

                # check the addon.xml with self.__ParseChannelVersionInfo(path)
                channelVersion = self.__ParseChannelVersionInfo(channelPath)
                if channelVersion:
                    self.__channelVersions.append(channelVersion)
                else:
                    # no info was returned, so we will not include the channel
                    Logger.Warning("Match in %s has incorrect version", classPath)
                    continue

                # create ChannelInfo objects from the xml file and get the correct ChannelInfo object. It coulde that none
                # is found and we might need to continue (in case there were duplicate channel names
                fileName = os.path.join(classPath, "chn_" + folderToFind + ".json")

                Logger.Debug("Loading info for chn_%s @ %s", folderToFind, fileName)
                if not os.path.isfile(fileName):
                    Logger.Warning("Could not load %s", fileName)
                    continue

                cis = ChannelInfo.FromJson(fileName)
                ci = filter(lambda c: c.moduleName == className and (c.channelCode == channelCode or c.channelCode is channelCode), cis)
                if not ci or len(ci) > 1:
                    Logger.Warning("Could not load channel with className=%s and channelCode=%s from %s", className, channelCode, fileName)
                    continue

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
                    continue

        Logger.Error("No Channel found for class '%s' and channelCode '%s'", className, channelCode)
        return channel

    def GetSingleChannel(self, className, channelCode):
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
                channelPath = os.path.join(classPath, "..")
        else:
            Logger.Warning("Missing ChannelIndex. Importing all and selecting a single.")
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
        channelInfo.textureManager.PurgeTextureCache()
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
                versionNumber = version.Version(updateParts[-1])

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
                        existingVersion = version.Version(existing.split("-")[-1])
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
            importTimer = StopWatch("ChannelImporter :: importing channels", Logger.Instance())

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
            importTimer.Lap("Directories scanned for .channel")

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

            importTimer.Lap()

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
            importTimer.Stop()
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
            packageVersion = version.Version(version=packVersion[1])
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
