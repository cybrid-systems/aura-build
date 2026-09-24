# Moving Average from Data Stream

## Problem

You are given a data stream of integers arriving one at a time, together with a fixed window size `k`. Implement a structure that supports the following operations:

- `next(value)` — append a new integer `value` to the stream and return the average of the last `k` values seen so far. If fewer than `k` values have been seen, average over all values seen so far.
- `get_average()` — return the average of the last `k` values currently stored, or over all values stored if there are fewer than `k`.

The average is defined as `sum_of_values / count_of_values` (the count is `min(k, total_seen)`).

Your implementation must process each `next` call in **O(1)** amortized time.

## Function Signature

```
(defn solve [ops]
  ;; ops is a vector of operations.
  ;; Returns a vector of results for query operations.
  ...)
```

Where `ops` is a sequence of operation tokens:

- `["M" k]` — operations of size `k`. Must be the first op (constructor).
- `["N" v]` — `next(v)`, returns the current moving average (truncated to integer).
- `["G"]`   — `get_average()`, returns the current moving average (truncated to integer).

The first op is always `["M", k]` which sets up the window size. There is no explicit "constructor" output; subsequent `N` and `G` operations each produce one output value.

## I/O Convention

Input is provided as lines on stdin in the form:

```
CASE0=N op1 op2 ...
```

For example:

```
CASE0=M 3
CASE0=N 1
CASE0=N 10
CASE0=N 3
CASE0=G
CASE0=N 5
```

Means: window size `k = 3`, then `next(1) → 1`, `next(10) → 5`, `next(3) → 4`, `get_average() → 4`, `next(5) → 6`.

Each `N` or `G` produces one integer in the output list, in order. If the harness runs multiple `CASE0=` blocks, concatenate results in the same order.

Output one integer per line on stdout.

## Notes

- Truncate (floor toward zero) when converting the average to an integer.
- Use a queue (FIFO) of length up to `k` plus a running sum to achieve O(1) amortized per operation.
- The data stream may be empty when `get_average` is called; in that case output `0`.
