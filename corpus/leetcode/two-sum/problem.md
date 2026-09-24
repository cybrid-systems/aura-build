# Two Sum

**Category:** arrays
**Difficulty:** easy
**Slug:** two-sum

## Problem

You are given an array of integers and an integer `target`. Return the indices of the two numbers in the array that add up to `target`.

Each input will have **exactly one** solution, and you may not use the same element twice. The order of the returned indices does not matter.

## Function Signature

```python
def solve(nums: list[int], target: int) -> list[int]:
```

## Input

The input consists of multiple test cases. Each test case has two lines:

- Line 1: Two space-separated integers `n` and `target`, where `n` is the length of the array (2 ≤ n ≤ 10^4).
- Line 2: `n` space-separated integers, the elements of the array.

The input ends at end-of-file.

### I/O Convention (Aura Harness)

For each test case, your `solve` function is called with the parsed inputs as its arguments. It must **return** the answer; do not print. The harness wraps multiple test cases and emits answers in this format:

```
CASE0=0 1
CASE1=2 4
CASE2=...
```

Each line begins with `CASE<k>=` followed by the returned pair of indices, space-separated, in increasing index order.

## Example

Input:
```
4 9
2 7 11 15
3 6
3 2 4
```

Expected output:
```
CASE0=0 1
CASE1=1 2
```

## Notes

- Aim for `O(n)` time and `O(n)` extra space using a hash map of value → index.
- The problem guarantees exactly one valid pair exists, so no tie-breaking is required.
