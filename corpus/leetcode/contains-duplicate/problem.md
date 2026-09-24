# Contains Duplicate

## Problem Statement

Given an array of integers, determine whether any value appears **at least twice** in the array.

Return `true` if at least one duplicate exists, otherwise return `false`.

### Examples

**Example 1**
- Input: `[1, 2, 3, 1]`
- Output: `true`
- Explanation: The value `1` occurs at indices `0` and `3`.

**Example 2**
- Input: `[1, 2, 3, 4]`
- Output: `false`
- Explanation: All values are unique.

**Example 3**
- Input: `[1, 1, 1, 3, 3, 4, 5, 2, 2]`
- Output: `true`
- Explanation: Both `1` and `2` appear more than once.

### Constraints

- `1 <= nums.length <= 10^5`
- `-10^9 <= nums[i] <= 10^9`

## Function Signature

```lisp
(solve nums)
```

- `nums` — a list/vector of integers.
- Returns a boolean (`true` / `false`).

## I/O Convention

The harness reads test cases from a `CASE0=...` block. Each line follows the form:

```
CASE0=[1, 2, 3, 1] -> true
CASE1=[1, 2, 3, 4] -> false
CASE2=[1, 1, 1, 3, 3, 4, 5, 2, 2] -> true
```

The left side of `->` is the input array, the right side is the expected boolean output. Your `solve` function is invoked once per case.

## Notes

- Aim for **O(n)** time and **O(n)** auxiliary space; a hash set is the natural fit.
- Sorting the array first also works in **O(n log n)** time with **O(1)** extra space (in-place sort).
- For very large inputs, a single linear pass with a set is typically fastest.
- The result is a strict boolean — do not return a count or an index.
