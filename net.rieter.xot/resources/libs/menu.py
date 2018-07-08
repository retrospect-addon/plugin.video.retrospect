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
import xbmc
import xbmcgui

from config import Config
from logger import Logger
from helpers.sessionhelper import SessionHelper
from helpers.channelimporter import ChannelIndex
from addonsettings import AddonSettings
from paramparser import ParameterParser
from helpers.languagehelper import LanguageHelper
from pickler import Pickler
from cloaker import Cloaker
from xbmcwrapper import XbmcWrapper

# only append if there are no active sessions
if not SessionHelper.IsSessionActive():
    # first call in the session, so do not append the log
    appendLogFile = False
else:
    appendLogFile = True


class Menu(ParameterParser):
    def __enter__(self):
        Logger.CreateLogger(os.path.join(Config.profileDir, Config.logFileNameAddon),
                            Config.appName,
                            append=appendLogFile,
                            dualLogger=lambda x, y=4: xbmc.log(x, y))
        Logger.Info("****** Starting menu for %s add-on version %s *******", Config.appName, Config.version)

        return Menu()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            Logger.Critical("Error in menu handling: %s", exc_val.message, exc_info=True)

        # make sure we leave no references behind
        Logger.Instance().CloseLog()
        AddonSettings.ClearCachedAddonSettingsObject()
        return False

    def __init__(self):

        # noinspection PyUnresolvedReferences
        self.kodiItem = sys.listitem
        self.channelObject = self.__GetChannel()

        params = self.kodiItem.getPath()
        name, params = params.split("?", 1)
        params = "?{0}".format(params)

        # Main constructor parses
        super(Menu, self).__init__(name, params)

        Logger.Debug("Plugin Params: %s (%s)\n"
                     "Name:        %s\n"
                     "Query:       %s", self.params, len(self.params), self.pluginName, params)

        if self.keywordPickle in self.params:
            self.mediaItem = Pickler.DePickleMediaItem(self.params[self.keywordPickle])
        else:
            self.mediaItem = None

    def SelectChannels(self):
        multiSelectValues = ChannelIndex.GetRegister().GetChannels(includeDisabled=True)
        enabledChannels = filter(lambda c: c.enabled, multiSelectValues)

        enabledListItems = map(lambda c: c.safeName, enabledChannels)
        selectedIndices = map(lambda c: multiSelectValues.index(c), enabledChannels)

        dialog = xbmcgui.Dialog()
        selectedChannels = dialog.multiselect("Select Enabled Channels", enabledListItems,
                                              preselect=selectedIndices)

        # TODO: we actually need to do something with them
        return selectedChannels

    def ShowSettings(self):
        AddonSettings.ShowSettings()

    def ChannelSettings(self):
        AddonSettings.ShowChannelSettings(self.channelObject)
        pass

    def Refresh(self):
        xbmc.executebuiltin("XBMC.Container.Refresh()")
        return

    def ToggleCloak(self):
        item = Pickler.DePickleMediaItem(self.params[self.keywordPickle])
        Logger.Info("Cloaking current item: %s", item)
        c = Cloaker(Config.profileDir, self.channelObject.guid, logger=Logger.Instance())
        if c.IsCloaked(item.url):
            c.UnCloak(item.url)
            self.Refresh()
            return

        firstTime = c.Cloak(item.url)
        if firstTime:
            XbmcWrapper.ShowDialog(LanguageHelper.GetLocalizedString(LanguageHelper.CloakFirstTime),
                                   LanguageHelper.GetLocalizedString(LanguageHelper.CloakMessage))

        self.Refresh()

    def __GetChannel(self):
        # noinspection PyUnresolvedReferences
        chn, code = self.kodiItem.getProperty("Retrospect").split("|")
        # chn = "chn_nos2010"
        # code = "uzgjson"
        if not chn:
            return None
        code = code or None
        Logger.Debug("Fetching channel %s - %s", chn, code)
        channel = ChannelIndex.GetRegister().GetChannel(chn, code, infoOnly=True)
        return channel
