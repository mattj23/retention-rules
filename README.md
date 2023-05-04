# Retention Rules

This is a pure python library which provides the primitives for calculating retention based from a period-based policy.  The library *only* computes retention, and is not tied to any specific application.  You can use it for calculating retention for backups, files, database entries...anything with a timestamp.

For example, let's say you have some set of entities which are being produced every 15 minutes, and you want a strategy where:

* For the first 3 days, you keep one entity per every 15-minute window
* Then, up to 7 days, you want to keep one entity per hour
* Then, up to 6 weeks, you want to keep one entity per day
* Then, up to 1 year, you want to keep one entity per week
* Then, up to 20 years, you want to keep one entity per month

This library provides the constructs to set up that strategy, give it the full list of existing timestamps, and calculate which entities should be kept and which should be removed.

## Quick Start

### Installation

```bash
pip install retention-rules
```

### Usage

```python
from retention_rules import build_policy

policy = build_policy(
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
)

# You can directly use a list of datetime timestamps, or your own custom object if you provide a key function
my_objects = [...<list of objects>...]
mask = policy.check_retention(my_objects, key=lambda x: x.timestamp)

for keep, obj in zip(mask, my_objects):
    if not keep:
        print(f"This one should be removed: {obj}")
```

## Retention Rules

### Period Based vs Duration Based Retention

This library uses retention policies based on periods, rather than durations.  A period, in this context, is a stable region on a timeline.  For example, all times in which the year is the same is a period.  All times in which both the year and the month are the same is a period.  All times in which the year, month, and day are the same is a period.  And so on.

Durations, on the other hand, are built not on the calendar, but on a fixed unit of time passing.  Durations are easier to reason about in simple contexts, however they present some problems for retention policies:  

1. The duration of units of time we associate with the calendar are not fixed.  For example, the duration of a month or a year is not always the same.
2. Durations must be measured from a fixed point in time...usually the current moment, and so the results of retention policy calculations can change depending on the frequency and interval of the calculation.
3. Periods more closely match the way we think about time in a business context. We think about *which* week or *which* month, not how many weeks or months have passed.

Period based policies also have some conceptual drawbacks. One is that they change in increments.  If a policy rule applies to everything within a number of hours, then the result of the calculation will change at the top of the hour.  A policy which applies to the last three hours, for example, will only apply to events more recent than 2 hours and 1 second ago if the calculation is done at the top of the hour.  This can produce some unintuitive results if you are expecting durations.

### Periods

This library uses the following fundamental periods:

| Key   | Period | Description                                                                                            |
|-------|--------|--------------------------------------------------------------------------------------------------------|
| `Y`   | Year   | All times in which the year number is the same (for example, 2022, or 2023)                            |
| `M`   | Month  | All times in which the year and month are the same (for example, 2022-01)                              |
| `W`   | Week   | A week starts on a Sunday and ends on a Saturday                                                       |
| `D`   | Day    | All times in which the year, month, and day are the same (for example, 2022-01-01)                     |
| `H`   | Hour   | All times in which the year, month, day, and hour are the same (for example, 2022-01-01 00)            |
| `MIN` | Minute | All times in which the year, month, day, hour, and minute are the same (for example, 2022-01-01 00:00) |

Internally, the library converts any `datetime` into an integer value representing that period.  All `datetime`s which reduce to the same period integer are considered to be in the same period.  

Periods can also be subdivided, producing a new period.  For example, `H/4` is a period which is 1/4 of an hour.  Each period will start at one of the following times: zero past the hour, fifteen minutes past the hour, thirty minutes past the hour, or forty-five minutes past the hour.  Although each period has a start-to-finish duration of 15 minutes, this is not the same as an arbitrary 15-minute window.  


### Policy Rules

A `RetentionPolicy` object is built from a set of rules.  Each rule contains three pieces of information:

1. What period (years, weeks, hours, etc) is relevant for applying this rule to a timestamp? This is the text key in the `applies_for` field.
2. How many of those periods are we using to apply this rule? This is the leading integer in the `applies_for` field.
3. What period should we retain one entity for? This is the text key in the `retain_every` field.

For example, consider the following rule:

```json
{
    "applies_for": "2D",
    "retain_every": "H/4"
}
```

This rule applies to the past 2 day periods.  This means that whenever the rule is evaluated at a given time, only timestamps from the current day and the previous day will be operated on by the rule. For example, if it is 2024-05-10 00:00, then the rule will only operate on timestamps from 2024-05-10 and 2024-05-09.  That means that the earliest timestamp which would be considered by the rule will be just 24 hours ago, even though the policy looks like it is intended to apply to the past 2 days.  As the clock rolls forward, this policy will continue to only apply to the 9th and the 10th, until the stroke of midnight, at which point it will now apply to the 10th and the 11th.

The second part of the rule, `retain_every`, specifies a period which we want to preserve one timestamp from.  In this case, we want to preserve one timestamp from each 15-minute period.  This means that the rule will keep one timestamp from the 00:00-00:15 period, one timestamp from the 00:15-00:30 period, one timestamp from the 00:30-00:45 period, one timestamp from the 00:45-01:00 period, and so on through the entire 2 day `applies_to` period.

### Evaluating Retention

Retention is evaluated by the `RetentionPolicy.check_retention()` method. 

A retention policy can have multiple rules.  Rules will be automatically sorted by their approximate `applies_to` duration and executed from shortest to longest.

During evaluation, the list of events (each with a corresponding `datetime` object), begins with the assumption that *no* entities will be preserved.  Then each rule is applied in order, and each rule can mark a single event from each `retain_every` period as to-be-preserved.  Rules *do not* un-mark events, so if an event is preserved by any rule in the policy it will be preserved.



