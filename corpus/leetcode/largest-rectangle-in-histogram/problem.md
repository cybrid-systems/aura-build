# Largest Rectangle in Histogram

## Problem

Given an array of non-negative integers `heights` representing a histogram where the width of each bar is `1`, find the area of the largest rectangle that can be formed within the histogram.

A rectangle formed by contiguous bars `i..j` has:
- **height** = `min(heights[k])` for `k` in `[i, j]`
- **width** = `j - i + 1`
- **area** = height × width

Return the largest possible area.

## Function Signature

```python
def solve(heights: list[int]) -> int:
    ...
```

- **Input:** `heights` — a list of `n` non-negative integers, `1 <= n <= 10^5`, `0 <= heights[i] <= 10^9`.
- **Output:** An integer — the maximum rectangle area.

## I/O Convention (stdin-less)

The harness invokes `solve(heights)` directly. When using the sample harness:

```
CASE0=heights=[2,1,5,6,2,3]
CASE0_EXPECTED=10
```

- `CASE0` — the input expression assigned to the parameter `heights`.
- `CASE0_EXPECTED` — the expected return value.
- Additional cases follow as `CASE1`, `CASE2`, ...

## Examples

**Example 1**
Input: `[2, 1, 5, 6, 2, 3]`
Output: `10`
Explanation: The largest rectangle uses bars at indices `2..3` with height `5` and width `2`, giving area `10`.

**Example 2**
Input: `[2, 4]`
Output: `4`
Explanation: Use the single bar of height `4`.

**Example 3**
Input: `[0, 0]`
Output: `0`

## Notes

- The optimal solution runs in **O(n)** time using a **monotonic increasing stack**: for each bar, find the nearest smaller bar on the left and right to determine the maximal width it can extend over.
- A common trick is to append a sentinel `0` to the end so the stack fully drains; this avoids leftover bars after the main loop.
- For the all-zeros case, the answer is `0` (no positive-height rectangle exists).
