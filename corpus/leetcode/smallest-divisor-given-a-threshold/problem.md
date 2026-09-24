# Smallest Divisor Given a Threshold

## Problem

Given a non-empty array of positive integers `nums` and a positive integer `threshold`, define `f(d)` as the sum over all elements `nums[i]` of `ceil(nums[i] / d)`. Find the smallest positive integer divisor `d` such that `f(d) <= threshold`.

## Function Signature

```lisp
(solve nums threshold)
```

- `nums` — a non-empty list of positive integers (length ≤ 10^5, each value ≤ 10^6).
- `threshold` — a positive integer.
- Returns the smallest positive integer `d` satisfying the condition.

## Input Convention (stdin-less)

The harness injects a single case as keyword arguments. A representative debug line looks like:

```
CASE0=ARGV=[12, 5, 7, 9, 11], THRESHOLD=10
```

- `ARGV` is the JSON-style list of `nums`.
- `THRESHOLD` is the integer threshold.

## Output Convention

Print a single integer: the smallest valid divisor `d`.

```
2
```

## Notes

- The sum `f(d)` is monotonically non-increasing in `d`, so a binary search over `d` in `[1, max(nums)]` is appropriate.
- `d` is guaranteed to exist because `d = max(nums)` always yields `f(d) = len(nums) <= threshold` when `threshold >= len(nums)`; if `threshold < len(nums)`, no valid divisor exists — in that case return `-1`.
- Be careful with integer division: use ceiling semantics (`(nums[i] + d - 1) // d`) to match the problem's `ceil`.
