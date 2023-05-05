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

This section is a very brief introduction to starting with the library. For a more detailed explanation of how it works and how to use it, see the documentation below.

### Installation

This library is on PyPI, so you can install it with pip:

```bash
pip install retention-rules
```

### Usage

```python
from retention_rules import PolicyBuilder

policy = PolicyBuilder().build(
    {
        "rules": [
            {"applies_for": "3D", "retain_every": "H/4"},
            {"applies_for": "2W", "retain_every": "H"},
            {"applies_for": "M", "retain_every": "D/2"},
            {"applies_for": "6M", "retain_every": "W/2"},
            {"applies_for": "Y", "retain_every": "W"},
            {"applies_for": "10Y", "retain_every": "M"},
        ],
        "reuse": True,
        "retain": "oldest"
    }
)

# You can directly use a list of datetime timestamps, or your own custom 
# object if you provide a key function
my_objects = [...<list of objects>...]
results = policy.check_retention(my_objects, key=lambda x: x.timestamp)

# Results come back as a list of RetentionResult objects, which encapsulates 
# the original object, the retention decision, and the rule which produced 
# the decision.

for result in results:
    if result.retain:
        print(f"Keep {result.item} because of {result.rule.note}")
```

## Concepts and Methodology

This section describes the concepts and methodology used by the library.  It is not necessary to understand these concepts to use the library, but it may be helpful to understand how it works.

### Period Based vs Duration Based Retention

This library uses retention policies based on periods, rather than durations.  A period, in the context of this library, refers to a stable region on a timeline/calendar.  

For example, one type of period can be defined as all points on a timeline in which the year number is the same.  That means that concepts like "the current year", and "the previous year" refer to stable, fixed regions of time and whether a timestamp falls within that region is calculable independent of when the calculation is performed.

Durations, on the other hand, are built not on the calendar, but on a fixed unit of time passing.  Durations are easier to reason about in simple contexts, however they present some problems for retention policies:  

1. The duration of units of time we associate with the calendar are not fixed.  For example, the duration of a month or a year is not always the same.
2. Periods more closely match the way we think about time in a business context. We think about *which* week or *which* month, not how many weeks or months have passed.
3. Whether a timestamp falls into a duration can only be determined by measuring against a reference time, so retention calculations may produce different results if the intervals they were performed at were different.

To clarify the last issue, imagine a process that produces a timestamp every 10 minutes.  You would ultimately like to retain one timestamp per hour.  If you were to look back from the present moment, the set of timestamps you chose to retain would be different if you performed the check between 00:10 and 0:20 than it would be if you performed the check between 00:20 and 00:30, or 00:30 and 00:40...and so on.

By using fixed periods, such as every numeric hour, this is avoided, as the set of timestamps which fall into a given period is always the same, regardless of when the calculation is performed.

The main drawback to period based policies is that they can be more difficult to reason about initially because they change in whole increments.  That means that a policy rule which applies to two hours will apply to timestamps that happen in the current hour and the previous hour only.  As the clock moves forward from the bottom of the hour the total number of timestamps affected by the policy will grow until the top of the hour, at which point it will shrink again as the previous hour is no longer included.

### Periods

This library uses the following fundamental periods:

| Key   | Period | Description                                                                                            |
|-------|--------|--------------------------------------------------------------------------------------------------------|
| `Y`   | Year   | All times in which the year number is the same (for example, 2022, or 2023)                            |
| `M`   | Month  | All times in which the year and month are the same (for example, 2022-01)                              |
| `W`   | Week   | A week starts on a Monday 00:00:00 and ends on a Sunday 23:59:59.9999...                               |
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
{ "applies_for": "2D", "retain_every": "H/4" }
```

This rule applies to the past 2 *day* periods.  This means that whenever the rule is evaluated at a given time, only timestamps from the current day and the previous day will be operated on by the rule. For example, if it is 2024-05-10 00:00, then the rule will only operate on timestamps from 2024-05-10 and 2024-05-09.  That means that the earliest timestamp which would be considered by the rule will be just 24 hours ago, even though the policy looks like it is intended to apply to the past 2 days.  As the clock rolls forward, this policy will continue to only apply to the 9th and the 10th, until the stroke of midnight, at which point it will now apply to the 10th and the 11th.

The second part of the rule, `retain_every`, specifies a period which we want to preserve one timestamp from.  In this case, we want to preserve one timestamp from each 15-minute period.  This means that the rule will keep one timestamp from the 00:00-00:15 period, one timestamp from the 00:15-00:30 period, one timestamp from the 00:30-00:45 period, one timestamp from the 00:45-01:00 period, and so on through the entire 2 day `applies_to` period.

***Note:** This is a good place to clarify the difference between an applies-for period with multiple counts and an equivalent larger period.  For example, `7D` is conceptually not the same as `1W`. The former refers to 7x 1-day periods, starting with the current day.  At midnight every night, the rule will start applying to the current new day and stop applying to the day 7 days ago.  On the other hand, `1W` refers to all timestamps in the current week. This will not change until midnight on Sunday, when it will no longer apply to timestamps from even a few seconds ago.*

### Evaluating Retention

Retention is evaluated by the `RetentionPolicy.check_retention()` method. 

A retention policy can have multiple rules.  Rules will be automatically sorted by their approximate `applies_to` duration and executed from shortest to longest.

During evaluation, the list of events (each with a corresponding `datetime` object), begins with the assumption that *no* entities will be preserved.  Then each rule is applied in order, and each rule can mark a single event from each `retain_every` period as to-be-preserved.  Rules *do not* un-mark events, so if an event is preserved by any rule in the policy it will be preserved.

The evaluation of each rule works the following way:

1. First, the applies-to period for the current rule is calculated by taking the current period and subtracting the number of counts.  For example, `4D` refers to the past four 1-day periods, including the current day which is not yet complete.
2. Next, all timestamps within the applies-to period are identified and set aside as being subject to the rule.
3. All the relevant timestamps are then grouped by the retain-every period, so each group contains every timestamp from a given retain-every period.  For example, if the retain-every period was `H`, then every timestamp between 00:00 and 01:00 would be in one group, every timestamp between 01:00 and 02:00 would be in another group, and so on.
4. For each group, the rule will ensure that at least one timestamp will be preserved.  It does this based on the following settings:
   1. If `reuse` is set to `True`, the rule will first check if there is *already* a timestamp in this group which has been marked for preservation from an earlier rule.  If so, it will not mark any additional timestamps in this group.  *This will generally only have an effect when the applies-to periods of rules do not share boundaries, such as with weeks and months.*
   2. Otherwise, the rule will choose a timestamp based on the `retain` strategy.  The default is `oldest`, which preserves the first timestamp in the group.  By using `newest` the rule will instead preserve the most recent timestamp in the group.  If `reuse` was set to `False`, there is a chance that the rule will select a timestamp which was already marked for preservation by an earlier rule. In this case, the rule will not select a different timestamp.

Once all rules have been processed, the list of events is returned.

## Library Usage

This library is meant to be straightforward to use, but to provide constructs to modify and extend its behavior. This section will cover the main ways to use it, while the [Development](#development) section will cover complex use cases and extension in more detail.

### Creating a Policy

The `RetentionPolicy` class is the main feature for using the library.  It can be instantiated either directly, or by using the `PolicyBuilder` class. 

The `PolicyBuilder` class is the normal way to build a policy, as it will take a python dictionary of primitive types (directly serializable from JSON or YAML) and build it into a `RetentionPolicy` object.  This is a class which must be instantiated to be used, because it contains in its internal state a dictionary which maps a shortened text representation of periods to their corresponding `Period` objects.  This dictionary can be modified on the instance to add new periods.

```python
from retention_rules import PolicyBuilder

config = {
    "rules": [
        {"applies_for": "3D", "retain_every": "H/4", "note": "First 3d every 15min"},
        # ...
        {"applies_for": "10Y", "retain_every": "M"},
    ],
    "reuse": True,
    "retain": "oldest"
}

policy = PolicyBuilder().build(config)
```

Currently, the configuration dictionary consists of three parts:

1. The `"rules"` key, which is a list of retention rules as described in [Policy Rules](#policy-rules) with text keys described [Periods](#periods).
2. The `"reuse"` key, which is a boolean value indicating whether this rule would be satisfied by a timestamp *already* marked for preservation by a previous rule in one of the `retain_every` periods. This will only matter when there are multiple rules with different `retain_every` periods which do not always share boundaries, like weeks and month.  The default is `False`, which will occasionally result in some extra timestamps being preserved in the short term.
3. The `"retain"` key, which is a string value indicating which timestamp in each `retain_every` period should be preserved.  The default is `"oldest"`, which will preserve the first timestamp in each period.  The other option is `"newest"`, which will preserve the most recent timestamp in each period.

### Evaluating a Policy

Once created, a policy can be evaluated by passing the `check_retention(...)` method a list of timestamps...

```python
from datetime import datetime
timestamps = [datetime(2022, 1, 10, 1, 0),
                # ...
              datetime(2022, 1, 10, 1, 30)]

results = policy.check_retention(timestamps)
```

...or a list of custom objects with a `Callable` that extracts a timestamp from the object:

```python
@dataclass
class MyBackupFile:
    file_path: str
    timestamp: datetime
    
my_objects: MyBackupFile = [ ... ]
results = policy.check_retention(my_objects, key=lambda x: x.timestamp)
```

Additionally, the `check_retention(...)` method can be passed a `datetime` object to use as the current time.  This is useful for testing, or for evaluating a policy for a time in the past or future.

```python
results = policy.check_retention(my_objects, key=lambda x: x.timestamp, now=datetime(2022, 1, 10, 1, 0))
```

### Evaluating the Results

The `check_retention(...)` method returns a list of `RetentionResult` objects.  These objects belong to the following dataclass:

```python
@dataclass
class RetentionResult:
   time: DateTime
   retain: bool
   item: Any
   rule: Optional[PolicyRule]
```

The `time` field is the timestamp which was extracted from the object.  The `retain` field is the result of the computation, specifying whether or not the object shoudl be retained.  If it is true, the `rule` field will contain the `PolicyRule` object which first marked it for retention.  The `item` field is the original object which was passed to the `check_retention(...)` method.

The `PolicyRule` has a `note` field which is filled out if the rule was created by the `PolicyBuilder` object. If a custom note was included in the configuration dictionary it will be the value here, otherwise a default one was generated by the `PolicyBuilder` from the text of the `applies_to` and `retain_every` fields.

## Development

This section covers information for developers looking to extend the library or use it in more complex ways.

### Periods

Periods inherit from the `Period` class and are the fundamental time structure in this library.  The following periods are built in and can be found in the `retention_rules.periods` module: `Year`, `Month`, `Week`, `Day`, `Hour`, and `Minute`.

Ultimately, a period must perform the following three functions:

1. It must be able to convert an arbitrary `datetime.datetime` object into an integer.  This integer must relate to a unique period on the calendar so that all timestamps in the same period will convert to the same integer.  This integer must also have the property that when a clock is advanced by an arbitrarily small amount of time, the integer will *either* stay the same, *or* advance by exactly one.
2. It must be able to convert the integer back into a `datetime.datetime` object which represents the beginning of the period.
3. It must be able to specify a duration (`datetime.timedelta`) which represents a safe *maximum* length for the period. For instance, no year is longer than 366 days, so the `Year` period specifies a duration of 366 days.  No month is longer than 31 days, so the `Month` period specifies a duration of 31 days.  The more accurate these durations are the better, but they are primarily used for sorting and testing.

Implementing a new period consists of implementing these three features, nothing else is currently required.

The current implementation of the `Period` class is as follows:

```python
from abc import ABC
from datetime import datetime as DateTime, timedelta as TimeDelta

class Period(ABC):
   def to_period(self, time_stamp: DateTime) -> int:
      """Converts a time_stamp into an integer representing the period of time it is in"""
      raise NotImplementedError()

   def period_start(self, period: int) -> DateTime:
      """Returns the start time of the period"""
      raise NotImplementedError()

   def max_duration(self) -> TimeDelta:
      """Returns the maximum duration of the period"""
      raise NotImplementedError()
```

### The Policy Builder

If a new period is implemented, the `PolicyBuilder` class can still be used to instantiate it by registering it with the `PolicyBuilder.keys` dictionary.  The dictionary can also be rebuilt with different text keys if desired.

```python
class Quarter(Period):
   pass

builder = PolicyBuilder()
builder.keys["Q"] = Quarter

policy = builder.build(config)
```