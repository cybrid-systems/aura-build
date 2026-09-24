# Sliding Window Maximum

## Problem

You are given an integer array `nums` and an integer window size `k`. Slide a window of length `k` across the array from left to right, one position at a time, and compute the maximum element inside the window after each slide.

Formally, for each index `i` from `k - 1` to `n - 1`, output

```
max(nums[i - k + 1], nums[i - k + 2], ..., nums[i])
```

There are exactly `n - k + 1` windows (empty output if `n < k`).

## Function Signature

Implement:

```
solve(nums: list[int], k: int) -> list[int]
```

Return the list of window maximums in order.

## Input Convention (CASE0)

The harness drives the problem without stdin. A typical case file looks like:

```
CASE0
nums = [1, 3, -1, -3, 5, 3, 6, 7]
k    = 3
expect = [3, 3, 5, 5, 6, 7]
```

- Lines are key/value pairs; `expect` is the canonical output for verification.
- `nums` is a JSON-style array of integers; `k` is a positive integer.

## Output Convention

`solve` returns a list of integers, e.g. `[3, 3, 5, 5, 6, 7]`. The harness compares it against `expect` element-wise.

## Notes

- Aim for **O(n)** time using a monotonic deque that stores candidate indices in decreasing value order; pop from the back while the new element is greater-or-equal, and pop from the front any index that fell out of the window.
- When `k == 1`, every element is its own window maximum.
- When `k > n`, the result is the empty list `[]`.
- Use `<=` (not `<`) when pruning the back so that equal values farther left are discarded; this guarantees each index is pushed and popped at most once.
