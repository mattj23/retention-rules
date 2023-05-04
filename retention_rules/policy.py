from dataclasses import dataclass
from .periods import Period
from datetime import datetime as DateTime
from typing import List, Optional, Any, Callable


@dataclass
class PolicyRule:
    applies_for: Period
    applies_period_count: int
    retain_every: Period


@dataclass
class _Result:
    index: int
    retain: bool
    time: DateTime


class RetentionPolicy:
    def __init__(self, layers: Optional[List[PolicyRule]] = None):
        self._layers = layers or []
        self._update()

    def _update(self):
        self._layers.sort(key=lambda l: l.applies_for.max_duration() * l.applies_period_count)

    def add_rule(self, applies_for: Period, applies_period_count: int, retain_every: Period):
        self._layers.append(PolicyRule(applies_for, applies_period_count, retain_every))
        self._update()

    def check_retention(self, items: List[Any],
                        key: Optional[Callable[[Any], DateTime]] = None,
                        now: Optional[DateTime] = None) -> List[bool]:
        """ Checks if the given time_stamps are to be retained according to the policy. """
        now = now or DateTime.now()

        # Construct the results
        key = key or (lambda x: x)
        results = [_Result(index, False, key(item) if key else now) for index, item in enumerate(items)]

        # We will iterate through each layer and mutate the results as we go. Layers will be able to mark a result as
        # to be retained, but will not un-mark something which has already been marked.
        for layer in self._layers:
            # Get the integer of the current layer's applies-to period
            now_period = layer.applies_for.to_period(now)

            # Find the items which are in the same applies-to period as the current time
            period_items = [item for item in results if
                            layer.applies_for.to_period(item.time) >= now_period - layer.applies_period_count + 1]

            # Now we will group the items by the retain-every period
            groups = {}
            for item in period_items:
                retain_period = layer.retain_every.to_period(item.time)
                if retain_period not in groups:
                    groups[retain_period] = []
                groups[retain_period].append(item)

            # Now we will iterate through the groups and mark the first item in each group as to be retained
            for group in groups.values():
                min(group, key=lambda x: x.time).retain = True

        # Finally, we will return the results
        return [x.retain for x in results]
