# Next Greater Element I

## Problem

You are given two integer arrays `nums1` and `nums2` where `nums1` is a subset of `nums2` (all elements of `nums1` appear in `nums2`, and all values in `nums2` are unique).

For each element `nums1[i]`, find the **next greater element** in `nums2`. The next greater element of `x` is the first element to the right of `x`'s position in `nums2` that is strictly greater than `x`. If no such element exists, use `-1`.

Return a vector `ans` of length `nums1.size()`, where `ans[i]` is the next greater element of `nums1[i]` in `nums2`.

## Function Signature

```haskell
solve :: [Int] -> [Int] -> [Int]
solve nums1 nums2 = ...
```

The harness will call `solve` once with the two lists and print the returned list.

## Input / Output (Harness Convention)

`nums1` and `nums2` are provided via `CASE0=...` / `CASE1=...` style configuration lines (no stdin). Each `CASE` value is a whitespace-separated list of integers, e.g.

```
CASE0=4 1 2
CASE1=1 3 4 2
```

Output is the result of `solve CASE0 CASE1` printed as a whitespace-separated list on a single line.

## Example

```
CASE0=4 1 2
CASE1=1 3 4 2
```
→ Output: `-1 3 -1`

```
CASE0=2 4
CASE1=1 2 3 4
```
→ Output: `3 -1`

## Notes

- `nums2` has distinct elements, but `nums1` may contain duplicates.
- An expected approach uses a monotonic decreasing stack scanned right-to-left (or left-to-right) over `nums2` to compute next-greater values in O(n), then looks each `nums1[i]` up in a hash map.
- Aim for O(|nums2| + |nums1|) time overall.
