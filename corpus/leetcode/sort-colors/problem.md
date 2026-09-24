# Sort Colors

## Problem

You are given an array `nums` containing only the integers `0`, `1`, and `2`. Sort the array **in-place** so that all `0`s come first, followed by all `1`s, then all `2`s.

You must not use the library sort function. Aim for a single-pass, O(1) extra space solution using three pointers (the classic Dutch National Flag approach).

## Function Signature

```python
def solve(nums: list[int]) -> list[int]:
    ...
```

- The function receives a list of integers `nums` (containing only 0, 1, 2).
- It should sort `nums` in-place and return the same list.

## I/O Convention (StdIn-less)

The harness invokes your `solve` function directly. For local testing, mimic this stub:

```
CASE0=[2,0,2,1,1,0]
CASE1=[2,0,1]
CASE2=[0]
CASE3=[1,1,1,0,0,2,2]
```

Your function should produce:

```
[0,0,1,1,2,2]
[0,1,2]
[0]
[0,0,1,1,1,2,2]
```

## Notes

- The order among equal values does not matter — only the three groups need to be separated.
- Expected complexity: O(n) time, O(1) extra space.
- A two-pass counting solution is acceptable, but the three-pointer approach is the intended one.
