#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import os.path
import sys

import xbmc


def RunPlugin():
    """ Runs Retrospect as a Video Add-On """

    logFile = None

    try:
        from config import Config
        from helpers.sessionhelper import SessionHelper

        # get a logger up and running
        from logger import Logger

        # only append if there are no active sessions
        if not SessionHelper.IsSessionActive():
            # first call in the session, so do not append the log
            appendLogFile = False
        else:
            appendLogFile = True
        logFile = Logger.CreateLogger(os.path.join(Config.rootDir, Config.logFileNameAddon), Config.appName,
                                      append=appendLogFile, memoryInfoProvider=xbmc.getFreeMem,
                                      dualLogger=lambda x, y=4: xbmc.log(x, y))

        from urihandler import UriHandler
        from addonsettings import AddonSettings

        # update the loglevel
        Logger.Instance().minLogLevel = AddonSettings.GetLogLevel()

        useCaching = AddonSettings.CacheHttpResponses()
        cacheDir = None
        if useCaching:
            cacheDir = Config.cacheDir

        # determine the platform
        from envcontroller import EnvController
        from environments import Environments
        maxFileNameLength = None
        if EnvController.IsPlatform(Environments.Xbox):
            maxFileNameLength = 42

        UriHandler.CreateUriHandler(cacheDir=cacheDir, maxFileNameLength=maxFileNameLength)

        # run the plugin
        import plugin
        plugin.Plugin(sys.argv[0], sys.argv[2], sys.argv[1])

        # close the log to prevent locking on next call
        Logger.Instance().CloseLog()
        logFile = None

        # make sure we leave no references behind
        AddonSettings.ClearCachedAddonSettingsObject()
    except:
        if logFile:
            logFile.Critical("Error running plugin", exc_info=True)
        raise


# setup the paths in Python
from initializer import Initializer
Initializer.SetUnicode()
currentPath = Initializer.SetupPythonPaths()

# ANY OF THESE SETTINGS SHOULD ONLY BE ENABLED FOR DEBUGGING PURPOSES
# from debug import remotedebugger
# debugger = remotedebugger.RemoteDebugger()

# import profile as cProfile
# import cProfile
# from debug import profilelinebyline as cProfile

# Path for PC
# statsPath = os.path.abspath(os.path.join(currentPath, "../data/retrospect.pc.pstats"))
# Path for ATV
# statsPath = os.path.abspath("/private/var/mobile/retrospect.atv.pstats")
# Path for rPi
# statsPath = os.path.abspath("/home/pi/.kodi/addons/net.rieter.xot/retrospect.rpi.pstats")

# Profiled run
# cProfile.run("RunPlugin()", statsPath)
# Normal run
RunPlugin()