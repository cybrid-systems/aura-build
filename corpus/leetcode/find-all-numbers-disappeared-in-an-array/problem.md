# Find All Numbers Disappeared in an Array

## Problem

Given an array `nums` of length `n` where each element is in the range `[1, n]`, some elements may appear more than once and others may be missing entirely. Return a list of all numbers in the range `[1, n]` that do **not** appear in `nums`.

You must solve this using **O(n)** time and **O(1)** extra space (ignoring the output list).

## Function Signature

```lisp
(defun solve (nums)
  ;; returns a list of missing numbers in [1, n]
  )
```

## Input

Read from standard input using the **Aura harness** `CASE0=` format. Each case provides one array.

```
CASE0=4 3 2 7 8 2 3 1
```

- The line begins with the literal prefix `CASE0=`.
- After the `=` sign is a space-separated sequence of integers representing the array `nums`.

## Output

Print the missing numbers as a space-separated list, in **ascending order**, followed by a newline.

Example output for the sample above:

```
5 6
```

## Notes

- `n` is the length of the input array; the values are guaranteed to lie in `[1, n]`.
- Multiple occurrences are allowed; only the *presence* of each value matters for this problem.
- The result must be sorted ascending.
