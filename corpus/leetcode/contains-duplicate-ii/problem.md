# Contains Duplicate II

## Problem

Given an integer array `nums` and an integer `k`, determine whether there exist two **distinct** indices `i` and `j` such that:

- `nums[i] == nums[j]`
- `|i - j| <= k`

Return `true` if such a pair exists, otherwise `false`.

## Function Signature

```python
def solve(nums: list[int], k: int) -> bool:
    ...
```

## Input / Output Convention

The harness runs a sequence of test cases. Each case is supplied as a single line on standard input in the form:

```
CASE0=nums=[1,2,3,1],k=3
CASE1=nums=[1,0,1,1],k=1
...
```

Your `solve` function receives the parsed `nums` list and integer `k` for each case, and must return a `bool`. The harness prints `True` / `False` per case in input order.

## Examples

| Case | `nums`        | `k` | Expected |
|------|---------------|-----|----------|
| 0    | `[1,2,3,1]`   | 3   | `True`   |
| 1    | `[1,0,1,1]`   | 1   | `True`   |
| 2    | `[1,2,3,1,2,3]`| 2  | `False`  |

## Notes

- `k` may be larger than the array length; in that case any duplicate anywhere in the array qualifies.
- `nums` may be empty; in that case the answer is `False`.
- A hash map of value → most recent index is sufficient for an `O(n)` solution.
