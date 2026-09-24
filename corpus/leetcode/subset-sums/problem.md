# Subset Sums

## Problem Statement

Given an array of `N` distinct integers, generate **all possible subset sums** that can be formed by choosing any non-empty subset of the array. Output these sums in **non-decreasing order**.

A subset sum is the sum of elements of a chosen non-empty subset. The same sum value should appear only once in the output, even if multiple subsets produce it.

### Example

For the input array `[1, 2, 3]`:

- Subset `{1}` → sum `1`
- Subset `{2}` → sum `2`
- Subset `{3}` → sum `3`
- Subset `{1, 2}` → sum `3`
- Subset `{1, 3}` → sum `4`
- Subset `{2, 3}` → sum `5`
- Subset `{1, 2, 3}` → sum `6`

Unique sums in non-decreasing order: `1, 2, 3, 4, 5, 6`.

## Function Signature

```python
def solve(n: int, arr: List[int]) -> List[int]:
    ...
```

## Input Format

The input is read from standard input in the following format:

- `CASE0=<n>` — number of elements
- `CASE1=<space-separated integers>` — the array elements

## Output Format

Print all unique subset sums in **non-decreasing order**, separated by spaces on a single line.

## Constraints

- `1 ≤ N ≤ 20`
- `-10^9 ≤ arr[i] ≤ 10^9`
- All elements in the array are distinct.

## Notes

- Use backtracking to enumerate subsets efficiently.
- After collecting the sums, sort and deduplicate them before printing.
- Empty subset sum (`0`) should be excluded from the output.
