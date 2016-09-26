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
    def __init__(self, profilePath, channelId, logger=None):
        # type: (str, str, Logger) -> Cloaker
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
            self.__cloaked = dict()
            self.__logger.Info("Creating a new cloaked settings file at '%s'", self.__cloakedSettings)
            self.__Store()

        with file(self.__cloakedSettings, mode='r') as fp:
            self.__cloaked = JsonHelper.Loads(fp.read())

        if self.__channelId not in self.__cloaked:
            self.__cloaked[self.__channelId] = {}
            self.__Store()

        if self.__logger:
            self.__logger.Trace("Found cloaked data:\n%s", JsonHelper.Dump(self.__cloaked, prettyPrint=True))

    def Cloak(self, url):
        # type: (str) -> None
        """ Cloaks a specific URL from future listing.

        @param url: the url to cloak.
        """

        if url in self.__cloaked[self.__channelId]:
            if self.__logger:
                self.__logger.Debug("'%s' in channel '%s' was already cloaked.", url, self.__channelId)
            return

        if self.__logger:
            self.__logger.Debug("Cloaking '%s' in channel '%s'", url, self.__channelId)

        self.__cloaked[self.__channelId][url] = {}
        self.__Store()
        return

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

    def __Store(self):
        # type: () -> None
        """ Store the current cloak information to the profile folder. """
        with file(self.__cloakedSettings, mode='w') as fp:
            if self.__logger:
                self.__logger.Info("Storing Cloaking information to cloak file '%s'.", self.__cloakedSettings)
            fp.write(JsonHelper.Dump(self.__cloaked, prettyPrint=True))


if __name__ == '__main__':
    cloakPath = os.path.join("..", "..", "..", "..", "net.rieter.xot.userdata")
    cloakPath = os.path.abspath(cloakPath)

    # noinspection PyUnusedLocal
    class DummyLogger:
        """ Just a dummy logger class that can be used to test"""

        def __init__(self):
            pass

        def Error(self, message, *args, **kwargs):
            message = "Dummy ERROR >> %s" % (message,)
            print message % args

        def Info(self, message, *args, **kwargs):
            message = "Dummy INFO >> %s" % (message,)
            print message % args

        def Debug(self, message, *args, **kwargs):
            message = "Dummy DEBUG >> %s" % (message,)
            print message % args

        def Trace(self, message, *args, **kwargs):
            message = "Dummy TRACE >> %s" % (message,)
            print message % args

    c = Cloaker(cloakPath, "channel2", logger=DummyLogger())
    c.Cloak("test1")
    c.Cloak("test2")
    c.Cloak("test2")
    print c.IsCloaked("test1")
    print c.IsCloaked("test2")
    print c.IsCloaked("test3")
    c.UnCloak("test2")
    c = Cloaker(cloakPath, "channel2", logger=DummyLogger())
    # print c._Cloaked__cloaked
