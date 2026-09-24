# Time Based Key-Value Store

## Problem Statement

Design a data structure that supports storing multiple values for the same key, where each value is associated with a timestamp, and retrieving the value of a key at or before a given timestamp.

Implement a `TimeMap` class with the following methods:

- `set(string key, string value, int timestamp)` — Stores the `key` with `value` at the given `timestamp`.
- `get(string key, int timestamp)` — Returns the most recent `value` associated with `key` whose timestamp is less than or equal to `timestamp`. If there is no such value, return an empty string `""`.

**Note:** For each key, timestamps passed to `set` are strictly increasing (i.e., they arrive in sorted order). However, `get` queries can arrive in any order.

## Function Signature

```python
class TimeMap:
    def __init__(self):
        ...

    def set(self, key: str, value: str, timestamp: int) -> None:
        ...

    def get(self, key: str, timestamp: int) -> str:
        ...
```

## I/O Convention (Aura Harness)

The harness reads a script of operations from a single block. The first line specifies the number of operations `N`. Each subsequent line is one of:

- `SET key value timestamp` — invoke `set(key, value, timestamp)`.
- `GET key timestamp` — invoke `get(key, timestamp)` and emit the result.

Output the result of each `GET` query on its own line.

### Example

**CASE0=**
```
7
SET foo bar 1
GET foo 1
GET foo 3
SET foo bar2 4
GET foo 4
GET foo 5
GET foo 0
```

**Expected Output:**
```
bar

bar2
bar2

```

## Notes

- Each `key` should maintain its values in timestamp order, allowing efficient lookup of the latest value at or before a query timestamp via binary search.
- A clean approach stores, per key, two parallel arrays: one of timestamps and one of corresponding values. Since `set` timestamps are strictly increasing for a key, appending is O(1), and `get` runs a binary search over the timestamps to find the greatest one ≤ the query timestamp.
