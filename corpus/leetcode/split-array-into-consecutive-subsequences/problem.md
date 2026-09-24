# Split Array into Consecutive Subsequences

## Problem

You are given an integer array `nums` sorted in non-decreasing order. Determine whether it is possible to split the array into one or more **subsequences** such that each subsequence satisfies:

- Its length is at least `3`.
- Its elements form a a sequence of **consecutive integers** (e.g. `[2, 3, 4, 5]`).

Each element of `nums` must belong to exactly one subsequence, and you may form any number of subsequences (one or more).

Return `true` if such a split exists, otherwise `false`.

## Example

```
Input:  [1, 2, 3, 3, 4, 4, 5, 5]
Output: true
Explanation: One valid split is [1,2,3,4,5] and [3,4,5].
```

```
Input:  [1, 2, 3, 3, 4, 4, 5, 5, 6]
Output: false
Explanation: Every partition into consecutive subsequences of length ≥ 3 fails to cover all 9 elements.
```

## Function Signature

```lisp
(defun solve (nums)
  ;; -> boolean
  )
```

## Input / Output (Harness Convention)

The harness reads from the symbol `CASE0` and prints the result of `(solve CASE0)`.

```
CASE0=(1 2 3 3 4 4 5 5)
;; -> T
```

```
CASE0=(1 2 3 3 4 4 5 5 6)
;; -> NIL
```

## Notes

- `nums` is non-decreasing; equal values are allowed and must each be placed into some subsequence.
- A subsequence is selected by indices (order in `nums` is preserved), but the values inside each subsequence must be strictly consecutive integers.
- Target complexity: **O(n)** time and **O(n)** auxiliary space. A greedy approach that prefers extending an existing subsequence over starting a new one works in linear time.
