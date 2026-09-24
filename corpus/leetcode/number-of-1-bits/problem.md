# Number of 1 Bits

## Problem

Write a function that takes an unsigned 32-bit integer and returns the number of `'1'` bits it has (also known as the Hamming weight or population count).

## Function Signature

```clojure
(defn solve [n] ...)
```

- `n` — an unsigned 32-bit integer (`0 <= n <= 2^32 - 1`).

Return the count of bits set to `1` in the binary representation of `n`.

## Input Convention

This problem is **stdin-less**. The harness calls your `solve` function directly with a single argument.

For debugging in the REPL, you may assume a `CASE0=...` style line, e.g.:

```
CASE0=11
CASE1=4294967293
```

where `CASE0` should return `3` (since `11` is `0b1011`) and `CASE1` should return `32` (since `4294967293` is `0xFFFFFFFF`).

## Output

Return the Hamming weight of `n` as a non-negative integer.

## Notes

- Treat the input as **unsigned**; do not interpret the high bit as a sign.
- Several approaches are possible: bit-by-bit scan, clearing the lowest set bit with `n & (n - 1)`, or a built-in popcount if your language provides one.
- Aim for an `O(number of set bits)` solution using the `n & (n - 1)` trick.
