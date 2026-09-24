# Peak Index in a Mountain Array

## Problem

An array `arr` of length `n >= 3` is called a *mountain array* if there exists some index `p` (with `1 <= p <= n-2`) such that:

- `arr[0] < arr[1] < ... < arr[p-1] < arr[p]`
- `arr[p] > arr[p+1] > ... > arr[n-1]`

In other words, the array strictly increases to a single peak `arr[p]` and then strictly decreases. It is guaranteed that `arr` is a mountain array.

Your task is to return the index `p` of the peak element.

You must solve it in **O(log n)** time.

## Function Signature

```
def solve(arr: list[int]) -> int
```

## Input

The input is provided via a stdin-less harness using a `CASE0=...` convention. A single test case is given on one line:

```
CASE0=0 1 2 4 7 5 3 1
```

The line after `CASE0=` is parsed as a space-separated array of integers `arr`.

## Output

Print a single line containing the index `p` of the peak element. For the example above the peak is `7` at index `4`, so the output is:

```
4
```

## Notes

- `n` can be large (up to ~10^6), so a linear scan is not acceptable — use binary search.
- Compare `arr[mid]` with `arr[mid+1]` to decide whether the peak lies to the left (including `mid`) or to the right of `mid`.
- The peak is guaranteed to exist and is unique.
