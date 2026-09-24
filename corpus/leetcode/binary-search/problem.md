# Binary Search

## Problem Statement

Given a sorted (non-decreasing) array of `n` integers and a target integer value, determine whether the target is present in the array. If it is, return the index of one occurrence of the target (any valid index is acceptable). If it is not present, return `-1`.

You must solve this using an **iterative binary search** approach with `O(log n)` time complexity. Recursive solutions are not allowed.

## Function Signature

```clojure
(defn solve [arr target]
  ;; Returns the index of target in arr, or -1 if not found.
  )
```

## Input / Output Convention

Input is provided via the `CASE0` environment-style lines (no stdin). Each test case is formatted as follows:

```
CASE0
n=5
arr=1 3 5 7 9
target=7
```

- `n` — the number of elements in the array (1 ≤ n ≤ 10^5).
- `arr` — `n` space-separated integers, sorted in non-decreasing order.
- `target` — the integer value to search for.

Output the single integer index (0-based) where `target` is found, or `-1` if it is absent. For example, the case above should produce:

```
3
```

## Notes

- The array is guaranteed to be sorted, but may contain duplicate values; returning the index of any one matching occurrence is acceptable.
- Edge cases to consider: an array of length 1, target smaller than all elements, target larger than all elements, and target equal to the first or last element.
- Use `lo` and `hi` bounds with the standard `mid = lo + (hi - lo) / 2` formulation to avoid overflow on large inputs.
