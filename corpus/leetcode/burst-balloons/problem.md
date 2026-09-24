# Burst Balloons

## Problem

You are given `n` balloons, each labeled with a number. The balloons are arranged in a row and indexed from `0` to `n-1`. Each balloon `i` has a value `nums[i]`.

You are tasked with bursting all the balloons one by one. If you burst balloon `i`, you earn:

```
nums[left] * nums[i] * nums[right]
```

coins, where `left` and `right` are the indices of the balloons **immediately adjacent** to balloon `i` at the moment it is burst (i.e., the nearest non-burst balloon to its left and right). After balloon `i` is burst, the balloons on either side become adjacent to each other.

The "boundary" balloons (the leftmost and rightmost neighbors) have a fixed value of `1`. Equivalently, you may imagine padding the array with `1` on both ends, so that bursting any balloon always has well-defined neighbors.

**Goal:** Maximize the total number of coins you can collect by bursting all the balloons.

You must implement:

```
solve(nums: list[int]) -> int
```

returning the maximum coins obtainable.

## Input / Output (Harness Convention)

The harness invokes your solver directly. For local self-testing, the harness reads cases from stdin using the convention:

```
CASE0=n
CASE0_VALS=...
CASE1=n
CASE1_VALS=...
...
```

Each `CASE*_VALS=` line contains `n` space-separated integers representing `nums`. The output is a single integer per case: the maximum coins.

Example:

```
CASE0=3
CASE0_VALS=3 1 5
```

Expected result for `nums = [3, 1, 5]` is `35` (burst order `1, 3, 5` → `3*1*5 + 3*5*1 + 1*1*1 = 35`).

## Notes

- `1 <= n <= 300`; `0 <= nums[i] <= 100`.
- A classic interval dynamic programming problem: consider the **last** balloon to be burst in a sub-interval rather than the first; this linearizes the recurrence to `O(n^3)`.
- Padded boundary values of `1` should not appear in the returned count's *boundary-only* bursts — they are only used for neighbor lookups.
