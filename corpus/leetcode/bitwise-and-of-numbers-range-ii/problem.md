# Bitwise AND of Numbers Range II

Given two integers `m` and `n` with `0 <= m <= n <= 2^31 - 1`, compute the bitwise AND of every integer in the inclusive range `[m, n]`.

In other words, return:

```
m & (m+1) & (m+2) & ... & (n-1) & n
```

## Function Signature

```
(solve [m n] -> int)
```

A single call is made with the arguments bound in a vector.

## Input

Input is provided through the harness in the `CASE0=...` format, one expression per binding. A typical line looks like:

```
CASE0=[5 7]
```

The harness will destructure the case into `[m n]` and invoke `(solve [m n])`.

## Output

Return the integer result of the bitwise AND over the entire range.

## Notes

- The trivial `O(n - m)` fold is far too slow for large ranges; aim for `O(log(max(m,n)))` by repeatedly clearing the lowest differing bit between `m` and `n`.
- When `m == n`, the result is just `m` (ANDing a single number).
- Edge case: `m == 0` always yields `0`, since `0` is included in the range.
- All values fit comfortably in a signed 32-bit integer; be mindful of negative-looking bit patterns if the host language uses two's-complement signed integers.
