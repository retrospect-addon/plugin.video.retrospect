#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import re

from helpers.jsonhelper import JsonHelper
from version import Version


class Updater:
    __regex = None

    def __init__(self, updateUrl, currentVersion, uriHandler, logger):
        """ Initiates a Updater class """

        if not updateUrl:
            raise ValueError("Missing update url")
        if not currentVersion:
            raise ValueError("Missing current version")
        if not uriHandler:
            raise ValueError("Missing UriHandler")

        self.updateUrl = updateUrl
        self.currentVersion = currentVersion
        self.onlineVersion = None

        self.__logger = logger
        self.__uriHandler = uriHandler

    def IsNewVersionAvailable(self):
        try:
            self.onlineVersion = self.__getOnlineVersion()
            if self.onlineVersion is None:
                return False

            self.__logger.Debug("Found online version: %s", self.onlineVersion)
            return self.currentVersion < self.onlineVersion
        except:
            self.__logger.Error("Error checking for updates", exc_info=True)
            return False

    def __getOnlineVersion(self):
        data = self.__uriHandler.Open(self.updateUrl, noCache=True)
        jsonData = JsonHelper(data)
        onlineDownloads = list(filter(lambda d: self.__isValidUpdate(d), jsonData.GetValue("values")))
        if len(onlineDownloads) == 0:
            return None

        onlineDownload = onlineDownloads[0]
        onlineParts = onlineDownload['name'].rsplit(".", 1)[0].split("-")
        if len(onlineParts) < 2:
            return None

        # fix the problem that a ~ is preventing downloads on BitBucket
        onlineVersionData = onlineParts[1].replace("alpha", "~alpha").replace("beta", "~beta")
        onlineVersion = Version(onlineVersionData)
        return onlineVersion

    def __isValidUpdate(self, download):
        name = download.get("name")
        if name is None:
            return False

        if Updater.__regex is None:
            Updater.__regex = re.compile(
                "^net\.rieter\.xot-\d+\.\d+\.\d+(\.\d+)?(~?(alpha|beta)\d+)?\.zip",
                re.IGNORECASE)

        return Updater.__regex.match(name) is not None
