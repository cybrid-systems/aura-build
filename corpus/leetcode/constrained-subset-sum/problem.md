# Constrained Subset Sum

## Problem

You are given an array `arr` of length `n` and a non‑negative integer `k`. Choose a subset `S` of indices `0 ≤ i < n` such that for any two chosen indices `i, j ∈ S` with `i < j`, the absolute difference `|arr[i] - arr[j]| ≤ k`. Among all valid subsets, maximize the sum of the chosen elements; output that maximum sum. (Choosing the empty subset is allowed only when no positive‑sum subset is valid, in which case the answer is `0`.)

## Function Signature

```python
def solve(arr: list[int], k: int) -> int:
    ...
```

## Input / Output Convention (Aura `CASE0` format)

The harness invokes `solve(arr, k)` directly — no stdin/stdout. If a driver is provided for local testing, it uses the `CASE0` block format:

```
CASE0
<arr as space-separated integers>
<k>
ANSWER0
<expected maximum sum>
```

Example:

```
CASE0
1 5 3 8 2 7 4
2
ANSWER0
24
```

## Notes

- `n` can be up to several hundred thousand; an `O(n log n)` or `O(n)` approach is expected.
- Elements of `arr` may be negative, zero, or positive.
- The "no two chosen elements differ by more than `k`" condition is independent of indices — only the **values** of the chosen elements matter.
- Use a sliding window / monotonic queue over sorted values, or a DP with a balanced structure; `O(n²)` will be too slow for large inputs.
