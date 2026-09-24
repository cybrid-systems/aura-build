# Bitwise AND of Numbers Range

## Problem

You are given two non‑negative integers `m` and `n` with `m <= n`. Compute the bitwise AND of every integer in the closed interval `[m, n]`, i.e. the value of `m & (m+1) & (m+2) & … & n`.

Since the answer can grow with the bit‑width of the inputs, the result must be returned as a 64‑bit unsigned integer (values `0 … 2^64 − 1`). Treat any signed input as its two's‑complement 64‑bit representation.

## Function Signature

```clojure
(solve m n)
```

- `m`, `n` — 64‑bit integers (read as unsigned), `0 <= m <= n < 2^64`.
- Returns the 64‑bit unsigned bitwise AND of all numbers in `[m, n]`.

## Input / Output Convention

The harness feeds **no stdin**. Instead the driver calls your `solve` function directly with concrete arguments and prints the result. The convention used by the runner is a `CASE0=` line:

```
CASE0=m=5,n=7
```

For the call `(solve 5 7)` your function should return `4` (since `5 & 6 & 7 = 0b100 = 4`). The harness prints:

```
ANS0=4
```

Additional cases follow the same pattern: `CASE1=…`, `CASE2=…`, each producing a matching `ANSk=…` line.

## Examples

| `m`  | `n`  | Range AND | Reason                                |
|-----:|-----:|----------:|---------------------------------------|
|    5 |    7 |         4 | `0b101 & 0b110 & 0b111 = 0b100`       |
|    0 |    0 |         0 | single element                        |
|    1 | 2^63 | 0         | low bit flips across the range        |
| 2^63 | 2^63| 2^63      | single 64‑bit element                 |

## Notes

- A naive accumulation over `n − m + 1` values is far too slow when `n − m` is near `2^64`; aim for `O(log max(m,n))` time.
- Observation: any bit that stays constant across the whole interval survives; bits that change anywhere are zeroed. Finding the longest common prefix of `m` and `n` (their shared high bits) is the standard trick.
- Output the answer as an unsigned decimal integer. When the true value has bit 63 set (i.e. ≥ 2^63), printing it as a signed decimal would look negative — make sure you emit the unsigned form.
