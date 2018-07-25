#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================
import time
import os

#===============================================================================
# Import the default modules
#===============================================================================
import xbmcgui
import xbmc

from config import Config
from locker import LockWithDialog


class XbmcDialogProgressWrapper:
    def __init__(self, title, line1, line2=""):
        """ Initialises a XbmcDialogProgressWrapper that wraps an XBMC DialogProgress object.

        @param title: Title of it
        @param line1: The first line to show
        @param line2: The second line to show

        """

        self.Title = title
        self.Line1 = line1
        self.Line2 = line2
        self.progressBarDialog = xbmcgui.DialogProgress()
        self.progressBarDialog.create(title, line1)

    def __call__(self, *args):
        return self.ProgressUpdate(*args)

    # noinspection PyUnusedLocal
    def ProgressUpdate(self, retrievedSize, totalSize, perc, completed, status):
        """ Updates the dialog

        @param retrievedSize:   int    - the bytes received
        @param totalSize:       int    - the total bytes to receive
        @param perc:            int    - the percentage done
        @param completed:       bool   - are we done?
        @param status:          string - what is the status?

        @return: True if canceled.

        NOTE: this method signature is the same as the XbmcDialogProgressBgWrapper.Update

        """

        if not completed:
            self.progressBarDialog.update(int(perc), self.Line1, self.Line2, status)
        else:
            self.progressBarDialog.close()

        return self.progressBarDialog.iscanceled()

    def Close(self):
        """ Close the progress dialog. """
        self.progressBarDialog.close()


class XbmcDialogProgressBgWrapper:
    def __init__(self, heading, message):
        """ Initialises a XbmcDialogProgressWrapper that wraps an XBMC DialogProgress object.

        @param heading: Title of it
        @param message: The first line to show

        """

        self.Heading = heading
        self.Message = message
        self.progressBarDialog = xbmcgui.DialogProgressBG()
        self.progressBarDialog.create(heading, message)
        # it does not reset?
        self.progressBarDialog.update(percent=1, heading=heading, message=message)

    def __call__(self, *args):
        return self.ProgressUpdate(*args)

    # noinspection PyUnusedLocal
    def ProgressUpdate(self, retrievedSize, totalSize, perc, completed, status):
        """ Updates the dialog

        @param retrievedSize:   int    - the bytes received
        @param totalSize:       int    - the total bytes to receive
        @param perc:            int    - the percentage done
        @param completed:       bool   - are we done?
        @param status:          string - what is the status?

        @return: True if canceled.

        NOTE: this method signature is the same as the XbmcDialogProgressWrapper.Update

        """

        if not completed:
            self.progressBarDialog.update(percent=int(perc), heading=self.Heading, message=status)
        else:
            self.progressBarDialog.close()

        # no cancel
        return False

    def Close(self):
        """ Close the progress dialog. """
        self.progressBarDialog.close()


class XbmcWrapper:
    """ Wraps some basic XBMC methods """

    Error = "error"
    Warning = "warning"
    Info = "info"

    def __init__(self):
        pass

    @staticmethod
    def ShowKeyBoard(default="", heading="", hidden=False):
        """ Displays the XBMC keyboard.

        @type default: string
        @type heading: string
        @type hidden: boolean
        @return: returns the text that was entered or None if cancelled.

        """

        # let's just unlock the interface, in case it's locked.
        LockWithDialog.CloseBusyDialog()

        keyboard = xbmc.Keyboard(default, heading, hidden)
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return None

        return keyboard.getText()

    @staticmethod
    def ShowNotification(title, lines, notificationType=Info, displayTime=1500, fallback=True, logger=None):
        """ Shows an XBMC Notification

        Arguments:
        titel   : String - The title to show
        content : String - The content to show

        Keyword Arguments:
        notificationType  : String - The type of notification: info, error, warning
        displayTime       : int    - Time to display the notification. Defaults to 1500 ms.
        fallback          : bool   - Should we fallback on XbmcWrapper.ShowDialog on error?

        """

        # check for a title
        if title:
            notificationTitle = "%s - %s" % (Config.appName, title)
        else:
            notificationTitle = Config.appName

        # check for content and merge multiple lines. This is to stay compatible
        # with the LanguageHelper.GetLocalizedString that returns strings as arrays
        # if they are multiple lines (this is because XbmcWrapper.ShowDialog needs
        # this for multi-line dialog boxes.
        if not lines:
            notificationContent = ""
        else:
            if isinstance(lines, (tuple, list)):
                notificationContent = " ".join(lines)
            else:
                notificationContent = lines

        # determine the duration
        notificationType = notificationType.lower()
        if notificationType == XbmcWrapper.Warning and displayTime < 2500:
            displayTime = 2500
        elif notificationType == XbmcWrapper.Info and displayTime < 5000:
            displayTime = 5000
        elif displayTime < 1500:
            # cannot be smaller then 1500 (API limit)
            displayTime = 1500

        # Get an icon
        notificationIcon = os.path.join(Config.rootDir, "icon.png")
        if os.path.exists(notificationIcon):
            # change the separators
            notificationIcon = notificationIcon.replace("\\", "/")
        else:
            notificationIcon = notificationType

        if logger:
            logger.Debug("Showing notification: %s - %s", notificationTitle, notificationContent)

        try:
            xbmcgui.Dialog().notification(
                notificationTitle, notificationContent, icon=notificationIcon, time=displayTime)
            return
        except:
            if fallback:
                XbmcWrapper.ShowDialog(title or "", lines or "")
            # no reason to worry if this does not work on older XBMC's
            return

    @staticmethod
    def ShowSelectionDialog(title, options):
        inputDialog = xbmcgui.Dialog()
        return inputDialog.select(title, options)

    @staticmethod
    def ShowYesNo(title, lines):
        """ Shows a dialog yes/no box with title and text

        Arguments:
        title : string       - the title of the box
        text  : List[string] - the lines to display

        """

        # let's just unlock the interface, in case it's locked.
        LockWithDialog.CloseBusyDialog()

        msgBox = xbmcgui.Dialog()
        if title == "":
            header = Config.appName
        else:
            header = "%s - %s" % (Config.appName, title)

        if len(lines) == 0:
            ok = msgBox.yesno(header, "")
        elif isinstance(lines, basestring):
            # it was just a string, no list or tuple
            ok = msgBox.yesno(header, lines)
        else:
            ok = False
        return ok

    @staticmethod
    def ShowDialog(title, lines):
        """ Shows a dialog box with title and text

        Arguments:
        title : string       - the title of the box
        text  : List[string] - the lines to display

        """

        # let's just unlock the interface, in case it's locked.
        LockWithDialog.CloseBusyDialog()

        msgBox = xbmcgui.Dialog()
        if title == "":
            header = Config.appName
        else:
            header = "%s - %s" % (Config.appName, title)

        if len(lines) == 0:
            ok = msgBox.ok(header, "")
        elif isinstance(lines, basestring):
            # it was just a string, no list or tuple
            ok = msgBox.ok(header, lines)
        elif len(lines) == 1:
            ok = msgBox.ok(header, lines[0])
        elif len(lines) == 2:
            ok = msgBox.ok(header, lines[0], lines[1])
        else:
            ok = msgBox.ok(header, lines[0], lines[1], lines[2])
        return ok

    @staticmethod
    def ShowFolderSelection(title, defaultPath=None, dialogType=3, mask=''):
        """

        @param title:
        @param dialogType: Integer - 0 : ShowAndGetDirectory
                                     1 : ShowAndGetFile
                                     2 : ShowAndGetImage
                                     3 : ShowAndGetWriteableDirectory

        shares         : string or unicode - from sources.xml. (i.e. 'myprograms')
        mask           : [opt] string or unicode - '|' separated file mask. (i.e. '.jpg|.png')
        useThumbs      : [opt] boolean - if True autoswitch to Thumb view if files exist.
        treatAsFolder  : [opt] boolean - if True playlists and archives act as folders.
        default        : [opt] string - default path or file.

        enableMultiple : [opt] boolean - if True multiple file selection is enabled.

        """

        if defaultPath is None:
            defaultPath = xbmc.translatePath("special://home")

        browseDialog = xbmcgui.Dialog()
        destFolder = browseDialog.browse(dialogType, title, 'files', mask, False, False, defaultPath)
        return destFolder

    @staticmethod
    def ExecuteJsonRpc(json, logger=None):
        if logger:
            logger.Trace("Sending command: %s", json)
        response = xbmc.executeJSONRPC(json)
        if logger:
            logger.Trace("Received result: %s", response)
        return response

    @staticmethod
    def WaitForPlayerToStart(player, timeout=10, logger=None, url=None):
        """ waits for the status of the player to start

        Arguments:
        timeout : integer - the maximum wait time
        logger  : Logger  - A logger to log to.
        url     : string  - the URL that should be playing.

        Requires: <import addon="xbmc.python" version="2.0"/>

        """
        return XbmcWrapper.__WaitForPlayer(player, 1, timeout, logger, url)

    @staticmethod
    def WaitForPlayerToEnd(player, timeout=10, logger=None):
        """ waits for the status of the player to end

        Arguments:
        timeout : integer - the maximum wait time
        logger  : Logger  - A logger to log to.

        Requires: <import addon="xbmc.python" version="2.0"/>

        """

        return XbmcWrapper.__WaitForPlayer(player, 0, timeout, logger, None)

    @staticmethod
    def __WaitForPlayer(player, toStart, timeout, logger, url):
        """ waits for the status of the player to be the desired value

        Arguments:
        toStart : integer - the desired value (1 = start, 0 = stop)
        timeout : integer - the maximum wait time
        logger  : Logger  - A logger to log to.
        url     : String  - the URL to wait for

        Requires: <import addon="xbmc.python" version="2.0"/>

        """

        start = time.time()

        if logger:
            logger.Debug("Waiting for Player status '%s'", toStart)
            if url is None:
                logger.Debug("player.isPlaying is '%s', preferred value is '%s'", player.isPlaying(), toStart)
            else:
                logger.Debug("player.isPlaying is '%s', preferred value is %s and stream: '%s'",
                             player.isPlaying(), toStart, url)

        while time.time() - start < timeout:
            if player.isPlaying() == toStart:
                if url is None:
                    # the player stopped in time
                    if logger:
                        logger.Debug("player.isPlaying obtained the desired value '%s'", toStart)
                    return True

                playingFile = player.getPlayingFile()
                if url == playingFile:
                    if logger:
                        logger.Debug("player.isPlaying obtained the desired value '%s' and correct stream.", toStart)
                    return True

                if logger:
                    logger.Debug("player.isPlaying obtained the desired value '%s', but incorrect stream: %s",
                                 toStart, playingFile)

            if logger:
                logger.Debug("player.isPlaying is %s, waiting a cycle", player.isPlaying())
            time.sleep(1.)

        # a time out occurred
        return False
