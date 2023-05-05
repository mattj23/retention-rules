from datetime import datetime as DateTime
from retention_rules.periods import Minute, Hour, Day, Week, Month, Year, SubdividedPeriod
from retention_rules.policy import RetentionPolicy, RetainStrategy


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

    for condition, message in _test_loop(raw_data, policy, DateTime(2020, 1, 1, 10, 0, 0)):
        assert condition, message


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

    for condition, message in _test_loop(raw_data, policy, DateTime(2020, 1, 1, 3, 20, 0)):
        assert condition, message


def test_simple_strategy_newest():
    """ This test is similar to the previous one, but the strategy is newest.  This means that the newest timestamp
    in each retain period will be kept. """
    policy = RetentionPolicy(retain_strategy=RetainStrategy.NEWEST)
    policy.add_rule(Hour(), 2, SubdividedPeriod(Hour(), 4))

    raw_data = [
        ('2020-01-01 01:20:00', False),
        ('2020-01-01 01:30:00', False),
        ('2020-01-01 01:40:00', False),
        ('2020-01-01 01:50:00', False),
        ('2020-01-01 02:00:00', False),
        ('2020-01-01 02:10:00', True),
        ('2020-01-01 02:20:00', True),
        ('2020-01-01 02:30:00', False),
        ('2020-01-01 02:40:00', True),
        ('2020-01-01 02:50:00', True),
        ('2020-01-01 03:00:00', False),
        ('2020-01-01 03:10:00', True),
    ]

    for condition, message in _test_loop(raw_data, policy, DateTime(2020, 1, 1, 3, 20, 0)):
        assert condition, message


def test_simple_strategy_reuse_off():
    policy = RetentionPolicy(reuse_in_group=False, retain_strategy=RetainStrategy.OLDEST)
    policy.add_rule(Week(), 1, Day())
    policy.add_rule(Month(), 1, SubdividedPeriod(Week(), 2))

    # Using the oldest strategy, the first timestamp for each day will be retained.  However, the second rule
    # breaks the week in half at 12:00 on the 4th, so the oldest timestamp for the second half of the week will be
    # the one at 17:00 on the 4th.  With reuse off, the second rule will choose to also retain the 17:00 timestamp
    # on the 5th
    raw_data = [
        ('2023-05-04 01:00:00', True),
        ('2023-05-04 17:00:00', True),
        ('2023-05-05 01:00:00', True),
        ('2023-05-05 17:00:00', False),
    ]
    for condition, message in _test_loop(raw_data, policy, DateTime(2023, 5, 5, 18, 0, 0)):
        assert condition, message


def test_simple_strategy_reuse_on():
    policy = RetentionPolicy(reuse_in_group=True, retain_strategy=RetainStrategy.OLDEST)
    policy.add_rule(Week(), 1, Day())
    policy.add_rule(Month(), 1, SubdividedPeriod(Week(), 2))

    # Using the oldest strategy, the first timestamp for each day will be retained.  However, the second rule
    # breaks the week in half at 12:00 on the 4th, so the oldest timestamp for the second half of the week will be
    # the one at 17:00 on the 4th.  With retain on, the second rule will accept the 01:00 timestamp on the 5th and
    # not additionally mark the 17:00 timestamp on the 4th.
    raw_data = [
        ('2023-05-04 01:00:00', True),
        ('2023-05-04 17:00:00', False),
        ('2023-05-05 01:00:00', True),
        ('2023-05-05 17:00:00', False),
    ]
    for condition, message in _test_loop(raw_data, policy, DateTime(2023, 5, 5, 18, 0, 0)):
        assert condition, message


def test_policy_rule_setting():
    """ Test that a policy rule is set on a result item """
    policy = RetentionPolicy(retain_strategy=RetainStrategy.OLDEST, reuse_in_group=False)
    policy.add_rule(Day(), 1, Hour())
    policy.add_rule(Week(), 1, Day())

    raw_data = [
        ('2023-05-04 01:00:00', True),
        ('2023-05-04 01:05:00', False),
    ]

    r0, r1 = _get_results(raw_data, policy, DateTime(2023, 5, 4, 18))
    assert r0.rule == policy.rules[0]
    assert r1.rule is None


def _get_results(raw_data, policy, now):
    data = [(DateTime.strptime(t, "%Y-%m-%d %H:%M:%S"), v) for t, v in raw_data]
    return policy.check_retention(data, key=lambda x: x[0], now=now)


def _test_loop(raw_data, policy, now):
    for v in _get_results(raw_data, policy, now):
        yield v.item[1] == v.retain, f"Item ({v.time.strftime('%Y-%m-%d %H:%M:%S')}) should be " \
                                     f"{v.item[1]} but was {v.retain}"
