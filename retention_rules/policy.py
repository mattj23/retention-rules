from dataclasses import dataclass
from enum import Enum
from .periods import Period
from datetime import datetime as DateTime
from typing import List, Optional, Any, Callable


class RetainStrategy(Enum):
    OLDEST = "oldest"
    NEWEST = "newest"


@dataclass
class PolicyRule:
    applies_for: Period
    applies_period_count: int
    retain_every: Period
    note: Optional[str] = None


@dataclass
class _Result:
    index: int
    retain: bool
    time: DateTime


@dataclass
class RetentionResult:
    time: DateTime
    retain: bool
    item: Any
    rule: Optional[PolicyRule]


class RetentionPolicy:
    def __init__(self, **kwargs):
        """
        :param rules: A list of PolicyRule objects

        :param retain_strategy: The strategy to use to decide which items to retain. When a retain-every period has more
            than one item in it (for example, in a retain-every hour rule there may be multiple items from a single
            hour, and we only want to retain one of the) this determines which gets kept.

        :param reuse_in_group: If a retain-every period already has an item marked to be retained from a previous rule,
            should we re-use that item for the current rule? If True, we will skip the retain_strategy logic and move
            on, since we already know that at least one item in this period will be retained.  If False, we will use
            the retain_strategy to determine which gets kept, which may or may not end up being the same as the item
            already marked to keep.
        """
        self.rules: List[PolicyRule] = kwargs.get("rules", [])
        self.retain_strategy: RetainStrategy = kwargs.get("retain_strategy", RetainStrategy.OLDEST)
        self.reuse_in_group: bool = kwargs.get("reuse_in_group", False)
        self._update()

    def _update(self):
        self.rules.sort(key=lambda l: l.applies_for.max_duration() * l.applies_period_count)

    def add_rule(self, applies_for: Period, applies_period_count: int, retain_every: Period,
                 note: Optional[str] = None):
        """ Adds a rule to the policy. """
        self.rules.append(PolicyRule(applies_for, applies_period_count, retain_every, note))
        self._update()

    def check_retention(self, items: List[Any],
                        key: Optional[Callable[[Any], DateTime]] = None,
                        now: Optional[DateTime] = None) -> List[RetentionResult]:
        """ Checks if the given time_stamps are to be retained according to the policy. """
        now = now or DateTime.now()
        results = _prepare_working(items, key)

        # We will iterate through each layer and mutate the results as we go. Layers will be able to mark a result as
        # to be retained, but will not un-mark something which has already been marked.
        for rule in self.rules:
            # Get the integer of the current rule's applies-to period, then calculate the smallest period integer which
            # the current rule will apply to.
            this_period = rule.applies_for.to_period(now)
            applies_period = this_period - rule.applies_period_count + 1

            # Find the items which are within the same applies-to period range as the current time
            applicable_items = [x for x in results if rule.applies_for.to_period(x.time) >= applies_period]

            # Now we will group the applicable items by the retain-every period that they fall in
            grouped = _group_items_by_period(applicable_items, rule.retain_every)

            # Now we will iterate through the groups and determine which item should be retained
            for item_group in grouped:
                if self.reuse_in_group and any(x.retain for x in item_group):
                    # If we are re-using items in a group, we will first check if any of the items are already marked
                    # to be retained. If so, we can safely skip doing anything to this group
                    continue

                if self.retain_strategy == RetainStrategy.OLDEST:
                    # If we are retaining the oldest (first) item, we will mark the minimum time-stamp item
                    to_retain = min(item_group, key=lambda x: x.time)
                    if not to_retain.retain:
                        to_retain.retain = True
                        to_retain.rule = rule

                elif self.retain_strategy == RetainStrategy.NEWEST:
                    # If we are retaining the newest (last) item, we will mark the maximum time-stamp item
                    to_retain = max(item_group, key=lambda x: x.time)
                    if not to_retain.retain:
                        to_retain.retain = True
                        to_retain.rule = rule

        # Finally, we will return the results
        return results


def _group_items_by_period(items: List[RetentionResult], period: Period) -> List[List[RetentionResult]]:
    """ Groups the given items by the given period. """
    grouped_items = {}
    for item in items:
        i = period.to_period(item.time)
        if i not in grouped_items:
            grouped_items[i] = []
        grouped_items[i].append(item)
    return list(grouped_items.values())


def _prepare_working(items: List[Any], key: Optional[Callable[[Any], DateTime]] = None) -> List[RetentionResult]:
    """ Prepares the given items for processing by the policy. """
    key = key or (lambda x: x)

    # Validate that we are getting datetime objects
    time_stamps = []
    for item in items:
        time_stamp = key(item)
        if not isinstance(time_stamp, DateTime):
            raise TypeError(f"Could not get a datetime from the {item} item, instead got: {type(time_stamp)}")
        time_stamps.append(time_stamp)

    return [RetentionResult(time_stamp, False, item, None) for time_stamp, item in zip(time_stamps, items)]
