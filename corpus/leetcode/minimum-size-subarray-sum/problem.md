# Minimum Size Subarray Sum

## Problem Statement

Given an array of positive integers `nums` and an integer `target`, find the length of the **shortest contiguous subarray** whose sum is **greater than or equal to** `target`. If no such subarray exists, return `0`.

All numbers in `nums` are strictly positive, which means a sliding window (two-pointer) approach is well-suited: expanding the right end monotonically grows the window's sum, and shrinking the left end monotonically decreases it.

## Function Signature

```
solve(nums: list[int], target: int) -> int
```

## Input / Output Convention

The harness feeds each case as labeled `CASE0=...` lines on stdin:

```
CASE0=[2, 3, 1, 2, 4, 3]
CASE0_TARGET=7
ANS0=2
```

- `CASE0=...` — JSON-ish list of positive integers (the array).
- `CASE0_TARGET=...` — the required minimum sum.
- `ANS0=...` — expected return: the minimal subarray length, or `0` if none qualifies.

The function must read whichever `CASEi` / `CASEi_TARGET` pair is active and produce `ANS0` on stdout (or the harness's expected channel).

## Examples

| nums | target | answer | explanation |
|---|---|---|---|
| `[2, 3, 1, 2, 4, 3]` | `7` | `2` | `[4, 3]` sums to 7 — length 2 |
| `[1, 4, 4]` | `4` | `1` | `[4]` alone suffices — length 1 |
| `[1, 1, 1, 1, 1]` | `11` | `0` | no subarray reaches the target |
| `[5, 1, 3, 5, 10, 7, 4, 9, 2, 8]` | `15` | `1` | element `10`? no — `[5,10]` sums to 15, length 2; check carefully for length 1 — none ≥ 15, so answer is 2 |

## Notes

- Because every element is positive, a classic left/right sliding window solves it in **O(n)** time.
- If you use a prefix-sum + binary-search variant, beware that it only matches the sliding-window answer when all values are non-negative — which holds here, so it's a valid alternative at **O(n log n)**.
- Edge cases to handle: empty `nums`, `target <= 0` (answer is `0` since no positive subarray can sum to a non-positive target… actually `target == 0` is trivially `0` length, but the problem typically guarantees `target > 0`), and `nums` of length 1.
- Return `0` when no qualifying subarray exists; do **not** return `len(nums)` or `-1`.
