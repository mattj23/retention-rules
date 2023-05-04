"""
    Constructs for retention periods

    Retention periods are windows of time which are used to apply retention rules.  They are not simply unfixed
    durations of time, but instead are regions on a timeline.  For example, a "week" is not the same as "7 days", as
    the week is a period of time which starts on a specific day of the week and ends on the same day of the week.

    To handle this, retention periods must convert a date into an integer, where the next period can be found by
    incrementing the integer by one and the previous period can be found by decrementing it by one.  The easiest
    example of this is a "year", which is simply the year associated with the date.  There is a difference between
    specifying that one wants to retain data from each year, vs specifying that one wants to retain data from increments
    of time backwards from the present we usually associate with a year.

"""

from abc import ABC, abstractmethod
from datetime import datetime as DateTime, timedelta as TimeDelta

_reference_date = DateTime(1970, 1, 1)


def _year(time_stamp: DateTime) -> int:
    return time_stamp.year - _reference_date.year


def _day(time_stamp: DateTime) -> int:
    return int((time_stamp - _reference_date).days)


class Period(ABC):
    def to_period(self, time_stamp: DateTime) -> int:
        """Converts a time_stamp into an integer representing the period of time it is in"""
        raise NotImplementedError()

    def max_duration(self) -> TimeDelta:
        """Returns the maximum duration of the period"""
        raise NotImplementedError()


class Year(Period):
    def to_period(self, time_stamp: DateTime) -> int:
        return _year(time_stamp)

    def max_duration(self) -> TimeDelta:
        return TimeDelta(days=366)


class Month(Period):
    def to_period(self, time_stamp: DateTime) -> int:
        return _year(time_stamp) * 12 + time_stamp.month

    def max_duration(self) -> TimeDelta:
        return TimeDelta(days=31)


class Week(Period):
    def to_period(self, time_stamp: DateTime) -> int:
        # This is easier than dealing with the years that have 53 weeks
        days = _day(time_stamp) - _reference_date.isocalendar().weekday
        return days // 7

    def max_duration(self) -> TimeDelta:
        return TimeDelta(days=7)


class Day(Period):
    def to_period(self, time_stamp: DateTime) -> int:
        return _day(time_stamp)

    def max_duration(self) -> TimeDelta:
        return TimeDelta(hours=24)


class Hour(Period):
    def to_period(self, time_stamp: DateTime) -> int:
        return _day(time_stamp) * 24 + time_stamp.hour

    def max_duration(self) -> TimeDelta:
        return TimeDelta(minutes=60)


class Minute(Period):
    def to_period(self, time_stamp: DateTime) -> int:
        return (_day(time_stamp) * 24 + time_stamp.hour) * 60 + time_stamp.minute

    def max_duration(self) -> TimeDelta:
        return TimeDelta(seconds=60)