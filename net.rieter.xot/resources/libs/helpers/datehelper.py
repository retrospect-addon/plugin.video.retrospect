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
    def this_year():
        now = datetime.datetime.now()
        return now.year

    @staticmethod
    def get_date_for_next_day(day, possibilities=None, tomorrow="Morgen", today="Vandaag"):
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
        day_now = date.weekday()

        if day.lower() == today.lower():
            return date

        if day.lower() == tomorrow.lower():
            return date + datetime.timedelta(days=1)

        day_of_week_to_find = possibilities.index(day)

        if day_now < day_of_week_to_find:
            date_to_find = date + datetime.timedelta(days=day_of_week_to_find - day_now)
        else:
            # Now: Su (6), Need Mo (0)
            date_to_find = date + datetime.timedelta(days=day_of_week_to_find + 7 - day_now)

        return date_to_find

    @staticmethod
    def get_date_for_previous_day(day, possibilities=None, yesterday="Gisteren"):
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
        day_now = date.weekday()

        if day.lower() == yesterday.lower():
            return date + datetime.timedelta(days=-1)

        day_of_week_to_find = possibilities.index(day)

        if day_now >= day_of_week_to_find:
            date_to_find = date - datetime.timedelta(days=day_now - day_of_week_to_find)
        else:
            # Now: Su (6), Need Mo (0)
            date_to_find = date - datetime.timedelta(days=day_now + 7 - day_of_week_to_find)

        return date_to_find

    @staticmethod
    def get_month_from_name(month, language, short=None):
        """ Gets the month number from the name.

        :param str month:           Name of the month.
        :param str language:        Language code (nl, en).
        :param bool|none short:     Indicates the monthnames are short. Default: None

        :return: The month number.
        :rtype: int

        """

        if short is None:
            try:
                return DateHelper.__get_month_from_name(month, language)
            except:
                return DateHelper.__get_month_from_name(month, language, False)
        else:
            return DateHelper.__get_month_from_name(month, language, short)

    @staticmethod
    def get_date_from_posix(posix, tz=None):
        # type: (float, datetime.tzinfo) -> datetime.datetime
        """ Creates a datetime from a Posix Time stamp

        @param posix:   the posix time stamp integer
        @return:        a valid datetime.datetime object.
        """

        return datetime.datetime.fromtimestamp(posix, tz)

    @staticmethod
    def get_date_from_string(value, date_format="%Y-%m-%dT%H:%M:%S+00:00"):
        # type: (str, str) -> time.struct_time
        """ Converts a formatted date-time string to a time struct.

        @param value:       the string value to parse
        @param date_format:  the format to use
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

        return time.strptime(value, date_format)

    @staticmethod
    def __get_month_from_name(month, language, short=True):
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
            month_lookup = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
        elif language == "nl":
            month_lookup = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]

        elif language == "no" and short:
            month_lookup = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
        elif language == "no":
            month_lookup = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"]

        elif language == "en" and short:
            month_lookup = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        elif language == "en":
            month_lookup = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

        elif language == "se" and short:
            month_lookup = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
        elif language == "se":
            month_lookup = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"]

        else:
            error = "Language code '%s' not implemented" % (language, )
            raise NotImplementedError(error)

        if month_lookup.count(month.lower()) > 0:
            month_value = month_lookup.index(month.lower()) + 1
        else:
            error = "Month '%s' not found for language '%s'" % (month, language)
            raise ValueError(error)
        return month_value
