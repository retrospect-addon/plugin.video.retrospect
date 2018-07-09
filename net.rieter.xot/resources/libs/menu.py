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
from addonsettings import AddonSettings
from paramparser import ParameterParser
from helpers.sessionhelper import SessionHelper
from helpers.channelimporter import ChannelIndex
from helpers.htmlentityhelper import HtmlEntityHelper
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
        if not params:
            return

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

    def HideChannel(self):
        Logger.Info("Hiding channel: %s", self.channelObject)
        AddonSettings.SetChannelVisiblity( self.channelObject, False)
        self.Refresh()

    def SelectChannels(self):
        validChannels = ChannelIndex.GetRegister().GetChannels(includeDisabled=True)
        selectedChannels = filter(lambda c: c.enabled, validChannels)
        selectedIndices = map(lambda c: validChannels.index(c), selectedChannels)
        Logger.Debug("Currently selected channels: %s", selectedIndices)

        validChannelNames = map(lambda c: HtmlEntityHelper.ConvertHTMLEntities(c.channelName),
                                validChannels)

        dialog = xbmcgui.Dialog()
        selectedChannels = dialog.multiselect("Select Enabled Channels", validChannelNames,
                                              preselect=selectedIndices)
        if selectedChannels is None:
            return

        selectedChannels = list(selectedChannels)
        Logger.Debug("New selected channels:       %s", selectedChannels)

        # TODO: we actually need to do something with them
        indicesToRemove = filter(lambda i: i not in selectedChannels, selectedIndices)
        indicesToAdd = filter(lambda i: i not in selectedIndices, selectedChannels)
        for i in indicesToRemove:
            Logger.Info("Hiding channel: %s", validChannels[i])
            AddonSettings.SetChannelVisiblity(validChannels[i], False)
            pass

        for i in indicesToAdd:
            Logger.Info("Showing channel: %s", validChannels[i])
            AddonSettings.SetChannelVisiblity(validChannels[i], True)

        self.Refresh()
        return

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
