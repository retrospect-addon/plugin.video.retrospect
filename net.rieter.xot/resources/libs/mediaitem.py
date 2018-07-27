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

import datetime
import time
import random

import xbmc
import xbmcgui

from addonsettings import AddonSettings
from logger import Logger
from helpers.htmlentityhelper import HtmlEntityHelper
from helpers.encodinghelper import EncodingHelper


class MediaItem:
    """Main class that represent items that are retrieved in XOT. They are used
    to fill the lists and have MediaItemParts which have MediaStreams in this
    hierarchy:

    MediaItem
        +- MediaItemPart
        |    +- MediaStream
        |    +- MediaStream
        |    +- MediaStream
        +- MediaItemPart
        |    +- MediaStream
        |    +- MediaStream
        |    +- MediaStream

    """

    LabelTrackNumber = "TrackNumber"

    def __dir__(self):
        """ Required in order for the Pickler.Validate to work! """
        return ["name",
                "url",
                "actionUrl",
                "MediaItemParts",
                "description",
                "thumb",
                "fanart",
                "icon",
                "__date",
                "__timestamp",
                "type",
                "dontGroup",
                "isLive",
                "isGeoLocked",
                "isDrmProtected",
                "isPaid",
                "__infoLabels",
                "complete",
                "downloaded",
                "downloadable",
                "items",
                "HttpHeaders",
                "rating",
                "guid",
                "guidValue"]

    #noinspection PyShadowingBuiltins
    def __init__(self, title, url, type="folder"):
        """Creates a new MediaItem

        Arguments:
        title  : string - the title of the item, used for appearance in lists.
        url    : string - url that used for further information retrieval.

        Keyword Arguments:
        type   : [opt] string    - type of MediaItem (folder, video, audio).
                                   Defaults to 'folder'.
        parent : [opt] MediaItem - the parent of the current item. None is
                                   the default.

        The <url> can contain an url to a site more info about the item can be
        retrieved, for instance for a video item to retrieve the media url, or
        in case of a folder where child items can be retrieved.

        Essential is that no encoding (like UTF8) is specified in the title of
        the item. This is all taken care of when creating XBMC items in the
        different methods.

        """

        name = title.strip()

        self.name = name
        self.url = url
        self.actionUrl = None
        self.MediaItemParts = []
        self.description = ""
        self.thumb = ""                           # : The local or remote image for the thumbnail of episode
        self.fanart = ""                          # : The fanart url
        self.icon = ""                            # : low quality icon for list

        self.__date = ""                          # : value show in interface
        self.__timestamp = datetime.datetime.min  # : value for sorting, this one is set to minimum so if non is set, it's shown at the bottom

        self.type = type                          # : video, audio, folder, append, page, playlist
        self.dontGroup = False                    # : if set to True this item will not be auto grouped.
        self.isLive = False                       # : if set to True, the item will have a random QuerySting param
        self.isGeoLocked = False                  # : if set to True, the item is GeoLocked to the channels language (o)
        self.isDrmProtected = False               # : if set to True, the item is DRM protected and cannot be played (^)
        self.isPaid = False                       # : if set to True, the item is a Paid item and cannot be played (*)
        self.__infoLabels = dict()                # : Additional Kodi InfoLabels

        self.complete = False
        self.downloaded = False
        self.downloadable = False
        self.items = []
        self.HttpHeaders = dict()                 # : http headers for the item data retrieval
        self.rating = None

        # Items that are not essential for pickled
        self.isCloaked = False
        self.metaData = dict()                    # : Additional data that is for internal / routing use only

        # GUID used for identifcation of the object. Do not set from script, MD5 needed
        # to prevent UTF8 issues
        try:
            self.guid = "%s%s" % (EncodingHelper.EncodeMD5(title), EncodingHelper.EncodeMD5(url or ""))
            # self.guid = ("%s-%s" % (encodinghelper.EncodingHelper.EncodeMD5(title), url)).replace(" ", "")
        except:
            Logger.Error("Error setting GUID for title:'%s' and url:'%s'. Falling back to UUID", title, url, exc_info=True)
            self.guid = self.__GetUUID()
        self.guidValue = int("0x%s" % (self.guid,), 0)

    def AppendSingleStream(self, url, bitrate=0, subtitle=None):
        """Appends a single stream to a new MediaPart of this MediaItem

        Arguments:
        url        : string - url of the stream.

        Keyword Arguments:
        bitrate    : [opt] integer - bitrate of the stream (default = 0)
        subtitle   : [opt] string  - url of the subtitle of the mediapart

        Returns a reference to the created MediaPart

        This methods creates a new MediaPart item and adds the provided
        stream to its MediaStreams collection. The newly created MediaPart
        is then added to the MediaItem's MediaParts collection.

        """

        newPart = MediaItemPart(self.name, url, bitrate, subtitle)
        self.MediaItemParts.append(newPart)
        return newPart

    def CreateNewEmptyMediaPart(self):
        """Adds an empty MediaPart to the MediaItem

        Returns:
        The new MediaPart object (as a reference) that was appended.

        This method is used to create an empty MediaPart that can be used to
        add new stream to. The newly created MediaPart is appended to the
        MediaItem.MediaParts list.

        """

        newPart = MediaItemPart(self.name)
        self.MediaItemParts.append(newPart)
        return newPart

    def HasMediaItemParts(self):
        """Return True if there are any MediaItemParts present with streams for
        this MediaItem

        """

        for part in self.MediaItemParts:
            if len(part.MediaStreams) > 0:
                return True

        return False

    def IsPlayable(self):
        """Returns True if the item can be played in a Media Player.

        At this moment it returns True for:
        * type = 'video'
        * type = 'audio'

        """

        return self.type.lower() in ('video', 'audio', 'playlist')

    def IsResolvable(self):
        """Returns True if the item can be played directly stream (using setResolveUrl).

        At this moment it returns True for:
        * type = 'video'
        * type = 'audio'

        """

        return self.type.lower() in ('video', 'audio')

    def HasTrack(self):
        """
        @return: if the track was set
        """

        return MediaItem.LabelTrackNumber in self.__infoLabels

    def HasDate(self):
        """Returns if a date was set """

        return self.__timestamp > datetime.datetime.min

    def ClearDate(self):
        """ Resets the date (used for favourites for example). """
        self.__timestamp = datetime.datetime.min
        self.__date = ""

    # noinspection PyUnresolvedReferences
    def SetInfoLabel(self, label, value):
        # type: (str, Any) -> None
        """
        @param label: the name of the label
        @param value: the value to assign

        See http://kodi.wiki/view/InfoLabels

        """

        self.__infoLabels[label] = value

    def SetSeasonInfo(self, season, episode):
        """ Set season and episode information

        @param season:
        @param episode:
        """

        if season is None or episode is None:
            Logger.Warning("Cannot set EpisodeInfo without season and episode")
            return

        self.__infoLabels["Episode"] = int(episode)
        self.__infoLabels["Season"] = int(season)
        return

    def SetDate(self, year, month, day, hour=None, minutes=None, seconds=None, onlyIfNewer=False, text=None):
        """Sets the datetime of the MediaItem

        Arguments:
        year       : integer - the year of the datetime
        month      : integer - the month of the datetime
        day        : integer - the day of the datetime

        Keyword Arguments:
        hour       : [opt] integer - the hour of the datetime
        minutes    : [opt] integer - the minutes of the datetime
        seconds    : [opt] integer - the seconds of the datetime
        onlyIfNewer: [opt] integer - update only if the new date is more
                                     recent then the currently set one
        text       : [opt] string  - if set it will overwrite the text in the
                                     date label the datetime is also set.

        Sets the datetime of the MediaItem in the self.__date and the
        corresponding text representation of that datetime.

        <hour>, <minutes> and <seconds> can be optional and will be set to 0 in
        that case. They must all be set or none of them. Not just one or two of
        them.

        If <onlyIfNewer> is set to True, the update will only occur if the set
        datetime is newer then the currently set datetime.

        The text representation can be overwritten by setting the <text> keyword
        to a specific value. In that case the timestamp is set to the given time
        values but the text representation will be overwritten.

        If the values form an invalid datetime value, the datetime value will be
        reset to their default values.

        @return: the datetime that was set.
        """

        # dateFormat = xbmc.getRegion('dateshort')
        # correct a small bug in XBMC
        # dateFormat = dateFormat[1:].replace("D-M-", "%D-%M")
        # dateFormatLong = xbmc.getRegion('datelong')
        # timeFormat = xbmc.getRegion('time')
        # dateTimeFormat = "%s %s" % (dateFormat, timeFormat)

        try:
            dateFormat = "%Y-%m-%d"     # "%x"
            dateTimeFormat = dateFormat + " %H:%M"

            if hour is None and minutes is None and seconds is None:
                timeStamp = datetime.datetime(int(year), int(month), int(day))
                date = timeStamp.strftime(dateFormat)
            else:
                timeStamp = datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes), int(seconds))
                date = timeStamp.strftime(dateTimeFormat)

            if onlyIfNewer and self.__timestamp > timeStamp:
                return

            self.__timestamp = timeStamp
            if text is None:
                self.__date = date
            else:
                self.__date = text

        except ValueError:
            Logger.Error("Error setting date: Year=%s, Month=%s, Day=%s, Hour=%s, Minutes=%s, Seconds=%s", year, month, day, hour, minutes, seconds, exc_info=True)
            self.__timestamp = datetime.datetime.min
            self.__date = ""

        return self.__timestamp

    def GetXBMCItem(self, name=None):
        """Creates an XBMC item with the same data is the MediaItem.

        Keyword Arguments:
        name       : [opt] string  - Overwrites the name of the XBMC item.

        Returns:
        A complete XBMC ListItem

        This item is used for displaying purposes only and changes to it will
        not be passed on to the MediaItem.

        Eventually the self.UpdateXBMCItem is called to set all the parameters.
        For the mapping and Encoding of MediaItem properties to XBMCItem
        properties the __doc__ can be used.

        """

        # Update name and descriptions
        namePostFix, descriptionPostFix = self.__UpdateTitleAndDescriptionWithLimitations()

        name = self.__GetTitle(name)
        name = "%s%s" % (name, namePostFix)
        name = self.__FullDecodeText(name)

        if self.description is None:
            self.description = ''

        description = "%s%s" % (self.description.lstrip(), descriptionPostFix)
        description = self.__FullDecodeText(description)
        if description is None:
            description = ""

        # the XBMC ListItem date
        # date          : string (%d.%m.%Y / 01.01.2009) - file date
        if self.__timestamp > datetime.datetime.min:
            xbmcDate = self.__timestamp.strftime("%d.%m.%Y")
            xbmcYear = self.__timestamp.year
        else:
            xbmcDate = ""
            xbmcYear = 0

        # Get all the info labels starting with the ones set and then add the specific ones
        infoLabels = self.__infoLabels.copy()
        infoLabels["Title"] = name
        if xbmcDate:
            infoLabels["Date"] = xbmcDate
            infoLabels["Year"] = xbmcYear
        if self.type != "audio":
            # infoLabels["PlotOutline"] = description
            infoLabels["Plot"] = description
        # if descriptionPostFix:
        #     infoLabels["Tagline"] = descriptionPostFix.lstrip()

        # now create the XBMC item
        item = xbmcgui.ListItem(name or "<unknown>", self.__date)
        item.setLabel(name)
        item.setLabel2(self.__date)

        # set a flag to indicate it is a item that can be used with setResolveUrl.
        if self.IsResolvable():
            Logger.Trace("Setting IsPlayable to True")
            item.setProperty("IsPlayable", "true")

        # specific items
        Logger.Trace("Setting InfoLabels: %s", infoLabels)
        if self.type == "audio":
            item.setInfo(type="music", infoLabels=infoLabels)
        else:
            item.setInfo(type="video", infoLabels=infoLabels)

        try:
            item.setIconImage(self.icon)
        except:
            # it was deprecated
            pass

        # now set all the art to prevent duplicate calls to Kodi
        if self.fanart and not AddonSettings.HideFanart():
            item.setArt({'thumb': self.thumb, 'icon': self.icon, 'fanart': self.fanart})
        else:
            item.setArt({'thumb': self.thumb, 'icon': self.icon})

        # art = dict()
        # for l in ("thumb", "poster", "banner", "fanart", "clearart", "clearlogo", "landscape"):
        #     art[l] = self.thumb
        # item.setArt(art)

        # We never set the content resolving, Retrospect does this. And if we do, then the custom
        # headers are removed from the URL when opening the resolved URL.
        try:
            item.setContentLookup(False)
        except:
            # apparently not yet supported on this Kodi version3
            pass
        return item

    def GetXBMCPlayList(self, bitrate, updateItemUrls=False, proxy=None):
        """ Creates a XBMC Playlist containing the MediaItemParts in this MediaItem

        Keyword Arguments:
        bitrate        : integer         - The bitrate of the streams that should be in
                                           the playlist. Given in kbps

        updateItemUrls : [opt] boolean   - If specified, the Playlist items will
                                           have a path pointing to the actual stream
        proxy          : [opt] ProxyInfo - The proxy to set

        Returns:
        a XBMC Playlist for this MediaItem

        If the Bitrate keyword is omitted the the bitrate is retrieved using the
        default bitrate settings:

        """

        playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        srt = None

        playListItems = []
        if not updateItemUrls:
            # if we are not using the resolveUrl method, we need to clear the playlist and set the index
            playList.clear()
            currentIndex = 0
        else:
            # copy into a list so we can add stuff in between (we can't do that in an
            # XBMC PlayList) and then create a new playlist item
            currentIndex = playList.getposition()  # this is the location at which we are now.
            if currentIndex < 0:
                # no items where there, so we can just start at position 0
                currentIndex = 0

            Logger.Info("Updating the playlist for item at position %s and trying to preserve other playlist items", currentIndex)
            for i in range(0, len(playList)):
                Logger.Trace("Copying playList item %s out of %s", i + 1, len(playList))
                playListItems.append((playList[i].getfilename(), playList[i]))

            startList = reduce(lambda x, y: "%s\n%s" % (x, y[0]), playListItems, "Starting with Playlist Items (%s)" % (len(playListItems),))
            Logger.Debug(startList)
            playList.clear()

        logText = "Creating playlist for Bitrate: %s kbps\n%s\nSelected Streams:\n" % (bitrate, self)

        # for each MediaItemPart get the URL, starting at the current index
        index = currentIndex
        for part in self.MediaItemParts:
            if len(part.MediaStreams) == 0:
                Logger.Warning("Ignoring empty MediaPart: %s", part)
                continue

            # get the playlist item
            (stream, xbmcItem) = part.GetXBMCPlayListItem(self, bitrate, updateItemUrls=updateItemUrls)
            logText = "%s\n + %s" % (logText, stream)

            streamUrl = stream.Url
            xbmcParams = dict()
            if proxy:
                if stream.Downloaded:
                    logText = "%s\n    + Not adding proxy as the stream is already downloaded" % (logText, )
                elif proxy.Scheme.startswith("http") and not stream.Url.startswith("http"):
                    logText = "%s\n    + Not adding proxy due to scheme mismatch" % (logText, )
                elif proxy.Scheme == "dns":
                    logText = "%s\n    + Not adding DNS proxy for Kodi streams" % (logText, )
                elif not proxy.UseProxyForUrl(streamUrl):
                    logText = "%s\n    + Not adding proxy due to filter mismatch" % (logText, )
                else:
                    if AddonSettings.IsMinVersion(17):
                        # See ffmpeg proxy in https://github.com/xbmc/xbmc/commit/60b21973060488febfdc562a415e11cb23eb9764
                        xbmcItem.setProperty("proxy.host", proxy.Proxy)
                        xbmcItem.setProperty("proxy.port", str(proxy.Port))
                        xbmcItem.setProperty("proxy.type", proxy.Scheme)
                        if proxy.Username:
                            xbmcItem.setProperty("proxy.user", proxy.Username)
                        if proxy.Password:
                            xbmcItem.setProperty("proxy.password", proxy.Password)
                        logText = "%s\n    + Adding (Krypton) %s" % (logText, proxy)
                    else:
                        xbmcParams["HttpProxy"] = proxy.GetProxyAddress()
                        logText = "%s\n    + Adding (Pre-Krypton) %s" % (logText, proxy)

            # Now add the actual HTTP headers
            for k in part.HttpHeaders:
                xbmcParams[k] = HtmlEntityHelper.UrlEncode(part.HttpHeaders[k])

            if xbmcParams:
                xbmcQueryString = reduce(lambda x, y: "%s&%s=%s" %
                                                      (x, y, xbmcParams[y]), xbmcParams.keys(), "").lstrip("&")
                Logger.Debug("Adding Kodi Stream parameters: %s\n%s", xbmcParams, xbmcQueryString)
                streamUrl = "%s|%s" % (stream.Url, xbmcQueryString)

            if index == currentIndex and index < len(playListItems):
                # We need to replace the current item.
                Logger.Trace("Replacing current Kodi ListItem at Playlist index %s (of %s)", index, len(playListItems))
                playListItems[index] = (streamUrl, xbmcItem)
            else:
                # We need to add at the current index
                Logger.Trace("Inserting Kodi ListItem at Playlist index %s", index)
                playListItems.insert(index, (streamUrl, xbmcItem))

            index += 1

            # for now we just add the last subtitle, this will not work if each
            # part has it's own subtitles.
            srt = part.Subtitle

        Logger.Info(logText)

        endList = reduce(lambda x, y: "%s\n%s" % (x, y[0]), playListItems, "Ended with Playlist Items (%s)" % (len(playListItems),))
        Logger.Debug(endList)
        for playListItem in playListItems:
            playList.add(playListItem[0], playListItem[1])

        return playList, srt

    def __GetUUID(self):
        """Generates a Unique Identifier based on Time and Random Integers"""

        t = long(time.time() * 1000)
        r = long(random.random() * 100000000000000000L)
        a = random.random() * 100000000000000000L
        data = str(t) + ' ' + str(r) + ' ' + str(a)
        data = EncodingHelper.EncodeMD5(data)
        return data

    def __FullDecodeText(self, stringValue):
        """ Decodes a byte encoded string with HTML content into Unicode String

        Arguments:
        stringValue : string - The byte encoded string to decode

        Returns:
        An Unicode String with all HTML entities replaced by their UTF8 characters

        The decoding is done by first decode the string to UTF8 and then replace
        the HTML entities to their UTF8 characters.

        """

        if stringValue is None:
            return None

        if stringValue == "":
            return ""

        # then get rid of the HTML entities
        stringValue = HtmlEntityHelper.ConvertHTMLEntities(stringValue)
        return stringValue

    def __str__(self):
        """ String representation """

        value = self.name

        if self.IsPlayable():
            if len(self.MediaItemParts) > 0:
                value = "MediaItem: %s [Type=%s, Complete=%s, IsLive=%s, Date=%s, Downloadable=%s, Geo/DRM=%s/%s]" % \
                        (value, self.type, self.complete, self.isLive, self.__date,
                         self.downloadable, self.isGeoLocked, self.isDrmProtected)
                for mediaPart in self.MediaItemParts:
                    value = "%s\n%s" % (value, mediaPart)
                value = "%s" % (value,)
            else:
                value = "%s [Type=%s, Complete=%s, unknown urls, IsLive=%s, Date=%s, Downloadable=%s, Geo/DRM=%s/%s]" \
                        % (value, self.type, self.complete, self.isLive, self.__date,
                           self.downloadable, self.isGeoLocked, self.isDrmProtected)
        else:
            value = "%s [Type=%s, Url=%s, Date=%s, IsLive=%s, Geo/DRM=%s/%s]" \
                    % (value, self.type, self.url, self.__date, self.isLive, self.isGeoLocked, self.isDrmProtected)

        return value

    def __eq__(self, item):
        """ checks 2 items for Equality

        Arguments:
        item : MediaItem - The item to check for equality.

        Returns:
        the output of self.Equals(item).

        """
        return self.Equals(item)

    def __ne__(self, item):
        """ returns NOT Equal

        Arguments:
        item : MediaItem - The item to check for equality.

        Returns:
        the output of not self.Equals(item).

        """

        return not self.Equals(item)

    def __hash__(self):
        """ returns the hash value """

        return hash(self.guidValue)

    def Equals(self, item):
        """ Compares two items

        Arguments:
        item : MediaItem - The item to compare to

        Returns:
        True if the item's GUID's match.

        """

        if not item:
            return False

        # if self.name == item.name and self.guid != item.guid:
        #    Logger.Debug("Duplicate names, but different guid: %s (%s), %s (%s)", self.name, self.url, item.name, item.url)
        return self.guidValue == item.guidValue

    def __UpdateTitleAndDescriptionWithLimitations(self):
        """ Updates the title/name and description with the symbols for DRM, GEO and Paid.

        @return:            (tuple) name postfix, description postfix
        """

        geoLock = "&ordm;"  # º
        drmLock = "^"       # ^
        paid = "&ordf;"     # ª
        cloaked = "&uml;"   # ¨
        descriptionAddition = []
        titlePostfix = []

        description = ""
        title = ""

        if self.isDrmProtected:
            titlePostfix.append(drmLock)
            descriptionAddition.append("DRM Protected")
        if self.isGeoLocked:
            titlePostfix.append(geoLock)
            descriptionAddition.append("Geo Locked")
        if self.isPaid:
            titlePostfix.append(paid)
            descriptionAddition.append("Premium/Paid")
        if self.isCloaked:
            titlePostfix.append(cloaked)
            descriptionAddition.append("Cloaked")
        # actually update it
        if descriptionAddition:
            descriptionAddition = " / ".join(descriptionAddition)
            description = "\n\n%s" % (descriptionAddition, )
        if titlePostfix:
            title = " %s" % ("".join(titlePostfix), )

        return title, description

    def __GetTitle(self, name):
        """ Create the title based on the MediaItems name and type.

        @param name: (string) the name to update
        @return:     (string) an updated name

        """

        if not name:
            name = self.name

        if self.type == 'page':
            # We need to add the Page prefix to the item
            name = "Page %s" % (name,)
            Logger.Debug("GetXBMCItem :: Adding Page Prefix")

        elif self.__date != '' and not self.IsPlayable():
            # not playable items should always show date
            name = "%s (%s)" % (name, self.__date)

        folderPrefix = AddonSettings.GetFolderPrefix()
        if self.type == "folder" and not folderPrefix == "":
            name = "%s %s" % (folderPrefix, name)

        return name

    def __setstate__(self, state):
        """ Sets the current MediaItem's state based on the pickled value. However, it also adds
        newly added class variables so old items won't brake.

        @param state: a default Pickle __dict__
        """

        # creating a new MediaItem here should not cause too much performance issues, as not very many
        # will be depickled.

        m = MediaItem("", "")
        self.__dict__ = m.__dict__
        self.__dict__.update(state)

    # def __getstate__(self):
    #     return self.__dict__


class MediaItemPart:
    """Class that represents a MediaItemPart"""

    def __init__(self, name, url="", bitrate=0, subtitle=None, *args):
        """ Creates a MediaItemPart with <name> with at least one MediaStream
        instantiated with the values <url> and <bitrate>.
        The MediaPart could also have a <subtitle> or Properties in the <*args>

        Arguments:
        name : string       - the name of the MediaItemPart
        url  : string       - the URL of the stream of the MediaItemPart
        args : list[string] - a list of arguments that will be set as properties
                              when getting an XBMC Playlist Item

        Keyword Arguments:
        bitrate  : [opt] integer - The bitrate of the stream of the MediaItemPart
        subtitle : [opt] string  - The url of the subtitle of this MediaItemPart

        If a subtitles was provided, the subtitle will be downloaded and stored
        in the XOT cache. When played, the subtitle is shown. Due to the XBMC
        limitation only one subtitle can be set on a playlist, this will be
        the subtitle of the first MediaPartItem

        """

        Logger.Trace("Creating MediaItemPart '%s' for '%s'", name, url)
        self.Name = name
        self.MediaStreams = []
        self.Subtitle = ""
        self.CanStream = True
        self.HttpHeaders = dict()                   # :  HTTP Headers for stream playback

        # set a subtitle
        if subtitle is not None:
            self.Subtitle = subtitle

        if not url == "":
            # set the stream that was passed
            self.AppendMediaStream(url, bitrate)

        # set properties
        self.Properties = []
        for prop in args:
            self.AddProperty(prop[0], prop[1])
        return

    def AppendMediaStream(self, url, bitrate, *args):
        """Appends a mediastream item to the current MediaPart

        Arguments:
        url     : string  - the url of the MediaStream
        bitrate : integer - the bitrate of the MediaStream
        args    : tuple   - (name, value) for any stream property 

        Returns:
        the newly added MediaStream by reference.

        The bitrate could be set to None.

        """

        stream = MediaStream(url, bitrate, *args)
        self.MediaStreams.append(stream)
        return stream

    def AddProperty(self, name, value):
        """Adds a property to the MediaPart

        Arguments:
        name  : string - the name of the property
        value : stirng - the value of the property

        Appends a new property to the self.Properties dictionary. On playback
        these properties will be set to the XBMC PlaylistItem as properties.

        """

        Logger.Debug("Adding property: %s = %s", name, value)
        self.Properties.append((name, value))

    def GetXBMCPlayListItem(self, parent, bitrate, updateItemUrls=False):
        """Returns a XBMC List Item than can be played or added to an XBMC
        PlayList.

        Arguments:
        parent : MediaItem - the parent MediaItem
        bitrate: integer   - the bitrate for the list items

        Keyword Arguments:
        quality        : [opt] integer - The quality of the requested XBMC
                                         PlayListItem streams.
        updateItemUrls : [opt] boolean - If set, the xbmc items will have a path
                                         that corresponds with the actual stream.

        Returns:
        A tuple with (stream url, XBMC PlayListItem). The XBMC PlayListItem
        can be used to add to a XBMC Playlist. The stream url can be used
        to set as the stream for the PlayListItem using xbmc.PlayList.add()

        If quality is not specified the quality is retrieved from the add-on
        settings.

        """

        if self.Name:
            Logger.Debug("Creating XBMC ListItem '%s'", self.Name)
            item = parent.GetXBMCItem(name=self.Name)
        else:
            Logger.Debug("Creating XBMC ListItem '%s'", parent.name)
            item = parent.GetXBMCItem()

        if not bitrate:
            raise ValueError("Bitrate not specified")

        for prop in self.Properties:
            Logger.Trace("Adding property: %s", prop)
            item.setProperty(prop[0], prop[1])

        # now find the correct quality stream and set the properties if there are any
        stream = self.GetMediaStreamForBitrate(bitrate)
        for prop in stream.Properties:
            Logger.Trace("Adding stream property: %s", prop)
            item.setProperty(prop[0], prop[1])

        if updateItemUrls:
            Logger.Info("Updating xbmc playlist-item path: %s", stream.Url)
            item.setProperty("path", stream.Url)

        return stream, item

    def GetMediaStreamForBitrate(self, bitrate):
        """Returns the MediaStream for the requested bitrate.

        Arguments:
        bitrate : integer - The bitrate of the stream in kbps

        Returns:
        The url of the stream with the requested bitrate.

        If bitrate is not specified the highest bitrate stream will be used.

        """

        # order the items by bitrate
        self.MediaStreams.sort()
        bestStream = None
        bestDistance = None

        for stream in self.MediaStreams:
            if stream.Bitrate is None:
                # no bitrate set, see if others are available
                continue

            # this is the bitrate-as-max-limit-method
            if stream.Bitrate > bitrate:
                # if the bitrate is higher, continue for more
                continue
            # if commented ^^ , we get the closest-match-method

            # determine the distance till the bitrate
            distance = abs(bitrate - stream.Bitrate)

            if bestDistance is None or bestDistance > distance:
                # this stream is better, so store it.
                bestDistance = distance
                bestStream = stream

        if bestStream is None:
            # no match, take the lowest bitrate
            return self.MediaStreams[0]

        return bestStream

    def __cmp__(self, other):
        """ Compares 2 items based on their appearance order

        Arguments:
        other : MediaItemPart - The part to compare to

        Returns:
         * -1 : If the item is lower than the current one
         *  0 : If the item is order is equal
         *  1 : If the item is higher than the current one

        The comparison is done base on the Name only.

        """
        if other is None:
            return -1

        # compare names
        return cmp(self.Name, other.Name)

    def __eq__(self, other):
        """ checks 2 items for Equality

        Arguments:
        item : MediaItemPart - The part to check for equality.

        Returns:
        the True if the items are equal. Equality takes into consideration:
         * Name
         * Subtitle
         * Length of the MediaStreams
         * Compares all the MediaStreams in the slef.MediaStreams

        """

        if other is None:
            return False

        if not other.Name == self.Name:
            return False

        if not other.Subtitle == self.Subtitle:
            return False

        # now check the strea
        if not len(self.MediaStreams) == len(other.MediaStreams):
            return False

        for i in range(0, len(self.MediaStreams)):
            if not self.MediaStreams[i] == other.MediaStreams[i]:
                return False

        # if we reach this point they are equal.
        return True

    def __str__(self):
        """ String representation """

        text = "MediaPart: %s [CanStream=%s, HttpHeaders=%s]" % (self.Name, self.CanStream, self.HttpHeaders)

        if self.Subtitle != "":
            text = "%s\n + Subtitle: %s" % (text, self.Subtitle)

        for prop in self.Properties:
            text = "%s\n + Property: %s=%s" % (text, prop[0], prop[1])

        for stream in self.MediaStreams:
            text = "%s\n + %s" % (text, stream)
        return text


class MediaStream:
    """Class that represents a Mediastream with <url> and a specific <bitrate>"""

    def __init__(self, url, bitrate=0, *args):
        """Initialises a new MediaStream

        Arguments:
        url  : string - the URL of the stream
        args : tuple  - (name, value) for any stream property

        Keyworkd Arguments:
        bitrate : [opt] integer - the bitrate of the stream (defaults to 0)

        """

        Logger.Trace("Creating MediaStream '%s' with bitrate '%s'", url, bitrate)
        self.Url = url
        self.Bitrate = int(bitrate)
        self.Downloaded = False
        self.Properties = []

        for prop in args:
            self.AddProperty(prop[0], prop[1])
        return

    def AddProperty(self, name, value):
        """Adds a property to the MediaStream

        Arguments:
        name  : string - the name of the property
        value : stirng - the value of the property

        Appends a new property to the self.Properties dictionary. On playback
        these properties will be set to the XBMC PlaylistItem as properties.

        Example:    
        strm.AddProperty("inputstreamaddon", "inputstream.adaptive")
        strm.AddProperty("inputstream.adaptive.manifest_type", "mpd")
        
        """

        Logger.Debug("Adding stream property: %s = %s", name, value)
        self.Properties.append((name, value))

    def __cmp__(self, other):
        """Compares two MediaStream based on the bitrate

        Arguments:
        other : MediaStream - The stream to compare to

        Returns:
         * -1 : If the item is lower than the current one
         *  0 : If the item is order is equal
         *  1 : If the item is higher than the current one

        The comparison is done base on the bitrate only.

        """

        if other is None:
            return -1

        return cmp(self.Bitrate, other.Bitrate)

    def __eq__(self, other):
        """Checks 2 items for Equality

        Arguments:
        other : MediaStream - The stream to check for equality.

        Returns:
        the True if the items are equal. Equality takes into consideration:
         * The url of the MediaStream

        """

        # also check for URL
        if other is None:
            return False

        return self.Url == other.Url

    def __str__(self):
        """String representation"""

        text = "MediaStream: %s [bitrate=%s, downloaded=%s]" % (self.Url, self.Bitrate, self.Downloaded)
        for prop in self.Properties:
            text = "%s\n    + Property: %s=%s" % (text, prop[0], prop[1])

        return text
