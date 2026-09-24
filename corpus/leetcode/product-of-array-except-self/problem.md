# Product of Array Except Self

Given an integer array `nums`, return an array `answer` of the same length such that `answer[i]` equals the product of every element of `nums` **except** `nums[i]`. Your solution must run in `O(n)` time and **must not use the division operator**.

## Function Signature

```lisp
(solve nums)
```

- `nums` — a list of integers (may contain zero or more zeros; may contain negative numbers).
- Returns a list of integers, one per input element.

## Input Convention

The harness feeds input directly to `solve` as a single list:

```
CASE0=2 1 3 4
CASE1=0 4 0
CASE2=-1 1 0 -3 3
```

- Each `CASE` line contains the space-separated values of `nums`.

## Output Convention

For each `CASE`, print the resulting list, space-separated, on its own line:

```
24 12 8 6
0 0 0
0 0 9 0 0
```

## Notes

- You cannot use division to compute the answer. The intended trick is a left-pass / right-pass of products (or an equivalent `O(n)`-space approach).
- Zeros in the input must be handled correctly: if `nums` contains exactly one zero, every output position except that zero's index should be `0`; if it contains two or more zeros, the entire output is `0`.
- The output fits in a signed 32-bit integer for the given test cases.
