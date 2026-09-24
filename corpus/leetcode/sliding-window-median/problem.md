# Sliding Window Median

## Problem

You are given an integer array `nums` and an integer `k`. A *sliding window* of size `k` moves from the left end of `nums` to the right end, one position at a time. For each position of the window, compute the **median** of the elements currently inside it.

- If `k` is odd, the median is the middle element after sorting the window.
- If `k` is even, the median is the average of the two middle elements. Return this average **multiplied by 2** (i.e. the sum of the two middle elements).

Output the medians (in order) as the window slides across the array.

## Function Signature

```python
def solve(nums: list[int], k: int) -> list[int]:
    ...
```

- `nums`: list of integers (length `n`, 1 ≤ n ≤ 200_000, values in reasonable int range).
- `k`: window size (1 ≤ k ≤ n).
- Returns a list of `n - k + 1` integers — the median of each window position.

## Input / Output Convention

The harness feeds parameters through the standard Aura `CASE0` block (no stdin/stdout). Example case format:

```
CASE0=
nums = [1,3,-1,-3,5,3,6,7]
k = 3
expected = [1, -1, -1, 3, 5, 6]
```

The grader will call your `solve(nums, k)` and compare against `expected`.

## Notes

- The output must contain exactly `n - k + 1` medians.
- For even `k`, the returned value is **twice** the true median (the sum of the two middle values), so results are always integers and no division or rounding is required.
- Use two heaps (a max-heap for the lower half and a min-heap for the upper half) to maintain the window in `O(n log k)`. Lazy deletion is typically used to remove elements that leave the sliding window.
