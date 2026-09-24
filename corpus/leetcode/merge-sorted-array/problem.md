# Merge Sorted Array

## Problem

You are given two integer arrays `nums1` and `nums2`, both sorted in non-decreasing order, plus two integers `m` and `n` representing the number of initialized elements in `nums1` and `nums2` respectively.

`nums1` has length `m + n`, where the last `n` slots are treated as empty placeholders that must be filled. Merge `nums2` into `nums1` so that the resulting array is sorted in non-decreasing order, and store the result entirely inside `nums1`.

The merge must be done **in-place** — do not allocate another array.

## Function Signature

```clojure
(solve m n nums1 nums2)
```

- `m` — number of real elements at the front of `nums1`
- `n` — number of elements in `nums2`
- `nums1` — vector of length `m + n` (mutable / managed in-place)
- `nums2` — vector of length `n`, sorted ascending
- Returns the merged contents that should now occupy `nums1`.

## Input / Output Convention

A single test case is provided on stdin using the `CASE0=` format:

```
CASE0=m=3,n=2,nums1=[1,2,3,0,0,0],nums2=[2,5,7]
```

Parse the values and call `(solve m n nums1 nums2)`. Print the resulting `nums1` as a vector on its own line:

```
[1,2,2,3,5,7]
```

## Notes

- Work from the **back** of `nums1` to avoid overwriting unread elements — fill the largest available position on each step.
- All inputs are guaranteed to be sorted in non-decreasing order, but may contain duplicates and negatives.
- After the merge, `nums1` must remain sorted; stability of equal elements is not required.
