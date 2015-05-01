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
import shutil
import zipfile

from regexer import Regexer
from xbmcwrapper import XbmcWrapper  # , XbmcDialogProgressWrapper
from addonsettings import AddonSettings
from config import Config
from version import Version
# from helpers import channelimporter -> Can't use this one here, because
# we are doing this before importing any channels
from helpers.languagehelper import LanguageHelper

#===============================================================================
# Make global object available
#===============================================================================
from logger import Logger
from urihandler import UriHandler


class Updater:
    def __init__(self):
        """ Initiates a Updater class """

        self.__NewMd5 = None
        self.__OldMd5 = None

    def AutoUpdate(self):
        """ Performs an auto update of channels """

        if not self.__IsNewVersionAvailable():
            return

        # find the updates
        availableUpdates = self.__GetAvailableUpdates()

        # download them
        for (url, filename) in availableUpdates:
            self.__UpdateFromUrl(url, filename)

        # always update the MD5 hash if we get to this point
        Logger.Debug("Updating MD5 to: %s", self.__NewMd5)
        AddonSettings.UpdateCurrentAddonXmlMd5(self.__NewMd5)

    def __IsNewVersionAvailable(self):
        """ Verifies that there is a new version available. It compares the addons.xml.md5 with the stored one.

        @return: True or False
        """

        # first check if there is a "channel" folder
        channelPath = os.path.join(Config.rootDir, "channels")
        if not os.path.isdir(channelPath):
            Logger.Warning("No Channels found at '%s', skipping updates for now.", channelPath)
            return False

        onlineData = UriHandler.Open(Config.UpdateUrl)
        self.__NewMd5 = onlineData.strip()
        self.__OldMd5 = AddonSettings.GetCurrentAddonXmlMd5()

        updated = self.__OldMd5 != self.__NewMd5
        if updated:
            Logger.Info("New updates are available ('%s' vs '%s')", self.__OldMd5, self.__NewMd5)
        else:
            Logger.Info("No new updates available, MD5 hashes match")
        return updated

    def __GetAvailableUpdates(self):
        """ Opens the addon.xml and fetches all updates. Compares them with the installed versions and returns a list
        of URL's to download

        @return: a list of URLs
        """

        data = UriHandler.Open(Config.UpdateUrl.replace(".md5", ""))
        channels = Regexer.DoRegex('<addon\W+id="(net.rieter.xot(?:.channel.[^"]+|))\W+version="([^"]+)"', data)
        updates = []

        for channel in channels:
            addonId = channel[0]
            addonVersion = channel[1]
            if addonId == Config.addonId:
                Logger.Debug("Found main Retrospect version: %s", addonVersion)
                # the main XOT add-on
                if Version(version=addonVersion) != Config.version:
                    Logger.Warning("Not deploying new channels because Retrospect versions do not match: "
                                   "Installed %s vs Online %s", Config.version, addonVersion)
                    message = LanguageHelper.GetLocalizedString(LanguageHelper.NewVersion2Id, splitOnPipes=False)
                    message = message % (Config.appName, addonVersion)
                    XbmcWrapper.ShowDialog(LanguageHelper.GetLocalizedString(LanguageHelper.NewVersionId),
                                           message.split("|"))
                    return []
            else:
                # set the zipfile name here, but check in the next loop!
                channelId = "%s-%s" % (addonId, addonVersion)
                if self.__IsVersionInstalled(addonId, addonVersion):
                    # already installed, continue as if
                    Logger.Info("Update already installed: %s", channelId)
                    continue
                else:
                    url = "http://www.rieter.net/net.rieter.xot.repository/%s/%s-%s.zip" % (addonId, addonId, addonVersion)
                    filename = "%s-%s.zip" % (addonId, addonVersion)
                    Logger.Info("New update found: %s @ %s", channelId, url)
                    updates.append((url, filename))
        return updates

    # noinspection PyUnusedLocal
    def __RetrieveProgressDummy(self, retrievedSize, totalSize, perc, completed, status):
        Logger.Debug("Retreived: %s from %s (%s %)", retrievedSize, totalSize, perc)
        return False

    def __UpdateFromUrl(self, url, zipName):
        """ Update a channel from an URL

        @param url:     The url to download
        @param zipName: The name to give the download

        """

        Logger.Info("Going to update from %s", url)
        # wrapper = XbmcDialogProgressWrapper("Updating XOT", url)
        # destFilename = UriHandler.Download(url, zipName, Config.cacheDir, wrapper.ProgressUpdate)
        destFilename = UriHandler.Download(url, zipName, Config.cacheDir, self.__RetrieveProgressDummy)
        Logger.Debug("Download succeeded: %s", destFilename)

        # we extract to the deploy folder, so with the first start of XOT, the new channel is deployed
        deployDir = os.path.abspath(os.path.join(Config.rootDir, "deploy"))
        zipFile = zipfile.ZipFile(destFilename)

        # now extract
        first = True
        Logger.Debug("Extracting %s to %s", destFilename, deployDir)
        for name in zipFile.namelist():
            if first:
                folder = os.path.split(name)[0]
                if os.path.exists(os.path.join(deployDir, folder)):
                    shutil.rmtree(os.path.join(deployDir, folder))
                first = False

            if not name.endswith("/") and not name.endswith("\\"):
                fileName = os.path.join(deployDir, name)
                path = os.path.dirname(fileName)
                if not os.path.exists(path):
                    os.makedirs(path)
                Logger.Debug("Extracting %s", fileName)
                outfile = open(fileName, 'wb')
                outfile.write(zipFile.read(name))
                outfile.close()

        zipFile.close()
        os.remove(destFilename)
        Logger.Info("Update completed and zip file (%s) removed", destFilename)

        message = LanguageHelper.GetLocalizedString(LanguageHelper.UpdateCompleteId, splitOnPipes=False) % (zipName.replace(".zip", ""), )
        message = message.split("|")
        XbmcWrapper.ShowNotification(LanguageHelper.GetLocalizedString(LanguageHelper.RestartId), message, displayTime=5000, logger=Logger.Instance())

    def __IsVersionInstalled(self, addonId, version):
        """ Checks if channel with a version is installed

        @param addonId: the addon id (net.rieter.xot.channel.<name>)
        @param version: the version (x.x.x.x)
        @return: True of False
        """

        Logger.Debug("Is %s-%s installed?", addonId, version)
        addonXml = os.path.join(Config.rootDir, "channels", addonId, "addon.xml")
        Logger.Debug("Trying to locate: %s", addonXml)
        if os.path.exists(addonXml):
            fp = file(addonXml)
            addonData = fp.read()
            fp.close()
            return "%s" % (version,) in addonData
        else:
            return False