# Shortest Unsorted Continuous Subarray

## Problem

Given an array of integers `nums`, find the length of the shortest contiguous subarray such that sorting this subarray in ascending order results in the entire array being sorted in ascending order.

Return `0` if the array is already sorted.

## Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input

A single line containing space-separated integers representing the array `nums`.

## Output

A single integer: the length of the shortest unsorted continuous subarray.

## Examples

**Input**
```
CASE0=2 6 4 8 10 9 15
```

**Output**
```
5
```

**Explanation**
Sorting the subarray `[6, 4, 8, 10, 9]` gives `[2, 4, 6, 8, 9, 10, 15]`, which is fully sorted. The subarray length is `5`.

---

**Input**
```
CASE0=1 2 3 4
```

**Output**
```
0
```

**Explanation**
The array is already sorted.

---

**Input**
```
CASE0=1
```

**Output**
```
0
```

## Constraints

- `1 ≤ len(nums) ≤ 10^5`
- `-10^9 ≤ nums[i] ≤ 10^9`

## Notes

- The input is read as a single line; multiple test cases are not required.
- Aim for an `O(n)` time solution by scanning from both ends to find the first out-of-order positions.
- The result is `0` when `n < 2`.
