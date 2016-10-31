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
from helpers.jsonhelper import JsonHelper


class Cloaker:
    __MESSAGE_SHOWN = "messageShown"

    def __init__(self, profilePath, channelId, logger=None):
        # type: (str, str, Logger) -> None
        """ Creates a Cloaker object that helps with cloaking objects

        @param profilePath: the path to the Kodi profile settings folder.
        @param channelId:   the GUID of the channel for which we need cloak information.
        @param logger:      a Logger object for logging purposes.

        """

        self.__cloakedSettings = os.path.join(profilePath, "cloaked.json")
        self.__logger = logger
        self.__channelId = channelId

        if self.__logger:
            self.__logger.Debug("Setting up a Cloaker based on '%s'", self.__cloakedSettings)

        # Create a new file if none existed
        if not os.path.exists(self.__cloakedSettings):
            self.__cloaked = {Cloaker.__MESSAGE_SHOWN: False}
            if self.__logger:
                self.__logger.Info("Creating a new cloaked settings file at '%s'", self.__cloakedSettings)
            # store but keep the first time message
            self.__Store(False)

        with file(self.__cloakedSettings, mode='r') as fp:
            self.__cloaked = JsonHelper.Loads(fp.read())

        if self.__channelId not in self.__cloaked:
            self.__cloaked[self.__channelId] = {}
            # store but keep the first time message
            self.__Store(False)

        if self.__logger:
            self.__logger.Trace("Found cloaked data:\n%s", JsonHelper.Dump(self.__cloaked, prettyPrint=True))

    def Cloak(self, url):
        # type: (str) -> bool
        """ Cloaks a specific URL from future listing.

        @param url: the url to cloak.
        @return: boolean indicating whether this was the first cloak or not.

        """

        if url in self.__cloaked[self.__channelId]:
            if self.__logger:
                self.__logger.Debug("'%s' in channel '%s' was already cloaked.", url, self.__channelId)
            return False

        if self.__logger:
            self.__logger.Debug("Cloaking '%s' in channel '%s'", url, self.__channelId)

        self.__cloaked[self.__channelId][url] = {}
        return self.__Store()

    def UnCloak(self, url):
        # type: (str) -> None
        """ Uncloak an URL and make sure it is not cloaked anymore.

        @param url: the URL to uncloak.
        """

        if url not in self.__cloaked[self.__channelId]:
            if self.__logger:
                self.__logger.Debug("'%s' in channel '%s' was not cloaked.", url, self.__channelId)
            return

        if self.__logger:
            self.__logger.Debug("Un-cloaking '%s' in channel '%s'", url, self.__channelId)

        self.__cloaked[self.__channelId].pop(url, None)
        self.__Store()
        return

    def IsCloaked(self, url):
        # type: (str) -> bool
        """ Checks whether an URL is cloaked or not.

        @param url: the URL to check
        @return:    a boolean value indicating whether the url is cloaked (True) or not (False)
        """

        return url in self.__cloaked[self.__channelId]

    def __Store(self, updateFirstTimeMessage=True):
        # type: () -> bool
        """ Store the current cloak information to the profile folder.

        @type updateFirstTimeMessage: bool
        @return: boolean indicating whether this was the first run.

        """

        firstTime = not self.__cloaked.get(Cloaker.__MESSAGE_SHOWN, False)

        # update the first time message setting unless we should not.
        if updateFirstTimeMessage:
            self.__cloaked[Cloaker.__MESSAGE_SHOWN] = updateFirstTimeMessage

        with file(self.__cloakedSettings, mode='w') as fp:
            if self.__logger:
                self.__logger.Info("Storing Cloaking information to cloak file '%s'.", self.__cloakedSettings)
            fp.write(JsonHelper.Dump(self.__cloaked, prettyPrint=True))

        if self.__logger:
            self.__logger.Debug("First time cloak found.")
        return firstTime
