# Find All Duplicates in an Array

## Problem Statement

Given an integer array `nums` of length `n` where each integer `nums[i]` is in the range `[1, n]`, some elements appear **twice** and others appear **once**. Return a list of all the integers that appear **twice** in the array.

You must write an algorithm that runs in **O(n)** time and uses **O(1)** extra space (excluding the output list).

## Function Signature

```lisp
(defun solve (nums) ...)
```

- `nums`: a list of integers of length `n` (1 ≤ `nums[i]` ≤ `n`).
- Returns: a list of integers that each appear exactly twice (order of the output does not matter, but duplicates in the output itself are not expected).

## Input / Output Convention

The harness reads a single test case from standard input in the following format:

```
CASE0=<list-of-ints>
```

For example:

```
CASE0=[4,3,2,7,8,2,3,1]
```

The element after `CASE0=` is parsed as a list of integers (e.g., `[4,3,2,7,8,2,3,1]` → `'(4 3 2 7 8 2 3 1)`).

The function `solve` should return the list of integers that appear twice. The harness will compare the returned list to the expected answer (as a set).

### Example

**Input**

```
CASE0=[4,3,2,7,8,2,3,1]
```

**Output** (one valid ordering)

```
[2, 3]
```

Explanation: `2` and `3` each appear twice in the array; all other values appear exactly once.

## Notes

- You are guaranteed that at least one element appears twice.
- The list length `n` can be up to 10⁵, so an O(n²) solution will not pass.
- Because each value is in `[1, n]`, you can use **in-place negation** or **sign marking** of indices to detect duplicates in O(1) extra space.
- Order of the output list is not significant; the grader treats the result as a set.
