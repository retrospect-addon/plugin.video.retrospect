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
import sys
import time

import xbmc

# from xbmcwrapper import XbmcWrapper
from logger import Logger, DEBUG
from environments import Environments
from config import Config

# from helpers.languagehelper import LanguageHelper


class EnvController:
    """Controller class for getting all kinds of information about the
    XBMC environment."""

    __CurrentPlatform = None
    __SQLiteEnabled = None

    def __init__(self, logger=None):
        """Class to determine platform depended stuff

        Keyword Arguments:
        logger : Logger - a logger object that is used to log information to

        """

        self.logger = logger
        pass

    def GetPythonVersion(self):
        """Returns the current python version

        Returns:
        Python version in the #.#.# format

        """

        major = sys.version_info[0]
        minor = sys.version_info[1]
        build = sys.version_info[2]
        return "%s.%s.%s" % (major, minor, build)

    @staticmethod
    def UpdateLocalAddons():
        """ Ask Kodi to update the list of local add-ons. """
        Logger.Info("Asking Kodi to update the local add-ons")
        xbmc.executebuiltin("UpdateLocalAddons")

    # def AreAddonsEnabled(self, config):
    #     """ Checks if all Retrospect channel add-ons are enabled.
    #
    #     @param config: The config object
    #     @return: True or False
    #
    #     If channel add-ons are not enabled in Kodi, they will not be auto updated.
    #     """
    #
    #     addonDir = os.path.join(config.rootDir, "..")
    #     for directory in os.listdir(addonDir):
    #         if not directory.startswith("%s.channel" % (config.addonId, )):
    #             continue
    #
    #         installed = xbmc.getCondVisibility('System.HasAddon("%s")' % (directory,)) == 1
    #         if not installed:
    #             if not os.path.isfile(os.path.join(addonDir, directory, "addon.xml")):
    #                 # no add-on, continue
    #                 continue
    #
    #             Logger.Warning("Add-on '%s' is not enabled in Kodi and will not be updated automatically", directory)
    #
    #             XbmcWrapper.ShowDialog(
    #                 LanguageHelper.GetLocalizedString(LanguageHelper.AddonsNotEnabledTitle),
    #                 LanguageHelper.GetLocalizedString(LanguageHelper.AddonsNotEnabledText))
    #             xbmc.executebuiltin("ActivateWindow(AddonBrowser, addons://user/all/, return)")
    #             return False
    #
    #         Logger.Debug("Add-on '%s' is enabled in Kodi", directory)
    #     return True

    # def IsInstallMethodValid(self, config):
    #     """ Validates that Retrospect is installed using the repository. If not
    #     it will popup a dialog box.
    #
    #     Arguments:
    #     config : Config - The Retrospect config object.
    #
    #     """
    #
    #     repoAvailable = self.__IsRepoAvailable(config)
    #
    #     if not repoAvailable:
    #         # show alert
    #         if self.logger:
    #             self.logger.Warning("No Respository installed. Reminding user to install it.")
    #
    #         XbmcWrapper.ShowDialog(LanguageHelper.GetLocalizedString(LanguageHelper.RepoWarningId), LanguageHelper.GetLocalizedString(LanguageHelper.RepoWarningDetailId))
    #
    #     return repoAvailable

    def DirectoryPrinter(self, config, settingInfo):
        """Prints out all the XOT related directories to the logFile.

        This method is mainly used for debugging purposes to provide developers a better insight
        into the system of the user.

        """

        # if we have a log level higher then debug, there is no need to do this
        if Logger.Instance().minLogLevel > DEBUG:
            Logger.Info("Not walking directory structure because the loglevel is set to INFO or higher")
            return

        directory = "<Unknown>"
        try:
            # in order to minimize the number of method resolves for os.path.join
            # we create a shortcut for it.
            ospathjoin = os.path.join

            version = xbmc.getInfoLabel("system.buildversion")
            buildDate = xbmc.getInfoLabel("system.builddate")

            repoName = self.__IsRepoAvailable(config, returnName=True)

            envCtrl = EnvController()
            infoString = "%s: %s" % ("Version", version)
            infoString = "%s\n%s: %s" % (infoString, "BuildDate", buildDate)
            infoString = "%s\n%s: %s" % (infoString, "Environment", envCtrl.__GetEnvironment())
            infoString = "%s\n%s: %s" % (infoString, "Platform", envCtrl.GetPlatform(True))
            infoString = "%s\n%s: %s" % (infoString, "Python Version", envCtrl.GetPythonVersion())
            infoString = "%s\n%s: %s" % (infoString, "Retrospect Version", config.version)
            infoString = "%s\n%s: %s" % (infoString, "AddonID", config.addonId)
            infoString = "%s\n%s: %s" % (infoString, "Path", config.rootDir)
            infoString = "%s\n%s: %s" % (infoString, "ProfilePath", config.profileDir)
            infoString = "%s\n%s: %s" % (infoString, "PathDetection", config.pathDetection)
            infoString = "%s\n%s: %s" % (infoString, "Encoding", sys.getdefaultencoding())
            infoString = "%s\n%s: %s" % (infoString, "Repository", repoName)
            infoString = "%s\n%s: %s" % (infoString, "TextureMode", config.TextureMode)
            if config.TextureUrl:
                infoString = "%s\n%s: %s" % (infoString, "TextureUrl", config.TextureUrl)

            self.logger.Info("Kodi Information:\n%s", infoString)

            # log the settings
            self.logger.Info("Retrospect Settings:\n%s", settingInfo.PrintSettingValues())

            if settingInfo.GetLogLevel() > 10:
                return

            # get the script directory
            dirScript = config.addonDir
            walkSourcePath = os.path.abspath(ospathjoin(config.rootDir, ".."))
            dirPrint = "Folder Structure of %s (%s)" % (config.appName, dirScript)

            # instead of walking all directories and files and then see if the
            # folders is in the exclude list, we first list the first children.
            # Then if the child folders contains the dirScript then, walk all
            # the subfolders and files. This greatly improves performance.
            for currentPath in os.listdir(walkSourcePath):
                self.logger.Trace("Checking %s", currentPath)
                if dirScript in currentPath:
                    self.logger.Trace("Now walking DirectoryPrinter")
                    # excludePattern = ospathjoin('a','.svn').replace("a","") -> we now have GIT and no more nested .SVN
                    dirWalker = os.walk(ospathjoin(walkSourcePath, currentPath))

                    for directory, folders, files in dirWalker:  # @UnusedVariables
                        # if directory.count(excludePattern) == 0:
                        if directory.count("BUILD") == 0:
                            for fileName in files:
                                if not fileName.startswith(".") \
                                        and not fileName.endswith(".pyo") \
                                        and not fileName.endswith(".pyc"):
                                    dirPrint = "%s\n%s" % (dirPrint, ospathjoin(directory, fileName))
            self.logger.Debug("%s" % (dirPrint, ))
        except:
            self.logger.Critical("Error printing folder %s", directory, exc_info=True)

    @staticmethod
    def GetPlatform(returnName=False):
        """Returns the platform that XBMC returns as it's host:

        Keyword Arguments:
        returnName : boolean - If true a string value is returned

        Returns:
        A string representing the host OS:
        * linux   - Normal Linux
        * Xbox    - Native Xbox
        * OS X    - Apple OS
        * Windows - Windows OS
        * unknown - in case it's undetermined

        """

        if not EnvController.__CurrentPlatform:
            # let's cache the current environment as the call to the xbmc library is very slow.
            platform = Environments.Unknown
            # it's in the .\xbmc\GUIInfoManager.cpp
            if xbmc.getCondVisibility("system.platform.linux"):
                platform = Environments.Linux
            elif xbmc.getCondVisibility("system.platform.xbox"):
                platform = Environments.Xbox
            elif xbmc.getCondVisibility("system.platform.windows"):
                platform = Environments.Windows
            elif xbmc.getCondVisibility("system.platform.ios"):
                platform = Environments.IOS
            elif xbmc.getCondVisibility("system.platform.atv2"):
                platform = Environments.ATV2
            elif xbmc.getCondVisibility("system.platform.tvos"):
                platform = Environments.TVOS
            elif xbmc.getCondVisibility("system.platform.osx"):
                platform = Environments.OSX
            elif xbmc.getCondVisibility("system.platform.android"):
                platform = Environments.Android

            EnvController.__CurrentPlatform = platform
            Logger.Info("Current platform determined to be: %s", Environments.Name(EnvController.__CurrentPlatform))

        if returnName:
            return Environments.Name(EnvController.__CurrentPlatform)
        else:
            return EnvController.__CurrentPlatform

    @staticmethod
    def IsPlatform(platform):
        """Checks if the current platform matches the requested on

        Arguments:
        platform : string - The requested platform

        Returns:
        True if the <platform> matches EnvController.GetPlatform().

        """

        plat = EnvController.GetPlatform()

        # check if the actual platform is in the platform bitmask
        # return plat & platform  == platform
        return platform & plat == plat

    @staticmethod
    def CacheCheck():
        """Checks if the cache folder exists. If it does not exists
        It will be created.

        Returns False it the folder initially did not exist

        """

        # check for cache folder. If not present. Create it!
        if not os.path.exists(Config.cacheDir):
            Logger.Info("Creating cache folder at: %s", Config.cacheDir)
            os.makedirs(Config.cacheDir)
            return False

        return True

    @staticmethod
    def CacheCleanUp(path, cacheTime, mask="*.*"):
        """Cleans up the XOT cache folder.

        Check the cache files create timestamp and compares it with the current datetime extended
        with the amount of seconds as defined in cacheTime.

        Expired items are deleted.

        """

        # let's import htis one here
        import glob

        try:
            Logger.Info("Cleaning up cache in '%s' that is older than %s days", path, cacheTime / 24 / 3600)
            if not os.path.exists(path):
                Logger.Info("Did not cleanup cache: folder does not exist")
                return

            deleteCount = 0
            fileCount = 0

            #for item in os.listdir(path):
            pathMask = os.path.join(path, mask)
            for item in glob.glob(pathMask):
                fileName = os.path.join(path, item)
                if os.path.isfile(fileName):
                    Logger.Trace(fileName)
                    fileCount += 1
                    createTime = os.path.getctime(fileName)
                    if createTime + cacheTime < time.time():
                        os.remove(fileName)
                        Logger.Debug("Removed file: %s", fileName)
                        deleteCount += 1
            Logger.Info("Removed %s of %s files from cache in: '%s'", deleteCount, fileCount, pathMask)
        except:
            Logger.Critical("Error cleaning the cachefolder: %s", path, exc_info=True)

    def __GetEnvironment(self):
        """Gets the type of environment

        Returns:
        A string defining the OS:
        * Linux   - Normal Linux
        * Linux64 - 64-bit Linux
        * OS X    - For Apple decices
        * win32   - Windows / Native Xbox

        """

        env = os.environ.get("OS", "win32")
        if env == "Linux":
            # (bits, type) = platform.architecture()
            # if bits.count("64") > 0:
            #     # first the bits of platform.architecture is checked
            #     return "Linux64"
            if sys.maxint >> 33:
                # double check using the sys.maxint
                # and see if more than 32 bits are present
                return "Linux64"
            else:
                return "Linux"
        elif env == "OS X":
            return "OS X"
        else:
            return "win32"

    def __IsRepoAvailable(self, config, returnName=False):
        """ Checks if the repository is available in XBMC and returns it's name.

        Arguments:
        config     : Config  - The configuration object of Retrospect

        Keyword Arguments:
        returnName : Boolean - [opt] If set to True the name of the repository will
                               be returned or a label with the reason why no repo
                               was found.

        """

        NOT_INSTALLED = "<not installed>"
        UNKWOWN = "<data only available in Eden builds>"

        if EnvController.IsPlatform(Environments.Xbox):
            if self.logger:
                self.logger.Debug("Skipping repository check on Xbox.")

            if returnName:
                # on Xbox it's never installed.
                return NOT_INSTALLED
            else:
                # always return True for Xbox
                return True

        if xbmc.getInfoLabel("system.buildversion").startswith("10."):
            if self.logger:
                self.logger.Debug("Skipping repository check on 10.x builds.")

            if returnName:
                return UNKWOWN
            else:
                # always return True
                return True

        try:
            repoName = "%s.repository" % (config.addonId,)
            repoAvailable = xbmc.getCondVisibility('System.HasAddon("%s")' % (repoName,)) == 1

            if self.logger:
                self.logger.Debug("Checking repository '%s'. Repository available=%s", repoName, repoAvailable)

            if not returnName:
                # return a boolean
                return repoAvailable
            elif repoAvailable:
                # return the name if it was available
                return repoName
            else:
                # return not installed if non was available
                return NOT_INSTALLED
        except:
            self.logger.Error("Error determining Repository Status", exc_info=True)
            if not returnName:
                # in case of error, return True
                return True
            else:
                return "<error>"
