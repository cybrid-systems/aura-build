# Partition Equal Subset Sum

## Problem

Given an integer array `arr` of size `n`, determine whether it can be split into two subsets whose sums are equal. Each element must belong to exactly one of the two subsets, and every element must be used.

Return `true` if such a partition exists, otherwise `false`.

### Function Signature

```clojure
(solve arr)  ; => boolean
```

## Input

A single line read by the harness describing the test case:

```
CASE0=<comma-separated integers>
```

Where `<comma-separated integers>` is the array `arr`, e.g. `CASE0=1,5,11,5`.

The harness will provide the string after `CASE0=` as the argument to `solve` (parsed into a sequence of integers). Output is the boolean result written to stdout.

### Example

```
Input:  CASE0=1,5,11,5
Output: true
```

(Subset `{1, 5, 5}` sums to `11`, the remainder `{11}` also sums to `11`.)

## Notes

- Empty array and single-element arrays cannot be split → return `false`.
- If the total sum `S` is odd, no equal partition is possible → return `false` immediately.
- A sum of `n` up to 20 elements with values up to ~10⁵ is expected; a subset-sum DP over achievable totals is sufficient.
- The function should consume only the parsed collection; no other I/O is performed by `solve`.
