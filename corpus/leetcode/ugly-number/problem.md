# Ugly Number

## Problem

A positive integer `n` is called an *ugly number* if its prime factors are limited to `2`, `3`, and `5`. Given a positive integer `n`, determine whether it is ugly.

Formally, `n` is ugly if and only if `n > 0` and after repeatedly dividing `n` by `2`, `3`, and `5` (any number of times, in any order), the result is exactly `1`.

## Function Signature

```scheme
(define (solve n) -> boolean?)
```

- `n`: a positive integer.
- Return `#t` if `n` is an ugly number, otherwise `#f`.

## Input / Output

The harness feeds the function directly. For local testing, use this convention:

```
CASE0=6
CASE0_ANS=#t
CASE1=14
CASE1_ANS=#f
CASE2=1
CASE2_ANS=#t
CASE3=0
CASE3_ANS=#f
```

## Notes

- `1` is considered ugly (it has no prime factors, so the condition is vacuously satisfied).
- `0` and negative integers are **not** ugly (they are not positive).
- A single brute-force approach is to keep dividing `n` by `2`, then `3`, then `5` while divisible; if the remainder is `1`, it is ugly.
- Be careful with negative inputs if your environment allows them — the definition above restricts `n` to positive integers only.
