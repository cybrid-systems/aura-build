# Product of Array Except Self (variant)

## Statement

Given an integer array `nums` of length `n`, return an array `answer` of the same length such that `answer[i]` equals the product of all elements of `nums` **except** `nums[i]`.

You must compute this without using the division operator. Any extra space used beyond the output array counts, but constant extra space (excluding the output) is preferred.

This is the classic "product of array except self" problem, restated in this variant set with a fixed harness format.

## Function Signature

```clojure
(defn solve [nums]
  ;; returns vector of same length as nums
  )
```

## Input

The input is provided directly as a Clojure value on a single line (no stdin parsing required):

- `nums` — a vector of integers (may be empty, may contain zeros, may contain negatives).

## Output

A single line containing the resulting vector in the harness `CASE0=...` format. For example:

```
CASE0=[24,12,8,6]
```

## Examples

```
CASE0=[1,2,3,4]
CASE1=[24,12,8,6]
```

```
CASE0=[-1,1,0,-3,3]
CASE1=[0,0,9,0,0]
```

## Notes

- The expected time complexity is **O(n)**.
- You may assume the product of all elements fits within a 64-bit signed integer range for the given test cases.
- When `nums` is empty, return an empty vector `[]`.
- Division is **not** allowed; products must be formed directly from the input elements.
