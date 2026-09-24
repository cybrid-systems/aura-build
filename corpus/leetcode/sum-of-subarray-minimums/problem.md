# Sum of Subarray Minimums

## Problem

Given an array of integers `arr` of length `n`, compute the sum of the minimum element of every contiguous (contiguous) subarray of `arr`. Return the result modulo `10^9 + 7`.

Formally, let

```
answer = ( Σ  min(arr[i..j])  ) mod (10^9 + 7)
         over all 0 ≤ i ≤ j < n
```

For example, for `arr = [3, 1, 2, 4]` the contiguous subarrays and their minima are:

```
[3] -> 3
[3,1] -> 1
[3,1,2] -> 1
[3,1,2,4] -> 1
[1] -> 1
[1,2] -> 1
[1,2,4] -> 1
[2] -> 2
[2,4] -> 2
[4] -> 4
```

Sum = `3 + 1 + 1 + 1 + 1 + 1 + 1 + 2 + 2 + 4 = 17`.

A naive `O(n^2)` enumeration is too slow for `n` up to `3 * 10^5`. Use a monotonic stack to determine, for each position `k`, how many subarrays have `arr[k]` as their minimum, then sum `arr[k] * count[k]` over all `k`.

## Function Signature

```
(solve arr)
```

- `arr` : a list of integers (length `n`, `1 <= n <= 3*10^5`, `-10^9 <= arr[i] <= 10^9`).
- Returns an `int` — the required sum modulo `1_000_000_007`.

## Input / Output Convention (CASE0)

The harness uses a single case in the `CASE0` format described below; your `solve` function receives the parsed Python object directly (no stdin/stdout involved).

```
CASE0
n
arr_0 arr_1 ... arr_{n-1}
```

Example:

```
CASE0
4
3 1 2 4
```

Expected return value: `17`.

## Notes

- For each index `k`, find the nearest index to the left that is strictly less than `arr[k]` (call it `L[k]`) and the nearest index to the right that is less-than-or-equal to `arr[k]` (call it `R[k]`). Then `arr[k]` is the minimum of exactly `(k - L[k]) * (R[k] - k)` subarrays. This “strict vs. non-strict” split is important for ties.
- Compute contributions modulo `10^9 + 7`. Be careful with negative values in the input — convert the contribution `(arr[k] % MOD) * count % MOD` before summing.
- Time complexity `O(n)` and auxiliary space `O(n)` are expected.
