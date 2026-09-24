# Majority Element II

## Problem

You are given an integer array `nums` of length `n`. Return **all** values that appear strictly more than `⌊n / 3⌋` times in the array. The answer can be returned in any order.

It is guaranteed that the number of such values is at most two.

## Function Signature

```python
def solve(nums: list[int]) -> list[int]:
    ...
```

## Input

A single test case is read from standard input. The format is:

```
CASE0=<n>
CASE0_NUMS=<comma-separated integers>
```

- `n` is the size of the array (`1 ≤ n ≤ 100_000`).
- Each integer satisfies `-10^9 ≤ nums[i] ≤ 10^9`.

The harness parses these `CASE0=...` lines and invokes `solve(nums)`.

## Output

Your `solve` function must return a `list[int]` containing every element that occurs more than `n/3` times, in any order. Duplicates in the output are not allowed.

## Example

Input:
```
CASE0=7
CASE0_NUMS=3,2,3,2,1,1,1
```

Output (any order):
```
[1, 3]
```

Explanation: `n = 7`, so the threshold is `⌊7/3⌋ = 2`. Elements `1` and `3` each appear `3` times; `2` appears only `2` times and is excluded.

## Notes

- A single linear pass with a frequency table (hash map) is sufficient and runs in `O(n)` time with `O(n)` extra space.
- The classic `O(n)` / `O(1)` extra-space approach uses the Boyer–Moore majority vote idea adapted to track two candidate values, since at most two elements can exceed the `n/3` threshold. Either approach is acceptable.
- Edge case: when `n < 3`, every element trivially appears more than `n/3` times (since counts are at most `1` and `n/3 < 1`).
