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
import io
import sys
import traceback
import time
import datetime


class Logger:
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    TRACE = 0

    # the actual logger
    __logger = None

    @staticmethod
    def Instance():
        """ return the logger instance """
        return Logger.__logger

    @staticmethod
    def Exists():
        """ returns a boolean indicating that a logger was created """
        return Logger.__logger is not None

    @staticmethod
    def CreateLogger(logFileName, applicationName, minLogLevel=10, append=False, dualLogger=None):
        """Intialises the Logger Instance and opens it for writing

        Arguments:
        logFile    : string  - Path of the log file to write to
        logDual    : boolean - If set to True, exceptions are also written to the
                               standard out.

        Keyword Arguments:
        append              : [opt] bool -     If set to True, the current log file is not deleted.
                                               Default value is False.
        minLogLevel         : [opt] integer -  Minimum log level to log. Levels equal or higher
                                               are logged.
        memoryInfoProvider  : [opt] function - Function for memory callback
        dualLogger          : [opt] function - Fuction for dual logging

        """

        if Logger.__logger is None:
            Logger.__logger = Logger(logFileName, applicationName, minLogLevel, append, dualLogger)
            # Logger.__logger.dualLog("CREATING LOGGER: {0}".format(Logger.__logger.id))
        else:
            Logger.Warning("Cannot create a second logger instance!")
            # Logger.__logger.dualLog("EXISTING LOGGER: {0}".format(Logger.__logger.id))
        return Logger.__logger

    def __init__(self, logFileName, applicationName, minLogLevel=10, append=False, dualLogger=None):
        """Intialises the Logger Instance and opens it for writing

        Arguments:
        logFile    : string  - Path of the log file to write to
        logDual    : boolean - If set to True, exceptions are also written to the
                               standard out.

        Keyword Arguments:
        append     : [opt] bool    - If set to True, the current log file is not deleted.
                                     Default value is False.
        minLogLeve : [opt] integer - Minimum log level to log. Levels equal or higher
                                     are logged.

        """

        self.logFileName = logFileName
        self.fileMode = "a"
        self.fileFlags = os.O_WRONLY | os.O_APPEND | os.O_CREAT

        self.minLogLevel = minLogLevel
        self.dualLog = dualLogger
        self.logDual = dualLogger is not None
        self.logEntryCount = 0
        self.flushInterval = 5 if logFileName is not None else 1
        self.encoding = 'cp1252'
        self.applicationName = applicationName

        # self.logHandle = -1
        self.id = int(time.time())
        self.timeFormat = "%Y%m%d %H:%M:%S"
        self.logFormat = '%s - [%-8s] - %-20s - %-4d - %s\n'

        self.logLevelNames = {
            Logger.CRITICAL: 'CRITICAL',
            Logger.ERROR: 'ERROR',
            Logger.WARNING: 'WARNING',
            Logger.INFO: 'INFO',
            Logger.DEBUG: 'DEBUG',
            Logger.TRACE: 'TRACE'
        }

        if not append:
            self.CleanUpLog()

        # now open the file
        self.__OpenLog()

        # print to the XBMC logfile to tell the user the actual logfile path
        if self.dualLog:
            dualLogger("%s :: Additional logging can be found in '%s'" % (self.applicationName, self.logFileName,), 1)
        return

    @staticmethod
    def Trace(msg, *args, **kwargs):
        """Logs an trace message (with loglevel 0)

        Arguments:
        msg    : string - The message to log
        args   : list   - List of arguments

        Keyword Arguments:
        kwargs : list - List of keyword arguments

        The arguments and keyword arguments are used in a string format way
        so and will replace the parameters in the message.

        """

        Logger.__logger.__Write(msg, level=Logger.TRACE, *args, **kwargs)
        return

    @staticmethod
    def Debug(msg, *args, **kwargs):
        """Logs an debug message (with loglevel 10)

        Arguments:
        msg    : string - The message to log
        args   : list   - List of arguments

        Keyword Arguments:
        kwargs : list - List of keyword arguments

        The arguments and keyword arguments are used in a string format way
        so and will replace the parameters in the message.

        """

        Logger.__logger.__Write(msg, level=Logger.DEBUG, *args, **kwargs)
        return

    @staticmethod
    def Info(msg, *args, **kwargs):
        """Logs an informational message (with loglevel 20)

        Arguments:
        msg    : string - The message to log
        args   : list   - List of arguments

        Keyword Arguments:
        kwargs : list - List of keyword arguments

        The arguments and keyword arguments are used in a string format way
        so and will replace the parameters in the message.

        """

        Logger.__logger.__Write(msg, level=Logger.INFO, *args, **kwargs)
        return

    @staticmethod
    def Error(msg, *args, **kwargs):
        """Logs an error message (with loglevel 40)

        Arguments:
        msg    : string - The message to log
        args   : list   - List of arguments

        Keyword Arguments:
        kwargs : list - List of keyword arguments

        The arguments and keyword arguments are used in a string format way
        so and will replace the parameters in the message.

        """

        Logger.__logger.__Write(msg, level=Logger.ERROR, *args, **kwargs)
        return

    @staticmethod
    def Warning(msg, *args, **kwargs):
        """Logs an warning message (with loglevel 30)

        Arguments:
        msg    : string - The message to log
        args   : list   - List of arguments

        Keyword Arguments:
        kwargs : list - List of keyword arguments

        The arguments and keyword arguments are used in a string format way
        so and will replace the parameters in the message.

        """

        Logger.__logger.__Write(msg, level=Logger.WARNING, *args, **kwargs)
        return

    @staticmethod
    def Critical(msg, *args, **kwargs):
        """Logs an critical message (with loglevel 50)

        Arguments:
        msg    : string - The message to log
        args   : list   - List of arguments

        Keyword Arguments:
        kwargs : list - List of keyword arguments

        The arguments and keyword arguments are used in a string format way
        so and will replace the parameters in the message.

        """

        Logger.__logger.__Write(msg, level=Logger.CRITICAL, *args, **kwargs)
        return

    def CloseLog(self, logClosing=True):
        """Close the logfile.

        Calling close() on a filehandle also closes the FileDescriptor

        Keyword Arguments:
        logClosing : boolean - indicates whether a log line is written on closure.

        """

        if logClosing:
            self.Info("%s :: Flushing and closing logfile.", self.applicationName)
            # self.dualLog("CURRENT LOGGER before: {0}".format(Logger.Instance() or "none"))
            Logger._Logger__logger = None
            # self.dualLog("CURRENT LOGGER after: {0}".format(Logger.Instance() or "none"))
            # self.dualLog("CLOSING LOGGER: {0}".format(self.id))

        self.logHandle.flush()
        if self.logHandle is not sys.stdout:
            self.logHandle.close()

    def CleanUpLog(self):
        """Closes an old log file and creates a new one.

        This method renames the current log file to .old.log and creates a
        new log file with the .log filename.

        If the original file was open for writing/appending, the new file
        will also be open for writing/appending

        """

        if self.logFileName is None:
            return

        # create old.log file
        print("%s :: Cleaning up logfile: %s" % (self.applicationName, self.logFileName))
        try:
            wasOpen = True
            self.CloseLog(logClosing=False)
        except:
            wasOpen = False

        (fileName, extension) = os.path.splitext(self.logFileName)
        oldFileName = "%s.old%s" % (fileName, extension)
        if os.path.exists(self.logFileName):
            if os.path.exists(oldFileName):
                os.remove(oldFileName)
            os.rename(self.logFileName, oldFileName)

        if wasOpen:
            self.__OpenLog()
        return

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return str(self.id)

    def __Write(self, msg, *args, **kwargs):
        """Writes the message to the log file taking into account
        the given arguments and keyword arguments.

        Arguments:
        msg    : string - The message to log
        args   : list   - List of arguments

        Keyword Arguments:
        kwargs : list - List of keyword arguments

        The arguments and keyword arguments are used in a string format way
        so and will replace the parameters in the message.

        """

        try:
            formattedMessage = ""
            logLevel = kwargs["level"]

            # determine if write is needed:
            if logLevel < self.minLogLevel:
                return

            # convert possible tupple to string:
            msg = str(msg)

            # Fill the message with it's content
            if len(args) > 0:
                # print "# of args: %s" % (len(args[0]))
                msg = msg % args
            else:
                msg = msg

            # get frame information
            (sourceFile, sourceLineNumber) = self.__FindCaller()

            # get time information
            timestamp = datetime.datetime.today().strftime(self.timeFormat)

            # check for exception info, if present, add to end of string:
            if "exc_info" in kwargs:
                if self.logDual:
                    self.dualLog(traceback.format_exc())
                msg = "%s\n%s" % (msg, traceback.format_exc())

            # now split lines and write everyline into the logfile:
            # result = re.compile("[\r\n]+", re.DOTALL + re.IGNORECASE)
            # lines = result.split(msg)
            # lines = re.split("[\r\n]+", msg)#, flags = re.DOTALL + re.IGNORECASE)
            lines = msg.splitlines()

            try:
                # check if multiline
                if len(lines) > 1:
                    for i in range(0, len(lines)):
                        # for line in lines:
                        line = lines[i]
                        if len(line) <= 0:
                            continue

                        # if last line:
                        if i == 0:
                            line = line
                        elif i == len(lines) - 1:
                            line = '+ %s' % (line, )
                        else:
                            line = '| %s' % (line, )
                        formattedMessage = self.logFormat % (
                            timestamp,
                            self.logLevelNames.get(logLevel),
                            sourceFile,
                            sourceLineNumber,
                            line)
                        self.logHandle.write(formattedMessage)
                else:
                    formattedMessage = self.logFormat % (
                        timestamp,
                        self.logLevelNames.get(logLevel),
                        sourceFile,
                        sourceLineNumber,
                        msg)
                    self.logHandle.write(formattedMessage)
            except UnicodeEncodeError:
                # self.Error("Unicode logging error", exc_info=True)
                # formattedMessage = formattedMessage.encode('raw_unicode_escape')
                self.logHandle.write(formattedMessage)
                raise

            # Finally close the filehandle
            self.logEntryCount += 1
            if self.logEntryCount % self.flushInterval == 0:
                # self.logHandle.write("Saving")
                self.logEntryCount = 0
                self.logHandle.flush()
            return
        except:
            if self.logDual:
                self.dualLog("Retrospect Logger :: Error logging in Logger.py:")
                self.dualLog("---------------------------")
                self.dualLog(traceback.format_exc())
                self.dualLog("---------------------------")
                self.dualLog(repr(msg))
                self.dualLog(repr(args))
                # noinspection PyUnboundLocalVariable
                self.dualLog(repr(formattedMessage))
                self.dualLog("---------------------------")
            else:
                traceback.print_exc()

    def __FindCaller(self):
        """Find the stack frame of the caller.

        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.

        """
        returnValue = ("Unknown", 0)

        # get the current frame and descent down until the correct one is found
        # noinspection PyProtectedMember
        currentFrame = sys._getframe(3)  # could be _getframe(#) and (3)
        while hasattr(currentFrame, "f_code"):
            co = currentFrame.f_code
            sourceFile = os.path.normcase(co.co_filename)
            methodName = co.co_name
            # if currentFrame belongs to this logger.py, equals <string> or equals a private log
            # method (_log or __Log) continue searching.
            if sourceFile == "<string>" \
                    or sourceFile in os.path.normcase(__file__) \
                    or "stopwatch.py" in sourceFile \
                    or methodName in ("_Log", "__Log"):
                currentFrame = currentFrame.f_back
                continue
            else:
                # get the sourcePath and sourceFile
                (sourcePath, sourceFile) = os.path.split(sourceFile)
                returnValue = (sourceFile, currentFrame.f_lineno)
                break

        return returnValue

    def __OpenLog(self):
        """Opens the log file for appending

        This method opens a logfile for writing. If one already exists, it will
        be appended. If it does not exist, a new one is created.

        Problem:
        If we would use open(self.logFileName, "a") we would get an invalid
        filedescriptor error in Linux!

        Possible fixes:
        1 - Modding the flags to only have os.O_CREATE if the file does not exists
            works, but then the file is appended at position 0 instead of the end!

        2 - Using a custom filedescriptor. This works, but now the file just keeps
            getting overwritten.

        3 - OR: why not do a manual append: first read the complete file into a
            string. Then do an open(self.logFileName, "w"), write the previous
            content and then just continue!

        Finally: stick to the basic open(file, mode) and changes modes depending on
        the available files.

        """

        if self.logFileName is None:
            self.logHandle = sys.stdout
            return

        if os.path.exists(self.logFileName):
            # the file already exists. Now to prevent errors in Linux
            # we will open a file in Read + (Read and Update) mode
            # and set the pointer to the end.
            self.logHandle = io.open(self.logFileName, "r+b")
            self.logHandle.seek(0, 2)
            self.__Write("XOT Logger :: Appending Existing logFile", level=Logger.INFO)
        else:
            logDir = os.path.dirname(self.logFileName)
            if not os.path.isdir(logDir):
                os.makedirs(logDir)
            # no file exists, so just create a new one for writing
            self.logHandle = io.open(self.logFileName, "wb")

        return
