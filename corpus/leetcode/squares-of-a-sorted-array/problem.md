# Squares of a Sorted Array

## Statement

Given an integer array `nums` sorted in non-decreasing order, return an array of the squares of each number, also sorted in non-decreasing order.

The input is guaranteed to be sorted, but the squares are not necessarily sorted because a negative number squared becomes positive and can be larger than the squares of the original positive numbers.

## Function Signature

```clojure
(solve nums)
```

- `nums`: a vector of integers, sorted in non-decreasing order (length ≥ 0).

Returns a vector of integers containing the squares of `nums`, sorted in non-decreasing order.

## Input / Output Convention

The harness runs the function against multiple cases. Each case is provided via standard input lines in the following format:

```
CASE0=(1 2 3 4)
CASE1=(-4 -1 0 3 10)
CASE2=(-5 -3 -2 -1)
CASE3=()
```

- Each `CASEn=` line contains a single whitespace-separated list written in Lisp/EDN style (parentheses around the sequence of integers).
- An empty pair `() ` represents an empty input vector.
- The function should be invoked once per case, in order.

## Examples

| Input | Output |
|-------|--------|
| `(-4 -1 0 3 10)` | `(0 1 9 16 100)` |
| `(-7 -3 2 3 11)` | `(4 9 9 49 121)` |
| `()` | `()` |

## Notes

- A two-pointer approach from both ends of the array runs in `O(n)` time without needing to sort the result explicitly, because the largest square must come from either the leftmost or rightmost absolute value at each step.
- The constraint that `nums` is already sorted in non-decreasing order is what makes the two-pointer technique valid: after taking absolute values, the largest remaining element is always at one of the two ends.
- Empty input must return an empty vector.
