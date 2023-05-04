from datetime import datetime as DateTime, timedelta as TimeDelta
from retention_rules.periods import Year, Month, Week, Day, Hour, Minute, Period, SubdividedPeriod


def test_year_start_times():
    """ Tests that the year period starts at the correct times. """
    year = Year()
    for i in range(100):
        start = year.period_start(i)
        assert i == year.to_period(start), f"Year {i} ({start}) failed round trip"
        assert i - 1 == year.to_period(start - TimeDelta(seconds=1)), f"Year {i} ({start}) failed to decrement"


def test_month_start_times():
    """ Tests that the month period starts at the correct times. """
    month = Month()
    offset = month.to_period(DateTime(1980, 1, 1))

    for j in range(1200):
        i = j + offset
        start = month.period_start(i)
        assert i == month.to_period(start), f"Month {i} ({start}) failed round trip"
        assert i - 1 == month.to_period(start - TimeDelta(seconds=1)), f"Month {i} ({start}) failed to decrement"


def test_week_start_times():
    """ Tests that the week period starts at the correct times. """
    week = Week()
    offset = week.to_period(DateTime(2000, 1, 1))

    for j in range(52 * 50):
        i = j + offset
        start = week.period_start(i)
        assert i == week.to_period(start), f"Week {i} ({start}) failed round trip"
        assert i - 1 == week.to_period(start - TimeDelta(seconds=1)), f"Week {i} ({start}) failed to decrement"


def test_day_start_times():
    """ Tests that the day period starts at the correct times. """
    day = Day()
    offset = day.to_period(DateTime(2020, 1, 1))

    for j in range(365 * 50):
        i = j + offset
        start = day.period_start(i)
        assert i == day.to_period(start), f"Day {i} ({start}) failed round trip"
        assert i - 1 == day.to_period(start - TimeDelta(seconds=1)), f"Day {i} ({start}) failed to decrement"


def test_hour_start_times():
    """ Tests that the hour period starts at the correct times. """
    hour = Hour()
    offset = hour.to_period(DateTime(2015, 1, 1))

    for j in range(24 * 365 * 10):
        i = j + offset
        start = hour.period_start(i)
        assert i == hour.to_period(start), f"Hour {i} ({start}) failed round trip"
        assert i - 1 == hour.to_period(start - TimeDelta(seconds=1)), f"Hour {i} ({start}) failed to decrement"


def test_minute_start_times():
    """ Tests that the minute period starts at the correct times. """
    minute = Minute()
    offset = minute.to_period(DateTime(2024, 1, 1))

    for j in range(60 * 24 * 200):
        i = j + offset
        start = minute.period_start(i)
        assert i == minute.to_period(start), f"Minute {i} ({start}) failed round trip"
        assert i - 1 == minute.to_period(start - TimeDelta(seconds=1)), f"Minute {i} ({start}) failed to decrement"


def test_subdivided_hour_start_times():
    period = SubdividedPeriod(Hour(), 4)
    offset = period.to_period(DateTime(2015, 1, 1))

    for j in range(24 * 4 * 365 * 2):
        i = j + offset
        start = period.period_start(i)
        assert start.minute in [0, 15, 30, 45], f"Minute {start.minute} is not a quarter hour"
        assert i == period.to_period(start), f"Quarter hour {i} ({start}) failed round trip"
        assert i - 1 == period.to_period(start - TimeDelta(seconds=1)), f"Quarter hour {i} ({start}) failed to decrement"
