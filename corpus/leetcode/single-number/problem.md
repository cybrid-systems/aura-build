# Single Number

## Problem

Given a non-empty array of integers, every element appears exactly twice except for one element which appears exactly once. Find and return the element that appears only once.

Implement an algorithm with **O(n)** time complexity and **O(1)** extra space (the output itself does not count toward the space).

## Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input

The input is provided directly as the `nums` argument to `solve` (no stdin). For harness replay, the format is:

```
CASE0=5
NUMS0=[2,2,1]
EXPECTED0=1
CASE1=7
NUMS1=[4,1,2,1,2]
EXPECTED1=4
CASE2=9
NUMS2=[-1,-1,0,0,7]
EXPECTED2=7
```

- `CASE#` — zero-based case index.
- `NUMS#` — the array of integers (length is odd, at least 1).
- `EXPECTED#` — the single unique value to return.

## Output

Return the integer that appears exactly once in `nums`.

## Examples

| Input | Output |
|---|---|
| `[2, 2, 1]` | `1` |
| `[4, 1, 2, 1, 2]` | `4` |
| `[1]` | `1` |
| `[0, 0, 1]` | `1` |

## Notes

- The naive `O(n)` time / `O(n)` space solution uses a hash set or counter. The intended optimal solution uses the **bitwise XOR** trick: `a ^ a == 0` and `a ^ 0 == a`, so XORing all elements cancels duplicates and leaves the unique one.
- The constraint `O(1)` extra space rules out hash-table-based approaches.
- Numbers may be negative; XOR works identically on signed integers at the bit level.
