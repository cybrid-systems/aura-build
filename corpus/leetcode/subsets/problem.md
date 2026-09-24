# Subsets

## Problem

Given a set of **distinct** integers `nums`, return *all possible subsets* (the power set) of the array. The solution set must **not** contain duplicate subsets. You may return the subsets in any order.

Each subset should be represented as a list of integers. The order of elements inside a subset does not matter, but the overall collection of subsets returned must be exhaustive and unique.

## Function Signature

```lisp
(defun solve (nums)
  ...)
```

- `nums` — a list of distinct integers (may be empty).
- Returns a list of lists, where each inner list is one subset of `nums`. Order of subsets in the outer list is unspecified.

## Input / Output

The harness feeds the problem **without stdin**. Instead, test cases are expressed inline as `CASE` / `END_CASE` blocks. Each block has the form:

```
CASE0 = input = (1 2 3); expected = ((() (3) (2) (2 3) (1) (1 3) (1 2) (1 2 3))
CASE1 = input = (0); expected = ((() (0))
CASE2 = input = (); expected = ((())
```

For each `CASEn`, the harness binds `nums` to the `input` value and calls `solve`. The result is compared against `expected` using set/list equality (subsets may appear in any order).

## Notes

- The empty input `(nums = ())` must still yield exactly one subset: the empty subset `()`.
- Because `nums` contains distinct values, you don't need any deduplication logic beyond what backtracking naturally provides.
- The output is the power set, which always contains exactly `2^n` subsets where `n` is the length of `nums`.
