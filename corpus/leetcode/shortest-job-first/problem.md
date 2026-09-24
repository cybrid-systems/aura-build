# Shortest Job First

## Statement

You are given `n` jobs. Job `i` takes `t[i]` units of time to run on a non-preemptive single machine. The jobs must be processed one at a time in some order, and you want to minimize the average waiting time across all jobs.

Formally, if job `i` is scheduled at position `p` (0-indexed) in the sequence, its waiting time is the sum of durations of all jobs placed before it. Minimize the sum (equivalently, the average) of these waiting times.

## Input / Output Convention

The harness feeds data directly via the `solve` function — no `STDIN` reads.

- **First argument:** a list of integers `t` (length `n`, with `1 ≤ n ≤ 200_000` and `1 ≤ t[i] ≤ 10^4`), the durations of the jobs.
- **Return:** a single `int` (or `float`) — the minimum possible total waiting time. If a float is returned, any answer within `1e-6` absolute or relative error is accepted.

### Example `CASE0` lines

```
n = 4
t = [4, 1, 3, 2]
answer = 7
```

Explanation: sort to `[1, 2, 3, 4]`; waiting times are `0, 1, 3, 6`; sum = `7` (minimum achievable).

## Function Signature

```python
def solve(t: list[int]) -> int | float:
    ...
```

## Notes

- The optimal schedule is the classic *Shortest Job First* rule: simply sort the durations in non-decreasing order.
- A naive sorting solution is `O(n log n)`, which is fast enough for the given limits.
- Be careful with very large `n`: compute the running prefix sum in a 64-bit integer (`int` in Python is unbounded; in C++/Java use `long long`).
