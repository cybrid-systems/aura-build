# Longest Harmonious Subsequence

## Problem

We define a sequence to be **harmonious** if the absolute difference between the maximum value and the minimum value in it is exactly `1`. Equinumerous values (e.g., values that differ by more than `1`, or a sequence consisting of a single distinct value) are **not** harmonious.

Given a sequence `a` of `n` integers, find the length of the **longest harmonious subsequence** (not necessarily contiguous). If no harmonious subsequence exists, return `0`.

## Input

The input is read via standard input as a single test case in the following form:

```
CASE0=<comma-separated integers>
```

Example:

```
CASE0=1,3,2,4,3
```

The harness also supports additional cases `CASE1`, `CASE2`, ... using the same format; process every case and produce one line of output per case, in order.

## Output

For each case, print a single line containing the length of the longest harmonious subsequence. If none exists, print `0`.

## Function Signature

You will implement a function with a similar shape to:

```python
def solve(values: list[int]) -> int:
    """Return the length of the longest harmonious subsequence, or 0 if none exists."""
```

## Notes

- **Subsequence vs. substring**: only the relative order of chosen elements must be preserved; they need not be contiguous.
- **Counting multiplicity matters**: if value `x` appears `k` times, you may use any number of those copies (up to `k`) in the subsequence.
- A subsequence that uses only one distinct value has max - min = 0, so it is **never** harmonious.
- A solution based on counting occurrences of each value and checking the pair `(v, v+1)` runs in `O(n)` time using a hash map, which is sufficient.
