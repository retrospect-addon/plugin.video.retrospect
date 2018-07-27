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

#===============================================================================
# Make global object available
#===============================================================================
# from logger import Logger


class DateHelper:
    """Helper class to parse datenames into numbers"""

    def __init__(self):
        """No initialisation, just statics"""

        raise NotImplementedError("Just statics")

    @staticmethod
    def ThisYear():
        now = datetime.datetime.now()
        return now.year

    @staticmethod
    def GetDateForNextDay(day, possibilities=None, tomorrow="Morgen", today="Vandaag"):
        """ Gets the date for the next Weekday (default ["ma", "di", "wo", "do", "vr", "za", "zo"]).

        Arguments:
        day : String - Weekday with that has in index in the "possibilities" parameter

        Keywork Arguments:
        possibilities : List   - List of possible weekdays.
        today         : String - Value for today
        tomorrow      : String - Value for tomorrow

        Returns the date of the next "day".

        """

        if not possibilities:
            possibilities = ["ma", "di", "wo", "do", "vr", "za", "zo"]

        date = datetime.datetime.now()
        dayNow = date.weekday()

        if day.lower() == today.lower():
            return date

        if day.lower() == tomorrow.lower():
            return date + datetime.timedelta(days=1)

        dayOfWeekToFind = possibilities.index(day)

        if dayNow < dayOfWeekToFind:
            dateToFind = date + datetime.timedelta(days=dayOfWeekToFind - dayNow)
        else:
            # Now: Su (6), Need Mo (0)
            dateToFind = date + datetime.timedelta(days=dayOfWeekToFind + 7 - dayNow)

        return dateToFind

    @staticmethod
    def GetDateForPreviousDay(day, possibilities=None, yesterday="Gisteren"):
        """ Gets the date for the previous Weekday (default ["ma", "di", "wo", "do", "vr", "za", "zo"]).

        Arguments:
        day : String - Weekday with that has in index in the "possibilities" parameter

        Keywork Arguments:
        possibilities : List - List of possible weekdays.

        Returns the date of the previous "day".

        """

        if not possibilities:
            possibilities = ["ma", "di", "wo", "do", "vr", "za", "zo"]

        date = datetime.datetime.now()
        dayNow = date.weekday()

        if day.lower() == yesterday.lower():
            return date + datetime.timedelta(days=-1)

        dayOfWeekToFind = possibilities.index(day)

        if dayNow >= dayOfWeekToFind:
            dateToFind = date - datetime.timedelta(days=dayNow - dayOfWeekToFind)
        else:
            # Now: Su (6), Need Mo (0)
            dateToFind = date - datetime.timedelta(days=dayNow + 7 - dayOfWeekToFind)

        return dateToFind

    @staticmethod
    def GetMonthFromName(month, language, short=None):
        """Gets the month number from the name.

        Arguments:
        month    : string - Name of the month
        language : string - Language code (nl, en)

        Keyword Arguments:
        short : [opt] boolean - indicates the monthnames are short. Default: None

        Returns:
        the month number. If short = None, both long and short formats are tried
        with the short first, then the long.
        if short is True or False, only those options are selected.

        """

        if short is None:
            try:
                return DateHelper.__GetMonthFromName(month, language)
            except:
                return DateHelper.__GetMonthFromName(month, language, False)
        else:
            return DateHelper.__GetMonthFromName(month, language, short)

    @staticmethod
    def GetDateFromPosix(posix, tz=None):
        # type: (float, datetime.tzinfo) -> datetime.datetime
        """ Creates a datetime from a Posix Time stamp

        @param posix:   the posix time stamp integer
        @return:        a valid datetime.datetime object.
        """

        return datetime.datetime.fromtimestamp(posix, tz)

    @staticmethod
    def GetDateFromString(value, dateFormat="%Y-%m-%dT%H:%M:%S+00:00"):
        # type: (str, str) -> time.struct_time
        """ Converts a formatted date-time string to a time struct.

        @param value:       the string value to parse
        @param dateFormat:  the format to use
        @return:            a time.struct_time

        time.struct_time values:
        0 	tm_year 	(for example, 1993)
        1 	tm_mon 	    range [1, 12]
        2 	tm_mday 	range [1, 31]
        3 	tm_hour 	range [0, 23]
        4 	tm_min 	    range [0, 59]
        5 	tm_sec 	    range [0, 61]; see (2) in strftime() description
        6 	tm_wday 	range [0, 6], Monday is 0
        7 	tm_yday 	range [1, 366]
        8 	tm_isdst 	0, 1 or -1; see below

        The datetime.strptime does not work in Kodi. See:
        https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior

        """

        return time.strptime(value, dateFormat)

    @staticmethod
    def __GetMonthFromName(month, language, short=True):
        """Gets the month number from the name.

        Arguments:
        month    : string - Name of the month
        language : string - Language code (nl, en)

        Keyword Arguments:
        short : [opt] boolean - indicates the monthnames are short. Default: True

        Returns:
        the month number

        """

        if language == "nl" and short:
            monthLookup = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
        elif language == "nl":
            monthLookup = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]

        elif language == "no" and short:
            monthLookup = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
        elif language == "no":
            monthLookup = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"]

        elif language == "en" and short:
            monthLookup = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        elif language == "en":
            monthLookup = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

        elif language == "se" and short:
            monthLookup = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
        elif language == "se":
            monthLookup = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"]

        else:
            error = "Language code '%s' not implemented" % (language, )
            raise NotImplementedError(error)

        if monthLookup.count(month.lower()) > 0:
            monthValue = monthLookup.index(month.lower()) + 1
        else:
            error = "Month '%s' not found for language '%s'" % (month, language)
            raise ValueError(error)
        return monthValue
