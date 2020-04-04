# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import xbmcplugin
import xbmc

from resources.lib import envcontroller
from resources.lib.logger import Logger
from resources.lib.addonsettings import AddonSettings
from resources.lib.locker import LockWithDialog
from resources.lib.retroconfig import Config
from resources.lib.xbmcwrapper import XbmcWrapper, XbmcDialogProgressWrapper, XbmcDialogProgressBgWrapper
from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.channelimporter import ChannelIndex
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.sessionhelper import SessionHelper
from resources.lib.textures import TextureHandler
from resources.lib.paramparser import ParameterParser
from resources.lib.urihandler import UriHandler
from resources.lib.actions import keyword


class Plugin(ParameterParser):
    """ Main Plugin Class

    This class makes it possible to access all the XOT channels as a Kodi Add-on
    instead of a script.

    """

    def __init__(self, addon_name, params, handle=0):  # NOSONAR complexity
        """ Initialises the plugin with given arguments.

        :param str addon_name:      The add-on name.
        :param str params:          The input parameters from the query string.
        :param int|str handle:      The Kodi directory handle.

        """

        Logger.info("******** Starting %s add-on version %s/repo *********", Config.appName, Config.version)
        # noinspection PyTypeChecker

        super(Plugin, self).__init__(addon_name, handle, params)
        Logger.debug(self)

        # Container Properties
        self.propertyRetrospect = "Retrospect"
        self.propertyRetrospectChannel = "RetrospectChannel"
        self.propertyRetrospectChannelSetting = "RetrospectChannelSettings"
        self.propertyRetrospectFolder = "RetrospectFolder"
        self.propertyRetrospectVideo = "RetrospectVideo"
        self.propertyRetrospectCloaked = "RetrospectCloaked"
        self.propertyRetrospectCategory = "RetrospectCategory"
        self.propertyRetrospectFavorite = "RetrospectFavorite"
        self.propertyRetrospectAdaptive = "RetrospectAdaptive"

        # channel objects
        self.channelObject = None
        self.channelFile = ""
        self.channelCode = None

        self.methodContainer = dict()   # : storage for the inspect.getmembers(channel) method. Improves performance

        # are we in session?
        session_active = SessionHelper.is_session_active(Logger.instance())

        # fetch some environment settings
        env_ctrl = envcontroller.EnvController(Logger.instance())

        if not session_active:
            # do add-on start stuff
            Logger.info("Add-On start detected. Performing startup actions.")

            # print the folder structure
            env_ctrl.print_retrospect_settings_and_folders(Config, AddonSettings)

            # show notification
            XbmcWrapper.show_notification(None, LanguageHelper.get_localized_string(LanguageHelper.StartingAddonId) % (
                Config.appName,), fallback=False, logger=Logger)

            # check for updates. Using local import for performance
            from resources.lib.updater import Updater
            up = Updater(Config.updateUrl, Config.version,
                         UriHandler.instance(), Logger.instance(),
                         AddonSettings.get_release_track())

            if up.is_new_version_available():
                Logger.info("Found new version online: %s vs %s", up.currentVersion, up.onlineVersion)
                notification = LanguageHelper.get_localized_string(LanguageHelper.NewVersion2Id)
                notification = notification % (Config.appName, up.onlineVersion)
                XbmcWrapper.show_notification(None, lines=notification, display_time=20000)

            # check for cache folder
            env_ctrl.cache_check()

            # do some cache cleanup
            env_ctrl.cache_clean_up(Config.cacheDir, Config.cacheValidTime)

            # empty picklestore
            self.pickler.purge_store(Config.addonId)

        # create a session
        SessionHelper.create_session(Logger.instance())

        #===============================================================================
        #        Start the plugin version of progwindow
        #===============================================================================
        addon_action = None
        if len(self.params) == 0:
            # Show initial start if not in a session now show the list
            if AddonSettings.show_categories():
                from resources.lib.actions.categoryaction import CategoryAction
                addon_action = CategoryAction(self)
            else:
                from resources.lib.actions.channellistaction import ChannelListAction
                addon_action = ChannelListAction(self)

        #===============================================================================
        #        Start the plugin verion of the episode window
        #===============================================================================
        else:
            # Determine what stage we are in. Check that there are more than 2 Parameters
            if len(self.params) > 1 and keyword.CHANNEL in self.params:
                # retrieve channel characteristics
                self.channelFile = os.path.splitext(self.params[keyword.CHANNEL])[0]
                self.channelCode = self.params[keyword.CHANNEL_CODE]
                Logger.debug("Found Channel data in URL: channel='%s', code='%s'", self.channelFile,
                             self.channelCode)

                # import the channel
                channel_register = ChannelIndex.get_register()
                channel = channel_register.get_channel(self.channelFile, self.channelCode)

                if channel is not None:
                    self.channelObject = channel
                else:
                    Logger.critical("None or more than one channels were found, unable to continue.")
                    return

                # init the channel as plugin
                self.channelObject.init_channel()
                Logger.info("Loaded: %s", self.channelObject.channelName)

            elif keyword.CATEGORY in self.params \
                    or keyword.ACTION in self.params and (
                        self.params[keyword.ACTION] == self.actionAllFavourites or
                        self.params[keyword.ACTION] == self.actionRemoveFavourite):
                # no channel needed for these favourites actions.
                pass

            # ===============================================================================
            # Vault Actions
            # ===============================================================================
            elif keyword.ACTION in self.params and \
                    self.params[keyword.ACTION] in \
                    (
                        self.actionSetEncryptedValue,
                        self.actionSetEncryptionPin,
                        self.actionResetVault
                    ):
                action = self.params[keyword.ACTION]

                from resources.lib.actions.vaultaction import VaultAction
                addon_action = VaultAction(self, action)
                addon_action.execute()
                return

            elif keyword.ACTION in self.params and \
                    self.actionPostLog in self.params[keyword.ACTION]:
                from resources.lib.actions.logaction import LogAction
                addon_action = LogAction(self)
                addon_action.execute()
                return

            else:
                Logger.critical("Error determining Plugin action")
                return

            #===============================================================================
            # See what needs to be done.
            #===============================================================================
            if keyword.ACTION not in self.params:
                Logger.critical("Action parameters missing from request. Parameters=%s", self.params)
                return

            elif self.params[keyword.ACTION] == self.actionListCategory:
                from resources.lib.actions.channellistaction import ChannelListAction
                addon_action = ChannelListAction(self, self.params[keyword.CATEGORY])

            elif self.params[keyword.ACTION] == self.actionConfigureChannel:
                from resources.lib.actions.configurechannelaction import ConfigureChannelAction
                addon_action = ConfigureChannelAction(self, self.channelObject)

            elif self.params[keyword.ACTION] == self.actionFavourites:
                # we should show the favourites
                from resources.lib.actions.favouritesaction import ShowFavouritesAction
                addon_action = ShowFavouritesAction(self, self.channelObject)

            elif self.params[keyword.ACTION] == self.actionAllFavourites:
                from resources.lib.actions.favouritesaction import ShowFavouritesAction
                addon_action = ShowFavouritesAction(self, None)

            elif self.params[keyword.ACTION] == self.actionListFolder:
                # channelName and URL is present, Parse the folder
                from resources.lib.actions.folderaction import FolderAction
                addon_action = FolderAction(self, self.channelObject, self.media_item)

            elif self.params[keyword.ACTION] == self.actionPlayVideo:
                self.play_video_item()

            elif not self.params[keyword.ACTION] == "":
                self.on_action_from_context_menu(self.params[keyword.ACTION])

            else:
                Logger.warning("Number of parameters (%s) or parameter (%s) values not implemented",
                               len(self.params), self.params)

        # Execute the action
        if addon_action is not None:
            addon_action.execute()

        self.__fetch_textures()
        return

    # @LockWithDialog(logger=Logger.instance())  No longer needed as Kodi will do this automatically
    def play_video_item(self):
        """ Starts the videoitem using a playlist. """

        from resources.lib import player

        Logger.debug("Playing videoitem using PlayListMethod")

        try:
            media_item = self.media_item

            if not media_item.complete:
                media_item = self.channelObject.process_video_item(media_item)

            # Any warning to show
            self.__show_warnings(media_item)

            # validated the updated media_item
            if not media_item.complete or not media_item.has_media_item_parts():
                Logger.warning("process_video_item returned an MediaItem that had MediaItem.complete = False:\n%s", media_item)

            if not media_item.has_media_item_parts():
                # the update failed or no items where found. Don't play
                XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                              LanguageHelper.get_localized_string(LanguageHelper.NoStreamsId),
                                              XbmcWrapper.Error)
                Logger.warning("Could not start playback due to missing streams. Item:\n%s", media_item)
                xbmcplugin.endOfDirectory(self.handle, False)
                return

            kodi_items = media_item.get_kodi_play_list_data(
                AddonSettings.get_max_stream_bitrate(self.channelObject),
                self.channelObject.proxy
            )

            Logger.debug("Continuing playback in plugin.py")
            if not bool(kodi_items):
                Logger.warning("play_video_item did not return valid playdata")
                xbmcplugin.endOfDirectory(self.handle, False)
                return

            # Now we force the busy dialog to close, else the video will not play and the
            # setResolved will not work.
            LockWithDialog.close_busy_dialog()

            # Append it to the Kodi playlist in a smart way.
            start_url = self.__append_kodi_play_list(kodi_items)

            # Set the mode (if the InputStream Adaptive add-on is used, we also need to set it)
            show_subs = AddonSettings.show_subtitles()

            # TODO: Apparently if we use the InputStream Adaptive, using the setSubtitles() causes sync issues.
            available_subs = [p.Subtitle for p in media_item.MediaItemParts]

            # Get the Kodi Player instance (let Kodi decide what player, see
            # http://forum.kodi.tv/showthread.php?tid=173887&pid=1516662#pid1516662)
            kodi_player = player.Player(show_subs=show_subs, subs=available_subs)
            kodi_player.waitForPlayBack(url=start_url, time_out=10)

            xbmcplugin.endOfDirectory(self.handle, True)
        except:
            XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                          LanguageHelper.get_localized_string(LanguageHelper.NoPlaybackId),
                                          XbmcWrapper.Error)
            Logger.critical("Could not playback the url", exc_info=True)

            # We need to single Kodi that it failed and it should not wait longer. Either using a
            # `raise` or with `xbmcplugin.endOfDirectory`. Doing the latter for now although we are
            # not really playing.
            xbmcplugin.endOfDirectory(self.handle, False)

        return

    def on_action_from_context_menu(self, action):
        """Peforms the action from a custom contextmenu

        Arguments:
        action : String - The name of the method to call

        """
        Logger.debug("Performing Custom Contextmenu command: %s", action)

        item = self.media_item
        if not item.complete:
            Logger.debug("The contextmenu action requires a completed item. Updating %s", item)
            item = self.channelObject.process_video_item(item)

            if not item.complete:
                Logger.warning("update_video_item returned an item that had item.complete = False:\n%s", item)

        # invoke
        function_string = "returnItem = self.channelObject.%s(item)" % (action,)
        Logger.debug("Calling '%s'", function_string)
        try:
            # noinspection PyRedundantParentheses
            exec(function_string)  # NOSONAR We just need this here.
        except:
            Logger.error("on_action_from_context_menu :: Cannot execute '%s'.", function_string, exc_info=True)
        return

    def __fetch_textures(self):
        textures_to_retrieve = TextureHandler.instance().number_of_missing_textures()

        if textures_to_retrieve > 0:
            w = None
            try:
                # show a blocking or background progress bar
                if textures_to_retrieve > 4:
                    w = XbmcDialogProgressWrapper(
                        "%s: %s" % (Config.appName, LanguageHelper.get_localized_string(LanguageHelper.InitChannelTitle)),
                        LanguageHelper.get_localized_string(LanguageHelper.FetchTexturesTitle)
                    )
                else:
                    w = XbmcDialogProgressBgWrapper(
                        "%s: %s" % (Config.appName, LanguageHelper.get_localized_string(LanguageHelper.FetchTexturesTitle)),
                        Config.textureUrl
                    )

                TextureHandler.instance().fetch_textures(w.progress_update)
            except:
                Logger.error("Error fetching textures", exc_info=True)
            finally:
                if w is not None:
                    # always close the progress bar
                    w.close()
        return

    def __show_warnings(self, media_item):
        """ Show playback warnings for this MediaItem

        :param MediaItem media_item: The current MediaItem that will be played.

        """

        if (media_item.isDrmProtected or media_item.isPaid) and AddonSettings.show_drm_paid_warning():
            if media_item.isDrmProtected:
                Logger.debug("Showing DRM Warning message")
                title = LanguageHelper.get_localized_string(LanguageHelper.DrmTitle)
                message = LanguageHelper.get_localized_string(LanguageHelper.DrmText)
                XbmcWrapper.show_dialog(title, message)
            elif media_item.isPaid:
                Logger.debug("Showing Paid Warning message")
                title = LanguageHelper.get_localized_string(LanguageHelper.PaidTitle)
                message = LanguageHelper.get_localized_string(LanguageHelper.PaidText)
                XbmcWrapper.show_dialog(title, message)

    def __append_kodi_play_list(self, kodi_items):
        # Get the current playlist
        play_list = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        play_list_size = play_list.size()
        start_index = play_list.getposition()  # the current location
        if start_index < 0:
            start_index = 0
        Logger.debug("Current playlist size and position: %s @ %s", play_list_size, start_index)

        current_play_list_items = [play_list[i] for i in range(0, len(play_list))]
        play_list.clear()
        for i in range(0, start_index):
            Logger.debug("Adding existing PlayList item")
            play_list.add(current_play_list_items[i].getfilename(), current_play_list_items[i])

        # The current item to play (we need to store te starting url for later)
        Logger.debug("Adding Main PlayList item")
        kodi_item, start_url = kodi_items.pop(0)
        play_list.add(start_url, kodi_item, start_index)
        xbmcplugin.setResolvedUrl(self.handle, True, kodi_item)

        # now we add the rest of the Kodi ListItems for the other parts
        for kodi_item, stream_url in kodi_items:
            Logger.debug("Adding Additional PlayList item")
            play_list.add(stream_url, kodi_item, start_index)
            xbmcplugin.setResolvedUrl(self.handle, True, kodi_item)

        # add the remaining items
        for i in range(start_index + 1, len(current_play_list_items)):
            Logger.debug("Adding existing PlayList item")
            play_list.add(current_play_list_items[i].getfilename(), current_play_list_items[i])

        return start_url
