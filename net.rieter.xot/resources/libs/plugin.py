# coding=utf-8
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

#import inspect

import xbmcplugin
import xbmc
import xbmcgui

try:
    import envcontroller

    from logger import Logger
    from addonsettings import AddonSettings
    from locker import LockWithDialog
    from config import Config
    from channelinfo import ChannelInfo
    from xbmcwrapper import XbmcWrapper, XbmcDialogProgressWrapper, XbmcDialogProgressBgWrapper
    from environments import Environments
    from initializer import Initializer
    from favourites import Favourites
    from mediaitem import MediaItem
    from helpers.channelimporter import ChannelIndex
    from helpers.languagehelper import LanguageHelper
    from helpers.htmlentityhelper import HtmlEntityHelper
    from helpers.stopwatch import StopWatch
    from helpers.statistics import Statistics
    from helpers.sessionhelper import SessionHelper
    from textures import TextureHandler
    from paramparser import ParameterParser
    from updater import Updater
    from urihandler import UriHandler
except:
    Logger.critical("Error initializing %s", Config.appName, exc_info=True)


#===============================================================================
# Main Plugin Class
#===============================================================================
class Plugin(ParameterParser):
    """Main Plugin Class

    This class makes it possible to access all the XOT channels as a Kodi Add-on
    instead of a script.

    """

    def __init__(self, pluginName, params, handle=0):
        """Initialises the plugin with given arguments."""

        Logger.info("*********** Starting %s add-on version %s ***********", Config.appName, Config.version)
        self.handle = int(handle)

        super(Plugin, self).__init__(pluginName, params)
        Logger.debug("Plugin Params: %s (%s)\n"
                     "Handle:      %s\n"
                     "Name:        %s\n"
                     "Query:       %s", self.params, len(self.params),
                     self.handle, self.pluginName, params)

        # channel objects
        self.channelObject = None
        self.channelFile = ""
        self.channelCode = None

        self.contentType = "episodes"
        self.methodContainer = dict()   # : storage for the inspect.getmembers(channel) method. Improves performance

        # are we in session?
        sessionActive = SessionHelper.is_session_active(Logger.instance())

        # fetch some environment settings
        envCtrl = envcontroller.EnvController(Logger.instance())
        # self.FavouritesEnabled = envCtrl.SQLiteEnabled()
        self.FavouritesEnabled = not envCtrl.is_platform(Environments.Xbox)

        if not sessionActive:
            # do add-on start stuff
            Logger.info("Add-On start detected. Performing startup actions.")

            # print the folder structure
            envCtrl.print_retrospect_settings_and_folders(Config, AddonSettings)

            # show notification
            XbmcWrapper.show_notification(None, LanguageHelper.get_localized_string(LanguageHelper.StartingAddonId) % (
                Config.appName,), fallback=False, logger=Logger)

            # check for updates
            up = Updater(Config.UpdateUrl, Config.version, UriHandler.instance(), Logger.instance())
            if up.is_new_version_available():
                Logger.info("Found new version online: %s vs %s", up.currentVersion, up.onlineVersion)
                notification = LanguageHelper.get_localized_string(LanguageHelper.NewVersion2Id)
                notification = notification % (Config.appName, up.onlineVersion)
                XbmcWrapper.show_notification(None, lines=notification, display_time=20000)

            # check if the repository is available -> We don't need this now.
            # envCtrl.is_install_method_valid(Config)
            # envCtrl.are_addons_enabled(Config)

            # check for cache folder
            envCtrl.cache_check()

            # do some cache cleanup
            envCtrl.cache_clean_up(Config.cacheDir, Config.cacheValidTime)

        # create a session
        SessionHelper.create_session(Logger.instance())

        #===============================================================================
        #        Start the plugin version of progwindow
        #===============================================================================
        if len(self.params) == 0:

            # Show initial start if not in a session
            # now show the list
            if AddonSettings.show_categories():
                self.ShowCategories()
            else:
                self.ShowChannelList()

        #===============================================================================
        #        Start the plugin verion of the episode window
        #===============================================================================
        else:
            try:
                # Determine what stage we are in. Check that there are more than 2 Parameters
                if len(self.params) > 1 and self.keywordChannel in self.params:
                    # retrieve channel characteristics
                    self.channelFile = os.path.splitext(self.params[self.keywordChannel])[0]
                    self.channelCode = self.params[self.keywordChannelCode]
                    Logger.debug("Found Channel data in URL: channel='%s', code='%s'", self.channelFile,
                                 self.channelCode)

                    # import the channel
                    channelRegister = ChannelIndex.get_register()
                    channel = channelRegister.get_channel(self.channelFile, self.channelCode)

                    if channel is not None:
                        self.channelObject = channel
                    else:
                        Logger.critical("None or more than one channels were found, unable to continue.")
                        return

                    # init the channel as plugin
                    self.channelObject.InitChannel()
                    Logger.info("Loaded: %s", self.channelObject.channelName)

                elif self.keywordCategory in self.params:
                    # no channel needed.
                    pass

                elif self.keywordAction in self.params and (
                        self.params[self.keywordAction] == self.actionAllFavourites or
                        self.params[self.keywordAction] == self.actionRemoveFavourite):
                    # no channel needed for these favourites actions.
                    pass

                # ===============================================================================
                # Vault Actions
                # ===============================================================================
                elif self.keywordAction in self.params and \
                        self.params[self.keywordAction] in \
                        (
                            self.actionSetEncryptedValue,
                            self.actionSetEncryptionPin,
                            self.actionResetVault
                        ):
                    try:
                        # Import vault here, as it is only used here or in a channel
                        # that supports it
                        from vault import Vault

                        action = self.params[self.keywordAction]
                        if action == self.actionResetVault:
                            Vault.reset()
                            return

                        v = Vault()
                        if action == self.actionSetEncryptionPin:
                            v.change_pin()
                        elif action == self.actionSetEncryptedValue:
                            v.set_setting(self.params[self.keywordSettingId],
                                          self.params.get(self.keywordSettingName, ""),
                                          self.params.get(self.keywordSettingActionId, None))
                            # value = v.get_setting(self.params[self.keywordSettingId])
                            # Logger.Critical(value)
                    finally:
                        if self.keywordSettingTabFocus in self.params:
                            AddonSettings.show_settings(self.params[self.keywordSettingTabFocus],
                                                        self.params.get(
                                                           self.keywordSettingSettingFocus, None))
                    return

                elif self.keywordAction in self.params and \
                        self.actionPostLog in self.params[self.keywordAction]:
                    self.__SendLog()
                    return

                elif self.keywordAction in self.params and \
                        self.actionProxy in self.params[self.keywordAction]:

                    # do this here to not close the busy dialog on the SetProxy when
                    # a confirm box is shown
                    title = LanguageHelper.get_localized_string(LanguageHelper.ProxyChangeConfirmTitle)
                    content = LanguageHelper.get_localized_string(LanguageHelper.ProxyChangeConfirm)
                    if not XbmcWrapper.show_yes_no(title, content):
                        Logger.warning("Stopping proxy update due to user intervention")
                        return

                    language = self.params.get(self.keywordLanguage, None)
                    proxyId = self.params.get(self.keywordProxy, None)
                    localIp = self.params.get(self.keywordLocalIP, None)
                    self.__SetProxy(language, proxyId, localIp)
                    return

                else:
                    Logger.critical("Error determining Plugin action")
                    return

                #===============================================================================
                # See what needs to be done.
                #===============================================================================
                if self.keywordAction not in self.params:
                    Logger.critical("Action parameters missing from request. Parameters=%s", self.params)
                    return

                elif self.params[self.keywordAction] == self.actionListCategory:
                    self.ShowChannelList(self.params[self.keywordCategory])

                elif self.params[self.keywordAction] == self.actionConfigureChannel:
                    self.__ConfigureChannel(self.channelObject)

                elif self.params[self.keywordAction] == self.actionFavourites:
                    # we should show the favourites
                    self.ShowFavourites(self.channelObject)

                elif self.params[self.keywordAction] == self.actionAllFavourites:
                    self.ShowFavourites(None)

                elif self.params[self.keywordAction] == self.actionListFolder:
                    # channelName and URL is present, Parse the folder
                    self.ProcessFolderList()

                elif self.params[self.keywordAction] == self.actionPlayVideo:
                    self.PlayVideoItem()

                elif not self.params[self.keywordAction] == "":
                    self.OnActionFromContextMenu(self.params[self.keywordAction])

                else:
                    Logger.warning("Number of parameters (%s) or parameter (%s) values not implemented",
                                   len(self.params), self.params)

            except:
                Logger.critical("Error parsing for add-on", exc_info=True)

        self.__FetchTextures()
        return

    def ShowCategories(self):
        """Displays the ShowCategories that are currently available in XOT as a directory
        listing.
        """

        Logger.info("Plugin::ShowCategories")
        channelRegister = ChannelIndex.get_register()
        categories = channelRegister.get_categories()

        xbmcItems = []
        icon = os.path.join(Config.rootDir, "icon.png")
        fanart = os.path.join(Config.rootDir, "fanart.jpg")
        for category in categories:
            name = LanguageHelper.get_localized_category(category)
            xbmcItem = xbmcgui.ListItem(name, name)

            # set art
            try:
                xbmcItem.setIconImage(icon)
            except:
                # it was deprecated
                pass
            xbmcItem.setArt({'thumb': icon, 'icon': icon})
            xbmcItem.setProperty(self.propertyRetrospect, "true")
            xbmcItem.setProperty(self.propertyRetrospectCategory, "true")

            if not AddonSettings.hide_fanart():
                xbmcItem.setArt({'fanart': fanart})

            url = self._create_action_url(None, action=self.actionListCategory, category=category)
            xbmcItems.append((url, xbmcItem, True))

        # Logger.Trace(xbmcItems)
        ok = xbmcplugin.addDirectoryItems(self.handle, xbmcItems, len(xbmcItems))
        xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(self.handle, ok)
        return ok

    def ShowChannelList(self, category=None):
        """Displays the channels that are currently available in XOT as a directory
        listing.

        Keyword Arguments:
        category : String - The category to show channels for

        """

        if category:
            Logger.info("Plugin::ShowChannelList for %s", category)
        else:
            Logger.info("Plugin::ShowChannelList")
        try:
            # only display channels
            channelRegister = ChannelIndex.get_register()
            channels = channelRegister.get_channels()

            xbmcItems = []
            for channel in channels:
                if category and channel.category != category:
                    Logger.debug("Skipping %s (%s) due to category filter", channel.channelName, channel.category)
                    continue

                # Get the XBMC item
                item = channel.get_kodi_item()
                item.setProperty(self.propertyRetrospect, "true")
                item.setProperty(self.propertyRetrospectChannel, "true")
                if channel.settings:
                    item.setProperty(self.propertyRetrospectChannelSetting, "true")

                # Get the context menu items
                contextMenuItems = self.__GetContextMenuItems(channel)
                item.addContextMenuItems(contextMenuItems)
                # Get the URL for the item
                url = self._create_action_url(channel, action=self.actionListFolder)

                # Append to the list of XBMC Items
                xbmcItems.append((url, item, True))

            # Add the items
            ok = xbmcplugin.addDirectoryItems(self.handle, xbmcItems, len(xbmcItems))

            # Just let Kodi display the order we give.
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE)
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
            xbmcplugin.setContent(handle=self.handle, content=self.contentType)
            xbmcplugin.endOfDirectory(self.handle, ok)
        except:
            xbmcplugin.endOfDirectory(self.handle, False)
            Logger.critical("Error fetching channels for plugin", exc_info=True)

    def ShowFavourites(self, channel):
        """ Show the favourites

        Arguments:
        channel : Channel - The channel to show favourites for. Might be None to show all.

        Keyword Arguments:
        replaceExisting : boolean - if True it will replace the current list

        """
        Logger.debug("Plugin::ShowFavourites")

        if channel is None:
            Logger.info("Showing all favourites")
        else:
            Logger.info("Showing favourites for: %s", channel)

        f = Favourites(Config.favouriteDir)
        favs = f.list(channel)
        return self.ProcessFolderList(favs)

    def ProcessFolderList(self, favorites=None):
        """Wraps the channel.ProcessFolderList"""

        Logger.info("Plugin::ProcessFolderList Doing ProcessFolderList")
        try:
            ok = True

            selectedItem = None
            if self.keywordPickle in self.params:
                selectedItem = self._pickler.de_pickle_media_item(self.params[self.keywordPickle])

            if favorites is None:
                watcher = StopWatch("Plugin ProcessFolderList", Logger.instance())
                episodeItems = self.channelObject.ProcessFolderList(selectedItem)
                watcher.lap("Class ProcessFolderList finished")
            else:
                watcher = StopWatch("Plugin ProcessFolderList With Items", Logger.instance())
                episodeItems = favorites

            if len(episodeItems) == 0:
                Logger.warning("ProcessFolderList returned %s items", len(episodeItems))
                ok = self.__ShowEmptyInformation(episodeItems)
            else:
                Logger.debug("ProcessFolderList returned %s items", len(episodeItems))

            xbmcItems = []
            for episodeItem in episodeItems:  # type: MediaItem
                if episodeItem.thumb == "":
                    episodeItem.thumb = self.channelObject.noImage
                if episodeItem.fanart == "":
                    episodeItem.fanart = self.channelObject.fanart

                if episodeItem.type == 'folder' or episodeItem.type == 'append' or episodeItem.type == "page":
                    action = self.actionListFolder
                    folder = True
                elif episodeItem.is_playable():
                    action = self.actionPlayVideo
                    folder = False
                else:
                    Logger.critical("Plugin::ProcessFolderList: Cannot determine what to add")
                    continue

                # Get the XBMC item
                item = episodeItem.get_kodi_item()

                # Set the properties for the context menu add-on
                item.setProperty(self.propertyRetrospect, "true")
                item.setProperty(self.propertyRetrospectFolder
                                 if folder
                                 else self.propertyRetrospectVideo, "true")

                if favorites is not None:
                    item.setProperty(self.propertyRetrospectFavorite, "true")
                elif episodeItem.isCloaked:
                    item.setProperty(self.propertyRetrospectCloaked, "true")

                # Get the context menu items
                contextMenuItems = self.__GetContextMenuItems(self.channelObject, item=episodeItem)
                item.addContextMenuItems(contextMenuItems)

                # Get the action URL
                url = episodeItem.actionUrl
                if url is None:
                    url = self._create_action_url(self.channelObject, action=action, item=episodeItem)

                # Add them to the list of XBMC items
                xbmcItems.append((url, item, folder))

            watcher.lap("Kodi Items generated")
            # add items but if OK was False, keep it like that
            ok = ok and xbmcplugin.addDirectoryItems(self.handle, xbmcItems, len(xbmcItems))
            watcher.lap("items send to Kodi")

            if selectedItem is None and self.channelObject is not None:
                # mainlist item register channel.
                Statistics.register_channel_open(self.channelObject, Initializer.StartTime)
                watcher.lap("Statistics send")

            watcher.stop()

            self.__AddSortMethodToHandle(self.handle, episodeItems)

            # set the content
            xbmcplugin.setContent(handle=self.handle, content=self.contentType)

            xbmcplugin.endOfDirectory(self.handle, ok)
        except:
            Statistics.register_error(self.channelObject)
            XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                          LanguageHelper.get_localized_string(LanguageHelper.ErrorList),
                                          XbmcWrapper.Error, 4000)
            Logger.error("Plugin::Error Processing FolderList", exc_info=True)
            xbmcplugin.endOfDirectory(self.handle, False)

    # @LockWithDialog(logger=Logger.instance())  No longer needed as Kodi will do this automatically
    def PlayVideoItem(self):
        """Starts the videoitem using a playlist. """

        Logger.debug("Playing videoitem using PlayListMethod")

        item = None
        try:
            item = self._pickler.de_pickle_media_item(self.params[self.keywordPickle])

            if (item.isDrmProtected or item.isPaid) and AddonSettings.show_drm_paid_warning():
                if item.isDrmProtected:
                    Logger.debug("Showing DRM Warning message")
                    title = LanguageHelper.get_localized_string(LanguageHelper.DrmTitle)
                    message = LanguageHelper.get_localized_string(LanguageHelper.DrmText)
                    XbmcWrapper.show_dialog(title, message)
                elif item.isPaid:
                    Logger.debug("Showing Paid Warning message")
                    title = LanguageHelper.get_localized_string(LanguageHelper.PaidTitle)
                    message = LanguageHelper.get_localized_string(LanguageHelper.PaidText)
                    XbmcWrapper.show_dialog(title, message)

            if not item.complete:
                item = self.channelObject.ProcessVideoItem(item)

            # validated the updated item
            if not item.complete or not item.has_media_item_parts():
                Logger.warning("UpdateVideoItem returned an item that had item.complete = False:\n%s", item)
                Statistics.register_error(self.channelObject, item=item)

            if not item.has_media_item_parts():
                # the update failed or no items where found. Don't play
                XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                              LanguageHelper.get_localized_string(LanguageHelper.NoStreamsId),
                                              XbmcWrapper.Error)
                Logger.warning("Could not start playback due to missing streams. Item:\n%s", item)
                return

            playData = self.channelObject.PlayVideoItem(item)

            Logger.debug("Continuing playback in plugin.py")
            if not playData:
                Logger.warning("PlayVideoItem did not return valid playdata")
                return
            else:
                playList, srt = playData

            # Get the Kodi Player instance (let Kodi decide what player, see
            # http://forum.kodi.tv/showthread.php?tid=173887&pid=1516662#pid1516662)
            xbmcPlayer = xbmc.Player()

            # now we force the busy dialog to close, else the video will not play and the
            # setResolved will not work.
            LockWithDialog.close_busy_dialog()

            resolvedUrl = None
            if item.is_resolvable():
                # now set the resolve to the first URL
                startIndex = playList.getposition()  # the current location
                if startIndex < 0:
                    startIndex = 0
                Logger.info("Playing stream @ playlist index %s using setResolvedUrl method", startIndex)
                resolvedUrl = playList[startIndex].getfilename()
                xbmcplugin.setResolvedUrl(self.handle, True, playList[startIndex])
            else:
                # playlist do not use the setResolvedUrl
                Logger.info("Playing stream using Playlist method")
                xbmcPlayer.play(playList)

            # the set the subtitles
            showSubs = AddonSettings.use_subtitle()
            if srt and (srt != ""):
                Logger.info("Adding subtitle: %s and setting showSubtitles to %s", srt, showSubs)
                XbmcWrapper.wait_for_player_to_start(xbmcPlayer, logger=Logger.instance(), url=resolvedUrl)

                xbmcPlayer.setSubtitles(srt)
                xbmcPlayer.showSubtitles(showSubs)

        except:
            if item:
                Statistics.register_error(self.channelObject, item=item)
            else:
                Statistics.register_error(self.channelObject)

            XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                          LanguageHelper.get_localized_string(LanguageHelper.NoPlaybackId),
                                          XbmcWrapper.Error)
            Logger.critical("Could not playback the url", exc_info=True)

        return

    def OnActionFromContextMenu(self, action):
        """Peforms the action from a custom contextmenu

        Arguments:
        action : String - The name of the method to call

        """
        Logger.debug("Performing Custom Contextmenu command: %s", action)

        item = self._pickler.de_pickle_media_item(self.params[self.keywordPickle])
        if not item.complete:
            Logger.debug("The contextmenu action requires a completed item. Updating %s", item)
            item = self.channelObject.ProcessVideoItem(item)

            if not item.complete:
                Logger.warning("UpdateVideoItem returned an item that had item.complete = False:\n%s", item)

        # invoke
        functionString = "returnItem = self.channelObject.%s(item)" % (action,)
        Logger.debug("Calling '%s'", functionString)
        try:
            exec functionString
        except:
            Logger.error("OnActionFromContextMenu :: Cannot execute '%s'.", functionString, exc_info=True)
        return

    def __FetchTextures(self):
        texturesToRetrieve = TextureHandler.instance().number_of_missing_textures()

        if texturesToRetrieve > 0:
            w = None
            try:
                # show a blocking or background progress bar
                if texturesToRetrieve > 4:
                    w = XbmcDialogProgressWrapper(
                        "%s: %s" % (Config.appName, LanguageHelper.get_localized_string(LanguageHelper.InitChannelTitle)),
                        LanguageHelper.get_localized_string(LanguageHelper.FetchTexturesTitle),
                        # Config.TextureUrl
                    )
                else:
                    w = XbmcDialogProgressBgWrapper(
                        "%s: %s" % (Config.appName, LanguageHelper.get_localized_string(LanguageHelper.FetchTexturesTitle)),
                        Config.TextureUrl
                    )

                bytesTransfered = TextureHandler.instance().fetch_textures(w.progress_update)
                if bytesTransfered > 0:
                    Statistics.register_cdn_bytes(bytesTransfered)
            except:
                Logger.error("Error fetching textures", exc_info=True)
            finally:
                if w is not None:
                    # always close the progress bar
                    w.close()
        return

    def __ConfigureChannel(self, channelInfo):
        """ Configures a proxy for a channel

        Arguments:
        channelInfo : ChannelInfo - The channel info

        """

        if not channelInfo:
            Logger.warning("Cannot configure channel without channel info")

        Logger.info("Configuring channel: %s", channelInfo)
        AddonSettings.show_channel_settings(channelInfo)
        return

    def __AddSortMethodToHandle(self, handle, items=None):
        """ Add a sort method to the plugin output. It takes the Add-On settings into
        account. But if none of the items have a date, it is forced to sort by name.

        Arguments:
        handle : int        - The handle to add the sortmethod to
        items  : MediaItems - The items that need to be sorted

        """

        if AddonSettings.mix_folders_and_videos():
            labelSortMethod = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS
        else:
            labelSortMethod = xbmcplugin.SORT_METHOD_LABEL

        if items:
            hasDates = len(filter(lambda i: i.has_date(), items)) > 0
            if hasDates:
                Logger.debug("Sorting method: Dates")
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_DATE)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=labelSortMethod)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
                return

            hasTracks = len(filter(lambda i: i.has_track(), items)) > 0
            if hasTracks:
                Logger.debug("Sorting method: Tracks")
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_DATE)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=labelSortMethod)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
                return

        Logger.debug("Sorting method: Default (Label)")
        xbmcplugin.addSortMethod(handle=handle, sortMethod=labelSortMethod)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        return

    def __GetContextMenuItems(self, channel, item=None):
        """Retrieves the context menu items to display

        Arguments:
        channel : Channel - The channel from which to get the context menu items. The channel might be None in case of
                            some actions that do not require a channel.

        Keyword Arguments
        item           : MediaItem - The item to which the context menu belongs.
        favouritesList : Boolean   - Indication that the menu is for the favorites
        """

        contextMenuItems = []

        if item is None:
            return contextMenuItems

        # if it was a favourites list, don't add the channel methods as they might be from a different channel
        if channel is None:
            return contextMenuItems

        # now we process the other items
        possibleMethods = self.__GetMembers(channel)
        # Logger.Debug(possibleMethods)

        for menuItem in channel.contextMenuItems:
            # Logger.Debug(menuItem)
            if menuItem.itemTypes is None or item.type in menuItem.itemTypes:
                # We don't care for complete here!
                # if menuItem.completeStatus == None or menuItem.completeStatus == item.complete:

                # see if the method is available
                methodAvailable = False

                for method in possibleMethods:
                    if method == menuItem.functionName:
                        methodAvailable = True
                        # break from the method loop
                        break

                if not methodAvailable:
                    Logger.warning("No method for: %s", menuItem)
                    continue

                cmdUrl = self._create_action_url(channel, action=menuItem.functionName, item=item)
                cmd = "XBMC.RunPlugin(%s)" % (cmdUrl,)
                title = "Retro: %s" % (menuItem.label,)
                Logger.trace("Adding command: %s | %s", title, cmd)
                contextMenuItems.append((title, cmd))

        return contextMenuItems

    def __GetMembers(self, channel):
        """ Caches the inspect.getmembers(channel) method for performance
        matters

        """

        if channel.guid not in self.methodContainer:
            #self.methodContainer[channel.guid] = inspect.getmembers(channel)
            self.methodContainer[channel.guid] = dir(channel)

        return self.methodContainer[channel.guid]

    def __ShowEmptyInformation(self, items, favs=False):
        """ Adds an empty item to a list or just shows a message.
        @type favs: boolean indicating that we are dealing with favourites
        @param items: the list of items

        @rtype : boolean indicating succes or not

        """

        if self.channelObject:
            Statistics.register_error(self.channelObject)

        if favs:
            title = LanguageHelper.get_localized_string(LanguageHelper.NoFavsId)
        else:
            title = LanguageHelper.get_localized_string(LanguageHelper.ErrorNoEpisodes)

        behaviour = AddonSettings.get_empty_list_behaviour()

        Logger.debug("Showing empty info for mode (favs=%s): [%s]", favs, behaviour)
        if behaviour == "error":
            # show error
            ok = False
        elif behaviour == "dummy" and not favs:
            # We should add a dummy items, but not for favs
            emptyListItem = MediaItem("- %s -" % (title.strip("."), ), "", type='video')
            emptyListItem.icon = self.channelObject.icon
            emptyListItem.thumb = self.channelObject.noImage
            emptyListItem.fanart = self.channelObject.fanart
            emptyListItem.dontGroup = True
            emptyListItem.description = "This listing was left empty intentionally."
            emptyListItem.complete = True
            emptyListItem.fanart = self.channelObject.fanart
            # add funny stream here?
            # part = emptyListItem.create_new_empty_media_part()
            # for s, b in YouTube.get_streams_from_you_tube("", self.channelObject.proxy):
            #     part.append_media_stream(s, b)

            # if we add one, set OK to True
            ok = True
            items.append(emptyListItem)
        else:
            ok = True

        XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                      title, XbmcWrapper.Error, 2500)
        return ok

    @LockWithDialog(logger=Logger.instance())
    def __SendLog(self):
        from helpers.logsender import LogSender
        senderMode = 'pastebin'
        logSender = LogSender(Config.LogSenderApi, logger=Logger.instance(), mode=senderMode)
        try:
            title = LanguageHelper.get_localized_string(LanguageHelper.LogPostSuccessTitle)
            urlText = LanguageHelper.get_localized_string(LanguageHelper.LogPostLogUrl)
            filesToSend = [Logger.instance().logFileName, Logger.instance().logFileName.replace(".log", ".old.log")]
            if senderMode != "gist":
                pasteUrl = logSender.send_file(Config.logFileNameAddon, filesToSend[0])
            else:
                pasteUrl = logSender.send_files(Config.logFileNameAddon, filesToSend)
            XbmcWrapper.show_dialog(title, urlText % (pasteUrl,))
        except Exception, e:
            Logger.error("Error sending %s", Config.logFileNameAddon, exc_info=True)

            title = LanguageHelper.get_localized_string(LanguageHelper.LogPostErrorTitle)
            errorText = LanguageHelper.get_localized_string(LanguageHelper.LogPostError)
            error = errorText % (e.message,)
            XbmcWrapper.show_dialog(title, error.strip(": "))
        return

    @LockWithDialog(logger=Logger.instance())
    def __SetProxy(self, language, proxyId, localIP):
        """ Sets the proxy and local IP configuration for channels.

        @param language: the language for what channels to update
        @param proxyId:  the proxy index to use
        @param localIP:  the localIP index to use.
        
        If no proxyId is specified (None) then the proxyId will be determined based on language
        If no localIP is specified (None) then the localIP will be determined based on language
        
        """

        languages = AddonSettings.get_available_countries(as_country_codes=True)

        if language is not None and language not in languages:
            Logger.warning("Missing language: %s", language)
            return

        if proxyId is None:
            proxyId = languages.index(language)
        else:
            proxyId = int(proxyId)

        if localIP is None:
            localIP = languages.index(language)
        else:
            localIP = int(localIP)

        channels = ChannelIndex.get_register().get_channels()
        Logger.info("Setting proxy='%s' (%s) and localIP='%s' (%s) for country '%s'",
                    proxyId, languages[proxyId],
                    localIP, languages[localIP],
                    language)
        channelsInCountry = filter(lambda c: c.language == language or language is None, channels)
        for channel in channelsInCountry:
            Logger.debug("Setting Proxy for: %s", channel)
            AddonSettings.set_proxy_id_for_channel(channel, proxyId)
            if channel.localIPSupported:
                Logger.debug("Setting Local IP for: %s", channel)
                AddonSettings.set_local_ip_for_channel(channel, localIP)
        pass
