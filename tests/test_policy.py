from datetime import datetime as DateTime
from retention_rules.periods import Minute, Hour, Day, Week, Month, Year, SubdividedPeriod
from retention_rules.policy import RetentionPolicy


def test_simple_policy():
    policy = RetentionPolicy()
    policy.add_rule(Day(), 1, Hour())
    policy.add_rule(Week(), 1, Day())

    raw_data = [
        ('2020-01-01 00:00:00', True),
        ('2020-01-01 00:30:00', False),
        ('2020-01-01 01:00:00', True),
        ('2020-01-01 01:30:00', False),
        ('2020-01-01 02:00:00', True),
        ('2020-01-01 02:30:00', False),
        ('2020-01-01 03:00:00', True),
        ('2020-01-01 03:30:00', False),
        ('2020-01-01 04:00:00', True),
        ('2020-01-01 04:30:00', False),
        ('2020-01-01 05:00:00', True),
        ('2020-01-01 05:30:00', False),
        ('2020-01-01 06:00:00', True),
        ('2020-01-01 06:30:00', False),
        ('2020-01-01 07:00:00', True),
        ('2020-01-01 07:30:00', False),
        ('2020-01-01 08:00:00', True),
        ('2020-01-01 08:30:00', False),
        ('2020-01-01 09:00:00', True),
        ('2020-01-01 09:30:00', False),
    ]

    data = [(DateTime.strptime(t, "%Y-%m-%d %H:%M:%S"), v) for t, v in raw_data]
    mask = policy.check_retention(data, key=lambda x: x[0], now=DateTime(2020, 1, 1, 10, 0, 0))
    for i, (t, v) in enumerate(data):
        assert mask[i] == v, f"Mask at index {i} should be {v} but was {mask[i]}"


def test_simple_applies_for_count():
    """ This is a slightly more complicated test. The current time is 3:20, and the applies-to period is an
    hour with a count of 2.  The retain-every period is 15 minutes.

    Because it's 3:20 the current hour is 3 and the previous hour is 2, so only timestamps from those hours will
    be considered.  Then, only timestamps that come immediately on or after :00, :15, :30, and :45 will be retained.
    """
    policy = RetentionPolicy()
    policy.add_rule(Hour(), 2, SubdividedPeriod(Hour(), 4))

    raw_data = [
        ('2020-01-01 00:00:00', False),
        ('2020-01-01 00:10:00', False),
        ('2020-01-01 00:20:00', False),
        ('2020-01-01 00:30:00', False),
        ('2020-01-01 00:40:00', False),
        ('2020-01-01 00:50:00', False),
        ('2020-01-01 01:00:00', False),
        ('2020-01-01 01:10:00', False),
        ('2020-01-01 01:20:00', False),
        ('2020-01-01 01:30:00', False),
        ('2020-01-01 01:40:00', False),
        ('2020-01-01 01:50:00', False),
        ('2020-01-01 02:00:00', True),
        ('2020-01-01 02:10:00', False),
        ('2020-01-01 02:20:00', True),
        ('2020-01-01 02:30:00', True),
        ('2020-01-01 02:40:00', False),
        ('2020-01-01 02:50:00', True),
        ('2020-01-01 03:00:00', True),
        ('2020-01-01 03:10:00', False),
    ]

    data = [(DateTime.strptime(t, "%Y-%m-%d %H:%M:%S"), v) for t, v in raw_data]
    mask = policy.check_retention(data, key=lambda x: x[0], now=DateTime(2020, 1, 1, 3, 20, 0))
    for i, (t, v) in enumerate(data):
        assert mask[i] == v, f"Mask at index {i} ({raw_data[i][0]}) should be {v} but was {mask[i]}"
