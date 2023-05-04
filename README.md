# Retention Rules

This is a pure python library which provides the primitives for calculating retention based from a period-based policy.  The library *only* computes retention, and is not tied to any specific application.  You can use it for calculating retention for backups, files, database entries...anything with a timestamp.

For example, let's say you have some set of entities which are being produced every 15 minutes, and you want a strategy where:

* For the first 3 days, you keep one entity per every 15-minute window
* Then, up to 7 days, you want to keep one entity per hour
* Then, up to 6 weeks, you want to keep one entity per day
* Then, up to 1 year, you want to keep one entity per week
* Then, for the rest of time, you want to keep one entity per month

This library provides the constructs to set up that strategy, give it the full list of existing timestamps, and calculate which entities should be kept and which should be removed.

