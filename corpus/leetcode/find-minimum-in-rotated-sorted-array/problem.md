# Find Minimum in Rotated Sorted Array

## Problem

You are given an array of distinct integers `nums` that was originally sorted in ascending order and then **rotated** at some pivot. For example, `[0,1,2,4,5,6,7]` rotated by 3 becomes `[4,5,6,7,0,1,2]`. An array that was not rotated is still considered "rotated" (by 0).

Return the **minimum element** of `nums`. The array has length `n` where `1 ≤ n ≤ 5000` and all elements are unique.

You must write an algorithm with `O(log n)` runtime.

## Function Signature

```clojure
(defn solve [nums]
  ;; returns the minimum value in the rotated sorted array
  )
```

## Input / Output Convention

The harness feeds inputs as a single line on stdin, but when called as a function:

- **Input:** a single collection `nums` — a vector of integers (length ≥ 1, all distinct).
- **Output:** an integer — the minimum element.

### CASE lines (illustrative)

```
CASE0=([3 1 2]) -> 1
CASE1=([4 5 6 7 0 1 2]) -> 0
CASE2=([11 13 15 17]) -> 11
CASE3=([2 1]) -> 1
CASE4=([1]) -> 1
```

## Notes

- The array contains **no duplicates**, which lets a strict binary search be used without ambiguity.
- Aim for logarithmic time; a linear scan will time out on the largest cases.
