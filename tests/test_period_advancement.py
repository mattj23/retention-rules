"""
    These tests confirm that the period classes perform as expected by brute force testing them over wide ranges of
    dates.  Rather than look directly for expected values, we are checking for the following behaviors:

    * When advancing a clock by time stamps that are significantly smaller than the rough duration of the
        period (keeping in mind that periods like "week" and "month" are not fixed durations), the period integer
        will only ever increase by one OR stay the same.

    * There is a duration which represents the longest possible instance of the period, and that after the clock has
        advanced by that duration, the period integer MUST have increased by one.  For example, after 366 days, the
        year integer MUST have increased by one.

    Because of this strategy, these tests are relatively slow to run and may take several seconds to complete.
    However, they should detect edge cases which might otherwise slip through.

"""

from datetime import datetime as DateTime, timedelta as TimeDelta
from retention_rules.periods import Year, Month, Week, Day, Hour, Minute, Period, SubdividedPeriod


def test_month_advancement():
    """ Tests that the month period advances correctly. """
    tester = AdvancementTester(Month(), TimeDelta(hours=4), TimeDelta(days=31))
    for t, m in tester.test_between(DateTime(1980, 1, 1), DateTime(2040, 1, 1)):
        assert t, m


def test_year_advancement():
    """ Tests that the year period advances correctly. """
    tester = AdvancementTester(Year(), TimeDelta(hours=4), TimeDelta(days=366))  # Leap years have 366 days
    for t, m in tester.test_between(DateTime(1980, 1, 1), DateTime(2040, 1, 1)):
        assert t, m


def test_week_advancement():
    """ Tests that the week period advances correctly. """
    tester = AdvancementTester(Week(), TimeDelta(hours=4), TimeDelta(days=7))
    for t, m in tester.test_between(DateTime(1980, 1, 1), DateTime(2040, 1, 1)):
        assert t, m


def test_week_rollover():
    """ Tests that the week period rolls over correctly. """
    week = Week()
    clock = DateTime(2020, 1, 4)
    last_clock = clock
    last_period = week.to_period(clock)
    while clock < DateTime(2035, 1, 1):
        period = week.to_period(clock)
        if clock.isocalendar()[2] == 1:
            assert period - last_period == 1, f"Week should have advanced by one from {last_clock} -> {clock}"

        last_clock = clock
        last_period = period
        clock += TimeDelta(days=1)


def test_day_advancement():
    """ Tests that the day period advances correctly. """
    tester = AdvancementTester(Day(), TimeDelta(hours=1), TimeDelta(hours=24))
    for t, m in tester.test_between(DateTime(2020, 1, 1), DateTime(2040, 1, 1)):
        assert t, m


def test_hour_advancement():
    """ Tests that the hour period advances correctly. """
    tester = AdvancementTester(Hour(), TimeDelta(minutes=6), TimeDelta(hours=1))
    for t, m in tester.test_between(DateTime(2020, 1, 1), DateTime(2026, 1, 1)):
        assert t, m


def test_minute_advancement():
    """ Tests that the minute period advances correctly. """
    tester = AdvancementTester(Minute(), TimeDelta(seconds=30), TimeDelta(minutes=1))
    for t, m in tester.test_between(DateTime(2024, 1, 1), DateTime(2024, 12, 31, 23, 59, 59)):
        assert t, m


def test_subdivided_hours():
    period = SubdividedPeriod(Hour(), 4)
    tester = AdvancementTester(period, TimeDelta(minutes=3), TimeDelta(minutes=15))
    for t, m in tester.test_between(DateTime(2024, 1, 1), DateTime(2025, 1, 1)):
        assert t, m


class AdvancementTester:
    def __init__(self, period: Period, advance_by: TimeDelta, verify_increment: TimeDelta):
        self.period = period
        self.advance_by = advance_by
        self.verify_increment = verify_increment

    def test_between(self, start: DateTime, end: DateTime):
        """ Tests that the period advances correctly between two dates """
        clock = start
        last_clock = clock
        last_period = self.period.to_period(clock)
        last_change = clock

        while clock < end:
            clock += self.advance_by
            period = self.period.to_period(clock)

            yield 0 <= period - last_period <= 1, f"Periods should only advance by one at a time, but {last_clock} " \
                                                  f"-> {clock} advanced by {period - last_period}"

            if period - last_period == 1:
                last_change = clock

            if clock - last_change > self.verify_increment:
                yield False, f"Period should have advanced between {last_change} -> {clock}, but did not ({period})"

            last_clock = clock
            last_period = period
