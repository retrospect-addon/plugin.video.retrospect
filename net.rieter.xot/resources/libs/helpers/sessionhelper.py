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
import time

from config import Config


class SessionHelper:
    __TimeOut = 1 * 60 * 60
    #__TimeOut = 10

    def __init__(self):
        # static only
        raise NotImplementedError()

    @staticmethod
    def CreateSession(logger=None):
        """ Creates a session file in the add-on data folder. This file indicates
        that we passed the channel selection screen. It's main purpose is to be
        able to distinguish between coming back to the channel selection screen
        (in which case a session file was present) or starting the add-on and
        getting to the channel screen. In the latter case we want to show some
        extra data.

        """

        if not SessionHelper.IsSessionActive() and logger:
            logger.Debug("Creating session at '%s'", SessionHelper.__GetSessionPath())
        elif logger:
            logger.Debug("Updating session at '%s'", SessionHelper.__GetSessionPath())

        if logger:
            fd = open(SessionHelper.__GetSessionPath(), 'w')
            fd.write(str(logger.minLogLevel))
            fd.close()
        else:
            open(SessionHelper.__GetSessionPath(), 'w').close()

    @staticmethod
    def ClearSession(logger=None):
        """ Clears the active session indicator by deleting the file """

        if os.path.isfile(SessionHelper.__GetSessionPath()):
            if logger:
                logger.Warning("Clearing session at '%s'", SessionHelper.__GetSessionPath())
            os.remove(SessionHelper.__GetSessionPath())
        elif logger:
            logger.Debug("No session to clear")

        return

    @staticmethod
    def IsSessionActive(logger=None):
        """ Returns True if an active session file is found """

        if logger:
            logger.Debug("Checking for active sessions (%.2f minutes / %.2f hours).", SessionHelper.__TimeOut / 60, SessionHelper.__TimeOut / 3600.0)

        if not os.path.isfile(SessionHelper.__GetSessionPath()):
            if logger:
                logger.Debug("No active sessions found.")
            return False

        timeStamp = os.path.getmtime(SessionHelper.__GetSessionPath())
        nowStamp = time.time()
        modifiedInLastHours = (nowStamp - SessionHelper.__TimeOut) < timeStamp

        logLevel = None
        # try to determine whether we have a new loglevel in this session, if so, we reset the session to get all
        # required debug data. But we can only do that with a logger.
        if logger:
            try:
                fd = open(SessionHelper.__GetSessionPath())
                logLevel = fd.readline()
                fd.close()
                if not logLevel == "":
                    # logger.Trace("Found previous loglevel: %s vs current: %s", logLevel, logger.minLogLevel)
                    newLogLevelFound = not logger.minLogLevel == int(logLevel)
                else:
                    newLogLevelFound = False
            except:
                logger.Error("Error determining previous loglevel", exc_info=True)
                newLogLevelFound = False
        else:
            newLogLevelFound = False

        if logger and newLogLevelFound:
            logger.Debug("Found active session at '%s' with an old loglevel '%s' vs '%s', resetting session",
                         SessionHelper.__GetSessionPath(), logLevel, logger.minLogLevel)
            modifiedInLastHours = False

        elif logger and modifiedInLastHours:
            logger.Debug("Found active session at '%s' which was modified %.2f minutes (%.2f hours) ago",
                         SessionHelper.__GetSessionPath(), (nowStamp - timeStamp) / 60, (nowStamp - timeStamp) / 3600.0)

        elif logger:
            logger.Debug("Found expired session at '%s' which was modified %.2f minutes (%.2f hours) ago",
                         SessionHelper.__GetSessionPath(), (nowStamp - timeStamp) / 60, (nowStamp - timeStamp) / 3600.0)

        return modifiedInLastHours

    @staticmethod
    def __GetSessionPath():
        """ Returns the session file path """

        return os.path.join(Config.profileDir, "xot.session.lock")
