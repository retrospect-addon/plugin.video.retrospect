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
    def create_session(logger=None):
        """ Creates a session file in the add-on data folder. This file indicates
        that we passed the channel selection screen. It's main purpose is to be
        able to distinguish between coming back to the channel selection screen
        (in which case a session file was present) or starting the add-on and
        getting to the channel screen. In the latter case we want to show some
        extra data.

        """

        if not SessionHelper.is_session_active() and logger:
            logger.debug("Creating session at '%s'", SessionHelper.__get_session_path())
        elif logger:
            logger.debug("Updating session at '%s'", SessionHelper.__get_session_path())

        if logger:
            fd = open(SessionHelper.__get_session_path(), 'w')
            fd.write(str(logger.minLogLevel))
            fd.close()
        else:
            open(SessionHelper.__get_session_path(), 'w').close()

    @staticmethod
    def clear_session(logger=None):
        """ Clears the active session indicator by deleting the file """

        if os.path.isfile(SessionHelper.__get_session_path()):
            if logger:
                logger.warning("Clearing session at '%s'", SessionHelper.__get_session_path())
            os.remove(SessionHelper.__get_session_path())
        elif logger:
            logger.debug("No session to clear")

        return

    @staticmethod
    def is_session_active(logger=None):
        """ Returns True if an active session file is found """

        if logger:
            logger.debug("Checking for active sessions (%.2f minutes / %.2f hours).", SessionHelper.__TimeOut / 60, SessionHelper.__TimeOut / 3600.0)

        if not os.path.isfile(SessionHelper.__get_session_path()):
            if logger:
                logger.debug("No active sessions found.")
            return False

        time_stamp = os.path.getmtime(SessionHelper.__get_session_path())
        now_stamp = time.time()
        modified_in_last_hours = (now_stamp - SessionHelper.__TimeOut) < time_stamp

        log_level = None
        # try to determine whether we have a new loglevel in this session, if so, we reset the session to get all
        # required debug data. But we can only do that with a logger.
        if logger:
            try:
                fd = open(SessionHelper.__get_session_path())
                log_level = fd.readline()
                fd.close()
                if not log_level == "":
                    # logger.Trace("Found previous loglevel: %s vs current: %s", logLevel, logger.minLogLevel)
                    new_log_level_found = not logger.minLogLevel == int(log_level)
                else:
                    new_log_level_found = False
            except:
                logger.error("Error determining previous loglevel", exc_info=True)
                new_log_level_found = False
        else:
            new_log_level_found = False

        if logger and new_log_level_found:
            logger.debug("Found active session at '%s' with an old loglevel '%s' vs '%s', resetting session",
                         SessionHelper.__get_session_path(), log_level, logger.minLogLevel)
            modified_in_last_hours = False

        elif logger and modified_in_last_hours:
            logger.debug("Found active session at '%s' which was modified %.2f minutes (%.2f hours) ago",
                         SessionHelper.__get_session_path(), (now_stamp - time_stamp) / 60, (now_stamp - time_stamp) / 3600.0)

        elif logger:
            logger.debug("Found expired session at '%s' which was modified %.2f minutes (%.2f hours) ago",
                         SessionHelper.__get_session_path(), (now_stamp - time_stamp) / 60, (now_stamp - time_stamp) / 3600.0)

        return modified_in_last_hours

    @staticmethod
    def __get_session_path():
        """ Returns the session file path """

        return os.path.join(Config.profileDir, "xot.session.lock")
