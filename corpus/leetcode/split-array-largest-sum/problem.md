# Split Array Largest Sum

## Problem

Given an integer array `nums` and an integer `m`, split `nums` into `m` non-empty contiguous subarrays. Your goal is to minimize the largest sum among the `m` subarrays. Return that minimized largest sum.

## Function Signature

```lisp
(defun solve (nums m) ...)
```

- `nums` — a list of integers (non-empty, with at least one element).
- `m` — an integer in the range `[1, length(nums)]`.
- Return a single integer: the minimal possible value of the largest subarray sum.

## Input / Output Convention

Input is provided on standard input as a single test case in the following form:

```
CASE0=(list of nums)
CASE0_M=<m>
```

For example:

```
CASE0=(7 2 5 10 8)
CASE0_M=2
```

Output a single integer on one line, the answer for `CASE0`.

## Examples

```
CASE0=(7 2 5 10 8)
CASE0_M=2
```
Output: `18`

Explanation: split into `[7,2,5]` and `[10,8]`, giving largest sum `18`, which is minimal.

```
CASE0=(1 2 3 4 5)
CASE0_M=2
```
Output: `9`

Explanation: split into `[1,2,3,4]` and `[5]` (largest sum `9`), which is optimal.

## Notes

- The answer lies between `max(nums)` (each element its own subarray, when `m = length(nums)`) and `sum(nums)` (one big subarray, when `m = 1`).
- A binary search over the candidate largest sum combined with a greedy check ("can we form ≤ m subarrays with each sum ≤ candidate?") yields an efficient solution.
- All numbers fit comfortably in standard 32-bit signed integers, but be mindful of overflow if using fixed-width languages.
