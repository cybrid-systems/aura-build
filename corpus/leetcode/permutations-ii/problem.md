# Permutations II

## Problem

Given a list of integers `nums` that may contain duplicate values, return **all unique permutations** of the list in any order.

A permutation is a rearrangement of all elements from `nums`. When the input contains duplicates, many rearrangements may be identical; each distinct arrangement should appear exactly once in the output.

### Example 1
```
Input:  [1, 1, 2]
Output: [[1, 1, 2], [1, 2, 1], [2, 1, 1]]
```
There are 3 distinct permutations of the multiset `{1, 1, 2}`.

### Example 2
```
Input:  [0, 1]
Output: [[0, 1], [1, 0]]
```

### Example 3
```
Input:  [1, 2, 3]
Output: [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
```
Since all elements are distinct, this reduces to standard permutation generation.

## Function Signature

```python
def solve(nums: list[int]) -> list[list[int]]:
    ...
```

## Input / Output Convention

The harness is **stdin-less**. You implement `solve(nums)` and it is called directly.

Test cases are injected as environment variables:

- `CASE0_INPUT` — JSON list, e.g. `[1,1,2]`
- `CASE0_EXPECTED` — JSON list of lists, e.g. `[[1,1,2],[1,2,1],[2,1,1]]`
- `CASE1_INPUT`, `CASE1_EXPECTED`, ...

The harness compares `solve(CASE0_INPUT)` to `CASE0_EXPECTED` after sorting both collections of permutations (so output ordering of permutations, and inner ordering of each permutation, is not asserted beyond set equality of the multiset of unique permutations).

## Notes

- The length of `nums` is at most 8, keeping the total number of unique permutations manageable (max 40320 for 8 distinct elements).
- The result must contain **no duplicates**, even if `nums` repeats values.
- Order of the returned permutations and order within each permutation does not matter; only the set of unique permutations is checked.
