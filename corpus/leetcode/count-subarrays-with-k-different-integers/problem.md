# Subarrays with K Different Integers

## Problem

Given an integer array `nums` and an integer `k`, return the number of subarrays that contain **exactly** `k` distinct integers.

A subarray is a contiguous non-empty sequence of elements within the array.

## Function Signature

```python
def solve(nums: list[int], k: int) -> int:
    ...
```

## Input Format

The input is read from a file named `input.txt` in the following format. Each test case begins with a line `CASE0=<id>` that identifies the case (the harness uses the highest-numbered `CASE` it finds). A single test case looks like:

```
CASE0=0
<value of k>
<n>
<n space-separated integers: nums>
```

The harness will invoke `solve(nums, k)` once per test case found and write each answer on its own line in `output.txt` in the same order as the cases.

## Output Format

For each test case, print one line containing the number of subarrays of `nums` that have exactly `k` distinct integers.

## Example

**Input**
```
CASE0=0
2
5
1 2 1 2 3
```

**Output**
```
7
```

**Explanation:** The subarrays with exactly 2 distinct integers are:
`[1,2]`, `[2,1]`, `[1,2]`, `[2,1]`, `[1,2,1]`, `[1,2,1,2]`, `[2,1,2]`.

## Notes

- `1 ≤ n ≤ 2 * 10^4`, `1 ≤ k ≤ n`, and `1 ≤ nums[i] ≤ 10^5`.
- A common technique is to compute `atMost(k)` and `atMost(k-1)` via a sliding window; the answer is `atMost(k) - atMost(k-1)`.
- The input may contain multiple `CASE0=...` lines for batched testing; process each independently.
