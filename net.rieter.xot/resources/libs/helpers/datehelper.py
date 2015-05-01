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

        elif language == "en" and short:
            monthLookup = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        elif language == "en":
            monthLookup = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

        elif language == "se" and short:
            monthLookup = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
        elif language == "se":
            monthLookup = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"]

        else:
            error = "Language code '%s' not implemented"
            raise NotImplementedError(error)

        if monthLookup.count(month.lower()) > 0:
            monthValue = monthLookup.index(month.lower()) + 1
        else:
            error = "Month '%s' not found for language '%s'" % (month, language)
            raise ValueError(error)
        return monthValue

if __name__ == "__main__":
    print "Next"
    for day in ("ma", "di", "wo", "do", "vr", "za", "zo", "morgen"):
        print "%s: %s" % (day, DateHelper.GetDateForNextDay(day))

    print "Previous"
    for day in ("ma", "di", "wo", "do", "vr", "za", "zo", "gisteren"):
        print "%s: %s" % (day, DateHelper.GetDateForPreviousDay(day))
