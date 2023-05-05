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
        ],
        "retain": "oldest",
        "reuse": True
    }

"""

import re
from typing import Dict, Tuple, Callable

from .policy import RetentionPolicy, RetainStrategy
from .periods import *


class PolicyBuilder:
    def __init__(self, **kwargs):
        self.keys: Dict[str, Callable[[], Period]] = kwargs.get("keys", _by_key)

    def build(self, policy_dict: Dict) -> RetentionPolicy:
        retain = RetainStrategy(policy_dict.get("retain", "oldest"))
        reuse = policy_dict.get("reuse", False)
        policy = RetentionPolicy(retain_strategy=retain, reuse_in_group=reuse)

        rule_items = policy_dict.get("rules", [])
        if not rule_items:
            raise ValueError("Policy must contain at least one rule in the 'rules' key")

        for rule in rule_items:
            applies_text = rule["applies_for"]
            retain_text = rule["retain_every"]

            applies, count = self._parse_key_text(applies_text)
            retain_every, rcount = self._parse_key_text(retain_text)
            if rcount != 1:
                raise ValueError(f"Retain-every does not currently support a count")

            note = rule.get("note", None) or f"{applies_text} retain {retain_text}"
            policy.add_rule(applies, count, retain_every, note)

        return policy

    def _parse_key_text(self, text: str):
        match = _key_pattern.match(text)
        if not match:
            raise ValueError(f"Invalid specifier: {text}")

        count = int(match.group(1) or 1)
        unit_key = match.group(2)
        sub_div = match.group(3)

        period_cls = self.keys.get(unit_key, None)
        if not period_cls:
            raise ValueError(f"PolicyBuilder could not find a period associated with the key: {unit_key}")

        period = period_cls()
        if sub_div:
            period = SubdividedPeriod(period, int(sub_div[1:]))

        return period, count


_key_pattern = re.compile(r"^(\d+)?(\w+)(/\d+)?$")

_by_key = {
    "Y": Year,
    "M": Month,
    "W": Week,
    "D": Day,
    "H": Hour,
    "MIN": Minute,
}
