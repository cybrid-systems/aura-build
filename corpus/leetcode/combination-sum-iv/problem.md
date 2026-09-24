# Combination Sum IV

## Problem

Given an array of **distinct** integers `nums` and a **target** integer, return the *number of possible combinations* that add up to `target`, where **order matters**.

Formally, count the number of ordered sequences `(i1, i2, …, ik)` such that:

- each `ij` is an index into `nums` (you may reuse the same value any number of times),
- `nums[i1] + nums[i2] + … + nums[ik] == target`.

The answer may be very large, so return it modulo **10⁹ + 7**.

### Example

```
nums = [1, 2, 3], target = 4

Sequences:
(1,1,1,1)  → 1+1+1+1 = 4
(1,1,2)    → 1+1+2   = 4
(1,2,1)    → 1+2+1   = 4
(2,1,1)    → 2+1+1   = 4
(2,2)      → 2+2     = 4
(1,3)      → 1+3     = 4
(3,1)      → 3+1     = 4

Total = 7
```

### Constraints

- `1 ≤ nums.length ≤ 200`
- `1 ≤ nums[i] ≤ 1000`
- All elements of `nums` are distinct.
- `1 ≤ target ≤ 1000`

## Function signature

```lisp
(defun solve (nums target)
  ;; returns number of ordered combinations modulo 1000000007
  )
```

- `nums` — a list of distinct integers (length 1…200, each value 1…1000).
- `target` — a non-negative integer (1…1000).
- Return a single integer: the count modulo `10⁹ + 7`.

## I/O convention

The harness calls `(solve …)` directly; **no stdin**. For local sanity checks you may mimic this convention:

```
CASE0=([1 2 3] 4) -> 7
CASE1=([9] 3)     -> 0
CASE2=([1] 4)     -> 1   ; only (1,1,1,1)
CASE3=([3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 ...) 100 -> <expected>
```

## Notes

- Because **order matters**, the classical "subsets with repetition" formulation does not apply — `(1,2)` and `(2,1)` are counted separately. Think in terms of permutations (with repetition allowed) that sum to `target`.
- A direct backtracking tree of sequences can easily blow up; a single 1-D DP table of size `target+1` is enough. The recurrence and its order of evaluation are the crux of the puzzle.
- The values are small enough for `O(n · target)` time, where `n = (length nums)`.
