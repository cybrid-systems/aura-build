# Subsets II

## Problem

Given an integer array `nums` that may contain **duplicates**, return all possible subsets (the power set) of the array. The solution set **must not contain duplicate subsets**. Return the subsets in any order, but each subset must appear only once and can be in any internal order (a canonical sorted order is conventional).

### Examples

**Example 1**

```
Input:  nums = [1, 2, 2]
Output: [[], [1], [1,2], [1,2,2], [2], [2,2]]
```

**Example 2**

```
Input:  nums = [0]
Output: [[], [0]]
```

**Example 3**

```
Input:  nums = [1, 2, 3]
Output: [[], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]]
```

### Constraints

- `1 <= nums.length <= 10`
- `-10 <= nums[i] <= 10`
- Each subset must be unique as a whole (treated as a multiset of elements in the order it was generated).

## Function Signature

```
(solve nums)
  nums : list[int]   -- the input array, may contain duplicates
  returns : list[list[int]]   -- all unique subsets (power set) in any order
```

## Input / Output Convention (Aura harness)

The harness invokes `(solve ...)` directly; there is no stdin. For local replay/testing the file `TEST.in` uses the convention:

```
CASE0=1 2 2
CASE1=0
CASE2=1 2 3
```

- Each `CASEn=` line contains the whitespace-separated values of `nums` for one test case, in order.
- Each corresponding `CASEn.out` (when generated) lists one subset per line, with subsets separated by a blank line, elements space-separated inside a subset. Output order is flexible; comparison ignores ordering between subsets.

## Notes

- Sorting `nums` first (e.g., ascending) makes it straightforward to skip duplicates during enumeration: when picking `nums[i]`, skip it if `i > start` and `nums[i] == nums[i-1]`.
- A backtracking approach that grows a partial subset and recurses over the indices `[start .. n)` runs in `O(n * 2^n)` time, which is optimal for output size.
- An iterative approach that, after sorting, conditionally inserts each `nums[i]` into pre-existing subsets also works, but be careful to avoid generating duplicates when `nums[i] == nums[i-1]`.
