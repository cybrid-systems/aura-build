# Combination Sum

## Problem Statement

Given an array of **distinct** positive integers `candidates` and a positive integer `target`, return *all unique combinations* of `candidates` where the chosen numbers sum to `target`. The same number from `candidates` may be chosen an unlimited number of times. Combinations whose elements appear in a different order are considered the **same** combination (i.e., the result must not contain duplicates, and the elements within each combination should be in non-decreasing order).

You may return the combinations in any order, but the list itself must contain no duplicates.

## Function Signature

```python
def solve(candidates: list[int], target: int) -> list[list[int]]:
    ...
```

## Input Convention (harness format)

The harness invokes `solve` directly — there is **no stdin**. Each test case is provided as two keyword arguments:

- `CASE0_CANDIDATES=[2,3,6,7]`
- `CASE0_TARGET=7`

`CASE0_RAND=` (a seed) may also be present for randomized cases; ignore it unless your solution needs randomness. Subsequent cases follow the same `CASE{k}_CANDIDATES` / `CASE{k}_TARGET` pattern.

The return value must be a `list[list[int]]` of integer combinations.

## Output Convention

The function should return a list of combinations (each combination is a list of integers in non-decreasing order). The harness will compare the returned list against the expected set of combinations as an unordered collection of unordered combinations.

## Examples

**Example 1**
- `candidates = [2, 3, 6, 7]`, `target = 7`
- Expected output (order may vary): `[[2, 2, 3], [7]]`

**Example 2**
- `candidates = [2, 3, 5]`, `target = 8`
- Expected output: `[[2, 2, 2, 2], [2, 3, 3], [3, 5]]`

**Example 3**
- `candidates = [2]`, `target = 1`
- Expected output: `[]`

## Notes

- All integers in `candidates` are positive and distinct; `target` is a positive integer.
- The same candidate may be reused unlimited times within a single combination.
- Sort `candidates` (or iterate in sorted order) to make pruning easy and to ensure combinations are emitted in non-decreasing order without duplicates.
- A classic backtracking approach works in time roughly proportional to the number of valid combinations times the average combination length; this is expected.
