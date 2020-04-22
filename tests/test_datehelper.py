# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import unittest
import datetime
import time
import pytz

from resources.lib.helpers.datehelper import DateHelper


class TestDateHelper(unittest.TestCase):

    def test_no_constructor(self):
        with self.assertRaises(NotImplementedError):
            DateHelper()

    def test_from_posix(self):
        tz = UTC()  # test using UTC
        date_time = DateHelper.get_date_from_posix(0, tz)
        should_be = datetime.datetime(1970, 1, 1, 0, 0, 0)

        self.__compareDates(should_be, date_time)

    def test_from_posix_float(self):
        tz = UTC()  # test using UTC
        date_time = DateHelper.get_date_from_posix(1477491485.9, tz)
        # Wed, 26 Oct 2016 14:18:05 GMT
        should_be = datetime.datetime(2016, 10, 26, 14, 18, 5, 900000)

        self.__compareDates(should_be, date_time)
        self.assertEqual(should_be.microsecond, date_time.microsecond)

    def test_from_posix_with_timezone(self):
        tz = PlusOne()  # test using UTC
        date_time = DateHelper.get_date_from_posix(3700161184, tz)
        # Wed, 26 Oct 2016 14:18:05 GMT
        should_be = datetime.datetime(2087, 4, 2, 22, 33, 4, 0, tzinfo=tz)

        self.__compareDates(should_be, date_time)
        self.assertEqual(should_be.microsecond, date_time.microsecond)

    def test_from_posix_out_of_range(self):
        tz = UTC()  # test using UTC
        date_time = DateHelper.get_date_from_posix(3700161184, tz)
        # Wed, 26 Oct 2016 14:18:05 GMT
        should_be = datetime.datetime(2087, 4, 2, 22, 33, 4, 0)

        self.__compareDates(should_be, date_time)
        self.assertEqual(should_be.microsecond, date_time.microsecond)

    def test_this_year(self):
        self.assertEqual(datetime.datetime.now().year, DateHelper.this_year())

    def test_next_day_today(self):
        today = datetime.datetime.now()
        today_value = "aapje"
        tomorrow_date = DateHelper.get_date_for_next_day(today_value, today=today_value)
        self.__compareDates(today, tomorrow_date, include_seconds=False)

    def test_next_day_tomorrow(self):
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        tomrrow_value = "aapje"
        tomorrow_date = DateHelper.get_date_for_next_day(tomrrow_value, tomorrow=tomrrow_value)
        self.__compareDates(tomorrow, tomorrow_date, include_seconds=False)

    def test_next_day_plusone(self):
        options = ["ma", "di", "wo", "do", "vr", "za", "zo"]
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

        day_to_find = options[tomorrow.weekday()]
        tomorrow_date = DateHelper.get_date_for_next_day(day_to_find, possibilities=options)
        self.__compareDates(tomorrow, tomorrow_date, include_seconds=False)

    def test_next_day_no_options(self):
        options = ["ma", "di", "wo", "do", "vr", "za", "zo"]
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)

        day_to_find = options[tomorrow.weekday()]
        tomorrow_date = DateHelper.get_date_for_next_day(day_to_find)
        self.__compareDates(tomorrow, tomorrow_date, include_seconds=False)

    def test_next_day_minusone(self):
        options = ["ma", "di", "wo", "do", "vr", "za", "zo"]
        yesterday_next_week = datetime.datetime.now() + datetime.timedelta(days=(-1 + 7))

        day_to_find = options[yesterday_next_week.weekday()]
        next_day_equal_to_yesterday = DateHelper.get_date_for_next_day(day_to_find, possibilities=options)
        self.__compareDates(yesterday_next_week, next_day_equal_to_yesterday, include_seconds=False)

    def test_previous_day_yesterday(self):
        yesterday = datetime.datetime.now() + datetime.timedelta(days=-1)
        yesterday_value = "daybeforetoday"
        yesterday_date = DateHelper.get_date_for_previous_day(yesterday_value, yesterday=yesterday_value)
        self.__compareDates(yesterday, yesterday_date, include_seconds=False)

    def test_previous_day_plusone(self):
        options = ["ma", "di", "wo", "do", "vr", "za", "zo"]
        tomorrow_previous_week = datetime.datetime.now() + datetime.timedelta(days=(1-7))
        day_to_find = options[tomorrow_previous_week.weekday()]
        previous_date = DateHelper.get_date_for_previous_day(day_to_find, possibilities=options)
        self.__compareDates(tomorrow_previous_week, previous_date, include_seconds=False)

    def test_previous_day_no_options(self):
        options = ["ma", "di", "wo", "do", "vr", "za", "zo"]
        previous_day = datetime.datetime.now() + datetime.timedelta(days=-1)
        day_to_find = options[previous_day.weekday()]
        previous_date = DateHelper.get_date_for_previous_day(day_to_find)
        self.__compareDates(previous_day, previous_date, include_seconds=False)

    def test_previous_day_minusone(self):
        options = ["ma", "di", "wo", "do", "vr", "za", "zo"]
        yesterday = datetime.datetime.now() + datetime.timedelta(days=-1)

        day_to_find = options[yesterday.weekday()]
        next_day_equal_to_yesterday = DateHelper.get_date_for_previous_day(day_to_find, possibilities=options)
        self.__compareDates(yesterday, next_day_equal_to_yesterday, include_seconds=False)

    def test_get_nl_month_short(self):
        month = DateHelper.get_month_from_name("jan", "nl", short=True)
        self.assertEqual(1, month)

    def test_get_nl_month_long(self):
        month_lng = DateHelper.get_month_from_name("januari", "nl", short=False)
        self.assertEqual(1, month_lng)

    def test_get_uk_month(self):
        month = DateHelper.get_month_from_name("jan", "en")
        month_lng = DateHelper.get_month_from_name("january", "en")
        self.assertEqual(1, month)
        self.assertEqual(1, month_lng)

    def test_get_no_month(self):
        month = DateHelper.get_month_from_name("jan", "no")
        month_lng = DateHelper.get_month_from_name("januar", "no")
        self.assertEqual(1, month)
        self.assertEqual(1, month_lng)

    def test_get_se_month(self):
        month = DateHelper.get_month_from_name("jan", "se")
        month_lng = DateHelper.get_month_from_name("januari", "se")
        self.assertEqual(1, month)
        self.assertEqual(1, month_lng)

    def test_get_month_unsupported(self):
        with self.assertRaises(NotImplementedError):
            DateHelper.get_month_from_name("jan", "limburgs")

    def test_get_month_unknown(self):
        with self.assertRaises(ValueError):
            DateHelper.get_month_from_name("nomonth", "en")

    def test_get_from_string(self):
        date_value = datetime.datetime(2016, 1, 1, 23, 21, 20)
        date = DateHelper.get_date_from_string("2016-01-01T23:21:20+00:00")
        self.__compareDateAndTimeStruct(date_value, date)

    def test_get_from_string_short(self):
        date_value = datetime.datetime(2016, 1, 1, 23, 21, 1)
        date = DateHelper.get_date_from_string("2016-1-1T23:21:1+00:00")
        self.__compareDateAndTimeStruct(date_value, date)

    def test_get_from_custom_string(self):
        date_value = datetime.datetime(2016, 12, 1, 23, 21, 20)
        frmt = "%H:%M:%S op %d in month %m of the year %Y"
        date = DateHelper.get_date_from_string("23:21:20 op 1 in month 12 of the year 2016", date_format=frmt)
        self.__compareDateAndTimeStruct(date_value, date)

    def test_get_naive_datetime_from_string(self):
        date_value = datetime.datetime(2016, 1, 1, 23, 21, 20)
        date_time = DateHelper.get_datetime_from_string("2016-01-01T23:21:20", "%Y-%m-%dT%H:%M:%S")
        self.assertIsNone(date_time.tzinfo)
        self.__compareDates(date_value, date_time)

    def test_get_utc_datetime_from_string(self):
        # Arrabge
        date_value = datetime.datetime(2016, 1, 1, 23, 21, 20)
        time_zone = "UTC"
        tz = pytz.timezone(time_zone)
        date_value = tz.localize(date_value)

        # Act
        date_time = DateHelper.get_datetime_from_string(
            "2016-01-01T23:21:20", "%Y-%m-%dT%H:%M:%S", "UTC")

        # Assert
        self.assertEqual(tz.zone, time_zone)
        self.__compareDates(date_value, date_time)

    def test_get_amsterdam_datetime_from_string(self):
        # Arrange
        date_value = datetime.datetime(2016, 1, 1, 23, 21, 20)
        time_zone = "Europe/Amsterdam"
        tz = pytz.timezone(time_zone)
        date_value = tz.localize(date_value)

        # Act
        date_time = DateHelper.get_datetime_from_string(
            "2016-01-01T23:21:20", "%Y-%m-%dT%H:%M:%S", "Europe/Amsterdam")

        # Assert
        self.assertEqual(tz.zone, time_zone)
        self.__compareDates(date_value, date_time)

    def __compareDateAndTimeStruct(self, date_value, time_value, include_seconds=True):
        # type: (datetime.datetime, time.struct_time, bool) -> None
        """ Compares to datetime objects based on values.

        @param date_value:       The date to compare
        @param time_value:       The time to compare
        @param include_seconds:  Compare seconds?

        """
        self.assertEqual(date_value.year, time_value[0])
        self.assertEqual(date_value.month, time_value[1])
        self.assertEqual(date_value.day, time_value[2])
        self.assertEqual(date_value.hour, time_value[3])
        self.assertEqual(date_value.minute, time_value[4])
        if include_seconds:
            self.assertEqual(date_value.second, time_value[5])

    def __compareDates(self, one, two, include_seconds=True):
        # type: (datetime.datetime, datetime.datetime, bool) -> None
        """ Compares to datetime objects based on values.

        @param one:             One value
        @param two:             The other value
        @param include_seconds:  Compare seconds?

        """
        self.assertEqual(one.year, two.year)
        self.assertEqual(one.month, two.month)
        self.assertEqual(one.day, two.day)
        self.assertEqual(one.hour, two.hour)
        self.assertEqual(one.minute, two.minute)
        if include_seconds:
            self.assertEqual(one.second, two.second)

        if one.tzinfo is not None:
            self.assertEqual(one.tzinfo, two.tzinfo)


class PlusOne(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return datetime.timedelta(hours=1)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(hours=1)


class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)
