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
from logger import Logger


class Updater:
    __regex = None

    def __init__(self, update_url, current_version, uri_handler, logger):
        """ Initiates a Updater class

        :param str update_url:
        :param Version current_version:
        :param any uri_handler:
        :param Logger logger:
        """

        if not update_url:
            raise ValueError("Missing update url")
        if not current_version:
            raise ValueError("Missing current version")
        if not uri_handler:
            raise ValueError("Missing UriHandler")

        self.updateUrl = update_url
        self.currentVersion = current_version
        self.onlineVersion = None

        self.__logger = logger
        self.__uriHandler = uri_handler

    def is_new_version_available(self):
        """ Check if a new version is available online.

        :return: Indication if a newer version is available
        :rtype: str

        """

        try:
            self.onlineVersion = self.__get_online_version()
            if self.onlineVersion is None:
                return False

            self.__logger.debug("Found online version: %s", self.onlineVersion)
            return self.currentVersion < self.onlineVersion
        except:
            self.__logger.error("Error checking for updates", exc_info=True)
            return False

    def __get_online_version(self):
        """ Retrieves the current online version.

        :return: Returns the current online version or `None` of no version was found.
        :rtype: None|Version

        """
        data = self.__uriHandler.open(self.updateUrl, noCache=True)
        json_data = JsonHelper(data)
        online_downloads = list(filter(lambda d: self.__is_valid_update(d), json_data.get_value("values")))
        if len(online_downloads) == 0:
            return None

        online_download = online_downloads[0]
        online_parts = online_download['name'].rsplit(".", 1)[0].split("-")
        if len(online_parts) < 2:
            return None

        # fix the problem that a ~ is preventing downloads on BitBucket
        online_version_data = online_parts[1].replace("alpha", "~alpha").replace("beta", "~beta")
        online_version = Version(online_version_data)
        return online_version

    def __is_valid_update(self, download):
        """ Checks if the found API entry is indeed an update.

        :param dict[str, Any] download: The information from the API.

        :return: Indication if the found download indeed points to a download.
        :rtype: bool

        """

        name = download.get("name")
        if name is None:
            return False

        if Updater.__regex is None:
            Updater.__regex = re.compile(
                "^net\.rieter\.xot-\d+\.\d+\.\d+(\.\d+)?(~?(alpha|beta)\d+)?\.zip",
                re.IGNORECASE)

        return Updater.__regex.match(name) is not None
