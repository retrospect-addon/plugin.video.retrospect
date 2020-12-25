# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import os

import xbmcvfs

from resources.lib.helpers import kodivfs
from resources.lib.logger import Logger
from resources.lib.pickler import Pickler
from resources.lib.regexer import Regexer


class Favourites:
    def __init__(self, path):
        """ Initializes a Favourites class that can be use to show, add and delete favourites.

        :param str path: The path to store the favourites file

        """

        self.__filePattern = "%s-%s.xotfav"
        self.__pickler = Pickler()

        self.FavouriteFolder = path

    def add(self, channel, item, action_url):
        """ Adds a favourite for a specific channel.

        :param channel:       The channel
        :param item:          The mediaitem
        :param str action_url:     The mediaitem's actionUrl

        """

        Logger.debug("Adding item %s\nfor channel %s\n%s", item, channel, action_url)
        file_name = self.__filePattern % (channel.guid, item.guid)
        file_path = os.path.join(self.FavouriteFolder, file_name)
        pickle = self.__pickler.pickle_media_item(item)

        # Just double check for folder existence
        if not xbmcvfs.exists(self.FavouriteFolder):
            xbmcvfs.mkdirs(self.FavouriteFolder)

        # replacing to pickle in the actionUrl to save space
        action_url = self.__remove_pickle(action_url)

        try:
            with kodivfs.File(file_path, "w") as file_handle:
                fav_data = "%s\n%s\n%s\n%s" % (channel.channelName, item.name, action_url, pickle)
                file_handle.write(fav_data.encode('utf-8'))
        except:
            Logger.error("Error saving favourite", exc_info=True)
            raise
        return

    # noinspection PyUnusedLocal
    def remove(self, item):
        """ Adds a favourite for a specific channel

        :param item:          The mediaitem

        """

        path_mask = os.path.join(self.FavouriteFolder, "*-%s.xotfav" % (item.guid, ))

        Logger.debug("Removing favourites for mask: %s", path_mask)
        for fav in glob.glob(path_mask):
            Logger.trace("Removing item %s\nFileName: %s", item, fav)
            xbmcvfs.delete(fav)
        return

    def list(self, channel=None):
        """ Lists favourites. If a channel was specified it will limit them to that.

        :param channel: The channel to limit the favourites to.

        :return: A list of tupples (action_url, pickle)
        :rtype: list

        """

        favs = []

        if channel:
            path_mask = os.path.join(self.FavouriteFolder, "%s-*.xotfav" % (channel.guid,))
        else:
            path_mask = os.path.join(self.FavouriteFolder, "*.xotfav")

        Logger.debug("Fetching favourites for mask: %s", path_mask)
        for fav in glob.glob(path_mask):
            Logger.trace("Fetching %s", fav)

            try:
                with kodivfs.File(fav) as file_handle:
                    file_data = file_handle.read()
                    file_lines = [line.strip() for line in file_data.splitlines()]

                    channel_name = file_lines[0]
                    name = file_lines[1]
                    action_url = file_lines[2]
                    if "pickle=" in action_url and "pickle=%s" not in action_url:
                        # see issue https://github.com/retrospect-addon/plugin.video.retrospect/issues/1037
                        Logger.debug("Found favourite with full pickle, removing the pickle as we should use the one from the file.")
                        action_url = self.__remove_pickle(action_url)

                    pickle = file_lines[3]
            except:
                Logger.error("Error fetching favourite", exc_info=True)
                raise

            if channel_name == "" or name == "" or action_url == "" or pickle == "":
                Logger.error("Apparently the file had too few lines, corrupt Favourite, removing it:\n"
                             "Pickle: %s\n"
                             "Channel: %s\n"
                             "Item: %s\n"
                             "ActionUrl: %s\n"
                             "Pickle: %s",
                             fav, channel_name, name, action_url, pickle)

                # Remove the invalid favourite
                xbmcvfs.delete(fav)
                continue

            Logger.debug("Found favourite: %s", name)
            try:
                item = self.__pickler.de_pickle_media_item(pickle)
            except Exception:
                Logger.error("Cannot depickle item.", exc_info=True)
                # Let's not remove them for now. Just ignore.
                # os.remove(fav)
                continue

            validation_error = self.__pickler.validate(item, logger=Logger.instance())
            if validation_error:
                Logger.error("Invalid Pickled Item: %s\nRemoving favourite: %s", validation_error, fav)

                # Remove the invalid favourite
                xbmcvfs.delete(fav)
                continue

            # clean up the .: from titles
            if ".:" in item.name and ":." in item.name:
                item.name = item.name.strip(".:\0\b ")

            # add the channel name
            if channel is None:
                item.name = "%s [%s]" % (item.name, channel_name)

            item.clear_date()

            item.actionUrl = action_url % (pickle,)
            favs.append(item)
        return favs

    def __remove_pickle(self, action_url):
        pickle = Regexer.do_regex("pickle=([^&]+)", action_url)
        if not pickle:
            return action_url

        return action_url.replace(pickle[0], "%s")
