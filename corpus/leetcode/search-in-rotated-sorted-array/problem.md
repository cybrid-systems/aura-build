# Search in Rotated Sorted Array

## Problem

You are given an array of distinct integers `nums` that was originally sorted in ascending order, but then it was rotated at some unknown pivot index `k` (with `1 <= k < nums.length`). Formally, after rotation the array looks like:

```
[nums[k], nums[k+1], ..., nums[n-1], nums[0], nums[1], ..., nums[k-1]]
```

For example, the sorted array `[0,1,2,4,5,6,7]` might become `[4,5,6,7,0,1,2]` after rotation.

Given the rotated array `nums` and an integer `target`, return the **index** of `target` in `nums`, or `-1` if it is not present.

You must write an algorithm that runs in **O(log n)** time.

## Function Signature

```
def solve(nums: list[int], target: int) -> int
```

## Input / Output Convention

Input is read as a single test case from stdin in `CASE0=...` format:

```
CASE0={"nums": [4,5,6,7,0,1,2], "target": 0}
```

Parse the JSON-like value after `CASE0=` to obtain `nums` (list of ints) and `target` (int).  
Print a single line containing the returned index (or `-1`) of `solve(nums, target)`.

### Examples

Input:
```
Case3={"nums": [4,5,6,7,0,1,2], "target": 0}
```
Output:
```
4
```

Input:
```
Case4={"nums": [4,5,6,7,0,1,2], "target": 3}
```
Output:
```
-1
```

Input:
```
Case5={"nums": [1], "target": 0}
```
Output:
```
-1
```

## Notes

- The array contains **distinct** integers (no duplicates); this guarantees a clean binary search decision in each step.
- A single-element array is a valid edge case — it is either the original sorted array or a "rotation" of it.
- Think in terms of "which half is properly sorted?" at each step, then decide which half must contain `target`.
- Expected complexity: **O(log n)** time, **O(1)** extra space.
