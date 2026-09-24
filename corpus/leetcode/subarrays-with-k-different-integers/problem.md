# Subarrays with K Different Integers

## Problem

Given an integer array `nums` and an integer `k`, return the number of contiguous subarrays that contain **exactly** `k` distinct integers.

## Function Signature

```python
def solve(nums: list[int], k: int) -> int:
```

## Input

The input is provided as a series of `CASE0=...` lines (one or more). Each case is described by two lines:

- `CASE0_NUMS=<array>` — a JSON-style array of integers, e.g. `[1,2,1,2,3]` or `[1,2,1,3,4]` (an empty array `[]` is also valid).
- `CASE0_K=<integer>` — the value of `k`, e.g. `2`.

Subsequent cases (if present) use `CASE1_...`, `CASE2_...`, etc. You must output one line per case.

## Output

For each case, print one line containing the count of subarrays with exactly `k` distinct integers.

## Examples

```
CASE0_NUMS=[1,2,1,2,3]
CASE0_K=2
```
Output: `7`

```
CASE1_NUMS=[1,2,1,3,4]
CASE1_K=3
```
Output: `3`

## Notes

- A standard approach uses the "at most" trick: the answer for `exactly k` equals `at_most(k) - at_most(k - 1)`, where `at_most(k)` counts subarrays with at most `k` distinct integers using a sliding window.
- The empty subarray is not counted; subarrays are non-empty contiguous slices.
- The array length `n` is small enough for an `O(n)` sliding window solution to run comfortably within limits.
