"""
    Tests to check the policy building
"""
from typing import Tuple

from retention_rules.builder import PolicyBuilder
from retention_rules.periods import Period, Year, Month, Week, Day, Hour, Minute, SubdividedPeriod


def test_parse_simple():
    assert parse_period_text("Y") == _Check(Year(), 1)
    assert parse_period_text("M") == _Check(Month(), 1)
    assert parse_period_text("W") == _Check(Week(), 1)
    assert parse_period_text("D") == _Check(Day(), 1)
    assert parse_period_text("H") == _Check(Hour(), 1)
    assert parse_period_text("MIN") == _Check(Minute(), 1)


def test_parse_with_count():
    assert parse_period_text("2Y") == _Check(Year(), 2)
    assert parse_period_text("2M") == _Check(Month(), 2)
    assert parse_period_text("2W") == _Check(Week(), 2)
    assert parse_period_text("2D") == _Check(Day(), 2)
    assert parse_period_text("2H") == _Check(Hour(), 2)
    assert parse_period_text("2MIN") == _Check(Minute(), 2)


def test_parse_with_sub_div():
    assert parse_period_text("Y/2") == _Check(SubdividedPeriod(Year(), 2), 1)
    assert parse_period_text("M/2") == _Check(SubdividedPeriod(Month(), 2), 1)
    assert parse_period_text("W/2") == _Check(SubdividedPeriod(Week(), 2), 1)
    assert parse_period_text("D/2") == _Check(SubdividedPeriod(Day(), 2), 1)
    assert parse_period_text("H/2") == _Check(SubdividedPeriod(Hour(), 2), 1)
    assert parse_period_text("MIN/2") == _Check(SubdividedPeriod(Minute(), 2), 1)


def test_parse_with_count_and_sub_div():
    assert parse_period_text("3Y/2") == _Check(SubdividedPeriod(Year(), 2), 3)
    assert parse_period_text("3M/2") == _Check(SubdividedPeriod(Month(), 2), 3)
    assert parse_period_text("3W/2") == _Check(SubdividedPeriod(Week(), 2), 3)
    assert parse_period_text("3D/2") == _Check(SubdividedPeriod(Day(), 2), 3)
    assert parse_period_text("3H/2") == _Check(SubdividedPeriod(Hour(), 2), 3)
    assert parse_period_text("3MIN/2") == _Check(SubdividedPeriod(Minute(), 2), 3)


def parse_period_text(text: str):
    b = PolicyBuilder()
    return b._parse_key_text(text)


class _Check:
    def __init__(self, period, count: int):
        self.period = period
        self.count = count

    def __eq__(self, other: Tuple[Period, int]):
        if isinstance(other[0], SubdividedPeriod):
            if not isinstance(self.period, SubdividedPeriod):
                return False
            return (isinstance(other[0]._sub_period, type(self.period._sub_period))
                    and other[0]._sub_div == self.period._sub_div
                    and other[1] == self.count)
        return isinstance(other[0], type(self.period)) and other[1] == self.count
