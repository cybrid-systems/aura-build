# Longest Turbulent Subarray

## Problem

Given an integer array `arr` of length `n`, a **turbulent subarray** is a contiguous subarray where the comparison between adjacent elements alternates strictly between `<` and `>`:

- For even index `i` (relative to the subarray's start), `arr[i] < arr[i+1]`
- For odd index `i` (relative to the subarray's start), `arr[i] > arr[i+1]`

(Or the pattern may start with `>` and then alternate.)

In other words, no two adjacent pairs in the subarray can have the same comparison sign, and the signs must alternate.

A subarray of length `1` is trivially turbulent, and a subarray of length `2` is turbulent as long as the two elements are not equal.

Your task is to return the length of the longest turbulent subarray of `arr`.

## Function Signature

```python
def solve(arr: list[int]) -> int:
    ...
```

## Input

The harness provides the input via standard variables (no stdin):

- `arr` — a list of integers, length `n` where `1 <= n <= 10^5` and `arr[i]` fits in a 32-bit signed integer.

For local debugging, use the `CASE0=...` convention. Examples:

```
CASE0=arr=[9,4,2,10,7,8,8,1,9]
CASE1=arr=[4,8,12,16]
CASE2=arr=[1,1,1,1]
```

Expected outputs for the cases above: `5`, `2`, `1`.

## Output

Return an `int`: the length of the longest turbulent subarray.

## Notes

- A sliding-window / two-pointer approach runs in `O(n)` time.
- Be careful with equal adjacent elements: they break turbulence immediately and force the window to reset.
- Examples:
  - `[9,4,2,10,7,8,8,1,9]` → the subarray `[4,2,10,7,8]` (length 5) is turbulent: `9>4`, `4>2`, `2<10`, `10>7`, `7<8`.
  - `[4,8,12,16]` → any two adjacent elements give a length of `2` (monotonic, so no alternation).
  - `[1,1,1,1]` → only length `1` subarrays qualify.
