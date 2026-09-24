# Median of Two Sorted Arrays

## Problem

You are given two integer arrays `nums1` and `nums2` that are sorted in non-decreasing order. The combined length of the two arrays is `m + n`. Find the median of the combined sorted array. The overall run time complexity should be `O(log (m+n))`.

If the total number of elements is odd, the median is the middle element. If it is even, the median is the average of the two middle elements.

## Function Signature

```
def solve(nums1: list[int], nums2: list[int]) -> float
```

## Input / Output Convention

The harness feeds each test case on stdin, one per invocation, as follows:

```
CASE0=nums1=[1,3] nums2=[2]
CASE1=nums1=[1,2] nums2=[3,4]
CASE2=nums1=[]    nums2=[1]
CASE3=nums1=[0,0] nums2=[0,0]
```

Each `CASEi=` line encodes one call to `solve(nums1, nums2)`. The expected output is one line per case containing the median value (printed with reasonable precision, e.g., `2.0` or `2.5`).

Example expected output for the cases above:

```
2.0
2.5
1.0
0.0
```

## Notes

- Empty arrays are valid inputs.
- The arrays may contain duplicates and may include negative numbers.
- The `O(log (m+n))` requirement is the core challenge — a linear merge will not pass. The intended approach uses binary search on the partition point of the smaller array.
- Always binary-search on the smaller of `nums1` and `nums2` to keep the search space tight and handle edge cases cleanly.
