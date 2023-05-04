"""
    This module converts python dictionaries into a policy object.

    A dictionary will look something like this:

    {
        "rules": [
            {"applies_for": "3D", "retain_every": "H/4"},
            {"applies_for": "2W", "retain_every": "H"},
            {"applies_for": "M", "retain_every": "D/2"},
            {"applies_for": "6M", "retain_every": "W/2"},
            {"applies_for": "Y", "retain_every": "W"},
            {"applies_for": "10Y", "retain_every": "M"},
        ]
    }

"""

import re
from typing import Dict, Tuple

from .policy import RetentionPolicy
from .periods import *


def build_policy(policy_dict: Dict) -> RetentionPolicy:
    policy = RetentionPolicy()
    rule_items = policy_dict.get("rules", [])
    if not rule_items:
        raise ValueError("Policy must contain at least one rule in the 'rules' key")

    for rule in rule_items:
        applies, count = parse_period_text(rule["applies_for"])
        retain_every, rcount = parse_period_text(rule["retain_every"])
        if rcount != 1:
            raise ValueError(f"Retain-every does not currently support a count")

        policy.add_rule(applies, count, retain_every)
    return policy


_key_pattern = re.compile(r"^(\d+)?(Y|M|W|D|H|MIN|S)(/\d+)?$")

_by_key = {
    "Y": Year,
    "M": Month,
    "W": Week,
    "D": Day,
    "H": Hour,
    "MIN": Minute,
}


def parse_period_text(text: str) -> Tuple[Period, int]:
    match = _key_pattern.match(text)
    if not match:
        raise ValueError(f"Invalid period: {text}")

    count = int(match.group(1) or 1)
    unit = match.group(2)
    sub_div = match.group(3)

    period_cls = _by_key.get(unit, None)
    if not period_cls:
        raise ValueError(f"Could not find period for unit: {unit}")

    period = period_cls()
    if sub_div:
        period = SubdividedPeriod(period, int(sub_div[1:]))
    return period, count
