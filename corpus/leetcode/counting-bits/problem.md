# Counting Bits

## Problem

Given an integer `n`, return an array `ans` of length `n + 1` such that `ans[i]` equals the number of `1` bits in the binary representation of `i`, for every `i` from `0` to `n` inclusive.

In other words, compute the **population count** (also known as the Hamming weight) for every integer in the range `[0, n]`.

## Function Signature

```clojure
(defn solve [n] ...)
```

- `n` — a non-negative integer (`0 ≤ n ≤ 100_000`).
- Returns — a vector of length `n + 1` where the element at index `i` is `popcount(i)`.

## Input / Output Convention

This problem is run in a **stdin-less harness**. Your solution is invoked directly with a single argument. Reference cases are encoded as follows:

```
CASE0=2 -> [0 1 1]
CASE1=5 -> [0 1 1 2 1 2]
CASE2=0 -> [0]
CASE3=1 -> [0 1]
CASE4=7 -> [0 1 1 2 1 2 2 3]
```

Each line specifies one call of the form `(solve N)` followed by `->` and the expected output vector.

## Notes

- The output vector must include the entry for `0`, which is always `0`.
- A naive `O(n * log n)` approach (popcount each `i` independently) is acceptable for the given limits, but an `O(n)` dynamic programming solution is also possible using the recurrence `bits[i] = bits[i >> 1] + (i & 1)`.
- All output values are small non-negative integers; the result vector's length is always exactly `n + 1`.
