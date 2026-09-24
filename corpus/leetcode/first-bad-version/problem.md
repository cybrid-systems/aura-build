# First Bad Version

## Problem

You are a product manager and currently leading a team to develop a new product. Unfortunately, the latest version of your product fails the quality check. Since each version is developed based on the previous version, all versions after a bad version are also bad.

Suppose you have `n` versions `[1, 2, ..., n]` and you have an API `bool isBadVersion(version)` which returns whether `version` is bad. Implement a function to find the first bad version. You should minimize the number of calls to the API.

Given that there is **at least one** bad version, find the **smallest** version number `v` such that `isBadVersion(v)` is `true`.

## Function Signature

```lisp
(defun solve (n is-bad-version)
  ;; is-bad-version is a function: integer -> boolean
  ;; return the first bad version (smallest v with is-bad-version(v) = true)
  )
```

## Input / Output Convention

The harness drives the solution without stdin. A single test case is supplied via `CASE0`:

```
CASE0=n=<N>;bad=<K>
```

Where:
- `N` is the total number of versions (1 ≤ N ≤ 2^31 − 1)
- `K` is the index of the first bad version (1 ≤ K ≤ N)

The implementation of `isBadVersion(version)` must return `true` for all versions `v ≥ K` and `false` otherwise. The harness wires this predicate into `solve` so that the candidate solution never needs to know `K` directly.

The return value of `solve` should be the smallest `v` such that `isBadVersion(v)` returns `true`, i.e. `K`.

## Examples

```
CASE0=n=5;bad=4
; isBadVersion(1..3) = false, isBadVersion(4..5) = true
; expected answer = 4
```

```
CASE0=n=1;bad=1
; expected answer = 1
```

```
CASE0=n=2126753390;bad=1702766719
; expected answer = 1702766719
```

## Notes

- Minimize the number of calls to `isBadVersion`. The intended complexity is **O(log n)**.
- Watch out for **integer overflow** when computing midpoints like `(lo + hi) / 2`; prefer `lo + (hi - lo) / 2` (or an equivalent shift-based formulation) since `n` can reach 2^31 − 1.
- The monotonicity guarantee (`false, false, …, false, true, true, …`) is what enables binary search; do not linear-scan.
