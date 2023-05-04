from datetime import datetime as DateTime
from retention_rules.periods import Minute, Hour, Day, Week, Month, Year
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
