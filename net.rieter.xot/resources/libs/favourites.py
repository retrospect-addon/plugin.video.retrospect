#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import glob
import os

from logger import Logger
from pickler import Pickler


class Favourites:
    def __init__(self, path):
        """ Initializes a Favourites class that can be use to show, add and delete favourites.

        @param path: The path to store the favourites file

        """

        self.__filePattern = "%s-%s.xotfav"

        self.FavouriteFolder = path

    def Add(self, channel, item, actionUrl):
        """ Adds a favourite for a specific channel.

        @param channel:       The channel
        @param item:          The mediaitem
        @param actionUrl:     The mediaitem's actionUrl

        Returns nothing
        """

        Logger.Debug("Adding item %s\nfor channel %s\n%s", item, channel, actionUrl)
        fileName = self.__filePattern % (channel.guid, item.guid)
        filePath = os.path.join(self.FavouriteFolder, fileName)
        pickle = Pickler.PickleMediaItem(item)

        # Just double check for folder existence
        if not os.path.isdir(self.FavouriteFolder):
            os.makedirs(self.FavouriteFolder)

        # replacing to pickle in the actionUrl to save space
        actionUrl = actionUrl.replace(pickle, "%s")
        fileHandle = None

        try:
            fileHandle = open(filePath, mode='w')
            fileHandle.write("%s\n%s\n%s\n%s" % (channel.channelName, item.name, actionUrl, pickle))
            fileHandle.close()
        except:
            Logger.Error("Error saving favourite", exc_info=True)
            if fileHandle and not fileHandle.closed:
                fileHandle.close()
            raise
        return

    # noinspection PyUnusedLocal
    def Remove(self, item):
        """ Adds a favourite for a specific channel

        @param item:          The mediaitem

        Returns nothing

        """

        pathMask = os.path.join(self.FavouriteFolder, "*-%s.xotfav" % (item.guid, ))

        Logger.Debug("Removing favourites for mask: %s", pathMask)
        for fav in glob.glob(pathMask):
            Logger.Trace("Removing item %s\nFileName: %s", item, fav)
            os.remove(fav)
        return

    def List(self, channel=None):
        """ Lists favourites. If a channel was specified it will limit them to that.

        @param channel: The channel to limit the favourites to.


        Returns a list of tupples (actionUrl, pickle)

        """

        favs = []

        if channel:
            pathMask = os.path.join(self.FavouriteFolder, "%s-*.xotfav" % (channel.guid,))
        else:
            pathMask = os.path.join(self.FavouriteFolder, "*.xotfav")

        Logger.Debug("Fetching favourites for mask: %s", pathMask)
        for fav in glob.glob(pathMask):
            Logger.Trace("Fetching %s", fav)

            fileHandle = None
            try:
                fileHandle = open(fav)
                channelName = fileHandle.readline().rstrip()
                name = fileHandle.readline().rstrip()
                actionUrl = fileHandle.readline().rstrip()
                pickle = fileHandle.readline()
                fileHandle.close()
            except:
                Logger.Error("Error fetching favourite", exc_info=True)
                if fileHandle and not fileHandle.closed:
                    fileHandle.close()
                raise

            if channelName == "" or name == "" or actionUrl == "" or pickle == "":
                Logger.Error("Apparently the file had too few lines, corrupt Favourite, removing it:\n"
                             "Pickle: %s\n"
                             "Channel: %s\n"
                             "Item: %s\n"
                             "ActionUrl: %s\n"
                             "Pickle: %s",
                             fav, channelName, name, actionUrl, pickle)

                # Remove the invalid favourite
                os.remove(fav)
                continue

            Logger.Debug("Found favourite: %s", name)
            item = Pickler.DePickleMediaItem(pickle)
            validationError = Pickler.Validate(item, logger=Logger.Instance())
            if validationError:
                Logger.Error("Invalid Pickled Item: %s\nRemoving favourite: %s", validationError, fav)

                # Remove the invalid favourite
                os.remove(fav)
                continue

            # add the channel name
            if channel is None:
                item.name = "%s [%s]" % (item.name, channelName)

            item.ClearDate()

            item.actionUrl = actionUrl % (pickle,)
            favs.append(item)
        return favs
