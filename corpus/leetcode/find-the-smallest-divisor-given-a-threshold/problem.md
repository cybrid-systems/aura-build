# Find the Smallest Divisor Given a Threshold

## Problem

You are given an integer array `nums` and an integer `threshold`. For a positive integer `divisor`, define the *division cost* of `nums` as:

$$\text{cost}(divisor) = \sum_{i=0}^{n-1} \left\lceil \frac{nums[i]}{divisor} \right\rceil$$

Find the **smallest** positive integer `divisor` such that `cost(divisor) <= threshold`.

If no such divisor exists, return `-1` (this happens only when `threshold` is smaller than the length of `nums`, since even `divisor = max(nums)` yields a cost equal to `n`).

## Function Signature

```python
def solve(nums: list[int], threshold: int) -> int:
    ...
```

## Input / Output (Aura Harness)

The harness calls `solve(...)` directly. Use the following convention when supplying sample cases in the prompt:

```
CASE0 = nums = [1, 2, 5]
THRESHOLD0 = 9
CASE1 = nums = [2, 1, 0]
THRESHOLD1 = 3
```

For each case `CASEi`, the harness unpacks the variables (`nums_i`, `threshold_i`) and asserts that `solve(nums_i, threshold_i)` matches the expected output.

## Expected Output

```
CASE0 -> 5
CASE1 -> -1
```

## Notes

- `1 <= len(nums) <= 10^5`, `1 <= nums[i] <= 10^5`.
- Binary search `divisor` over the range `[1, max(nums)]`. The cost function is **monotonically non-increasing** in `divisor`, so standard lower-bound search applies.
- Use integer ceiling division: `(num + divisor - 1) // divisor`.
