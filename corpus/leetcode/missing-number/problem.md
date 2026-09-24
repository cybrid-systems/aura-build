# Missing Number

## Problem Statement

Given an array `nums` containing `n` distinct integers in the range `[0, n]`, find the one number that is missing from the array.

In other words, the array has length `n` and should contain every number from `0` to `n`, but exactly one number from this range is absent. Return that missing number.

### Constraints
- `n == nums.length`
- `1 <= n <= 10^4`
- `0 <= nums[i] <= n`
- All numbers in `nums` are distinct

### Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input / Output Convention (CASE0 format)

This problem uses a **CASE0** I/O convention — no stdin/stdout. The harness calls your `solve()` function directly with parsed arguments.

Example test invocation:

```
CASE0 = solve([3, 0, 1])
EXPECTED = 2
```

```
CASE0 = solve([0, 1, 2, 3, 4, 5, 6, 7, 9])
EXPECTED = 8
```

## Notes

- A straightforward O(n) time and O(1) extra-space solution exists using the arithmetic series formula `n*(n+1)/2` minus the sum of the array, or via XOR.
- Alternatively, sorting or using a set also work but may be less optimal.
- Watch out for the case `n = 1` where the answer may be `0` or `1`.
