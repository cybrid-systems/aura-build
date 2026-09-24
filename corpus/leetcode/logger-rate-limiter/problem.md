# Logger Rate Limiter

## Problem Statement

Design a logger system that receives a stream of messages along with the timestamp (in seconds) at which each message arrives. For every incoming message, the system must decide whether to print it.

A message should be printed if **it has not been printed in the last 10 seconds** (i.e., no identical message was logged at a timestamp `t` where `current_timestamp - 10 < t ≤ current_timestamp`). If the same message was printed within that 10-second window, the new occurrence is suppressed.

Implement a class/structure that supports the following operations:

- Initialize the logger.
- For each incoming `(timestamp, message)` pair, return `true` if the message should be printed, or `false` if it should be suppressed.

The timestamps are strictly non-decreasing, but messages can arrive in any order of content.

## Function Signature

```python
class Logger:
    def __init__(self):
        ...

    def shouldPrintMessage(self, timestamp: int, message: str) -> bool:
        ...
```

## Input / Output Convention

The harness invokes your `Logger` directly, but the problem is expressed as a sequence of queries:

```
CASE0=5
INIT
SHOULD_PRINT 1 "foo"
SHOULD_PRINT 2 "bar"
SHOULD_PRINT 3 "foo"
SHOULD_PRINT 8 "foo"
SHOULD_PRINT 10 "foo"
SHOULD_PRINT 11 "foo"
```

- Lines beginning with `INIT` indicate a fresh logger instance.
- `SHOULD_PRINT <timestamp> "<message>"` calls `shouldPrintMessage(timestamp, message)` and expects `true`/`false`.
- Lines beginning with `CASE0=` describe the number of subsequent operations (used by the grader for sanity checks).

### Example

```
INIT
SHOULD_PRINT 1 "foo"   -> true   (first occurrence)
SHOULD_PRINT 2 "bar"   -> true   (different message)
SHOULD_PRINT 3 "foo"   -> false  (foo printed 2s ago)
SHOULD_PRINT 8 "foo"   -> false  (foo printed 7s ago)
SHOULD_PRINT 10 "foo"  -> false  (foo printed 9s ago, still within 10s window)
SHOULD_PRINT 11 "foo"  -> true   (foo last printed at t=1, now 11-1=10 > window)
```

## Notes

- Use a hash map from `message` → last printed timestamp for **O(1)** average-time decisions.
- A message is allowed to be reprinted as soon as the gap from its previous print exceeds 10 seconds.
- Timestamps can be large; no assumptions are made about an upper bound other than fitting in a standard integer.
- The structure only needs to store the most recent timestamp per unique message, not a full history.
