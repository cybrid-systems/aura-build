# Subarray Product Less Than K

## Statement

Given an array of positive integers `nums` and an integer `k`, count the number of contiguous subarrays whose product of all elements is **strictly less than** `k`.

## Function Signature

```lisp
(solve nums k)
```

- `nums` — list/vector of positive integers (length `n`, `1 ≤ n ≤ 3·10^4`, `1 ≤ nums[i] ≤ 10^3`)
- `k` — integer threshold (`0 < k ≤ 10^6`)

Return a single integer: the number of contiguous subarrays whose product is `< k`.

## Input Convention

The harness reads from a constant registry (no stdin). Each test case is provided as a single labeled line of literal s-expressions, in this order:

```
CASE0=((2 1 1) 6)
CASE1=((1 2 3) 0)
CASE2=((10 5 2 6) 100)
```

- `CASE0=...` — a single test case.
- The right-hand side is a two-element list: `(nums k)` where `nums` is a list of integers and `k` is an integer.

There may be multiple `CASEn=...` lines. Process every one and emit one output line per case (see Output Convention).

## Output Convention

For each `CASEn=...`, print one line:

```
ANSn=<integer>
```

where `<integer>` is the count of contiguous subarrays whose product is strictly less than `k`.

## Examples

Given:

```
CASE0=((10 5 2 6) 100)
```

The contiguous subarrays of `[10, 5, 2, 6]` with product `< 100` are:
- `[10]` (10), `[5]` (5), `[2]` (2), `[6]` (6)
- `[10,5]` (50), `[5,2]` (10), `[2,6]` (12)
- `[5,2,6]` (60), `[10,5,2]` (100 — **not** strict), `[10,5,2,6]` (600)

Valid: 8.

Expected output:

```
ANS0=8
```

## Notes

- A sliding-window approach runs in `O(n)`: maintain a window `[left..right]` whose product stays `< k`; when adding `nums[right]` would exceed `k`, advance `left` while shrinking the product. Each position contributes exactly `right - left + 1` valid subarrays ending at `right`.
- All values in `nums` are positive, so products are monotone with respect to window size — no negatives, no zeros to worry about as blockers.
- If `k ≤ 1`, no product of any positive-integer window can be strictly less than `k`, so the answer is `0`. Handle this as an edge case.
