# Count Primes

Given a non-negative integer `n`, count the number of prime numbers strictly less than `n`.

A prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself.

Your task is to compute this count efficiently. A naive check for each number will likely be too slow for the upper range of inputs; an O(n log log n) sieve-based approach is recommended.

## Function Signature

```
(solve n)
```

- `n` — a non-negative integer (`0 <= n <= 5_000_000` is a reasonable bound to keep runtime snappy).

Return the number of primes `p` such that `p < n`.

## Input / Output

The harness invokes `(solve n)` directly. The `CASE0` lines below illustrate the calling convention used by the test runner:

```
CASE0=10
CASE0=0
CASE0=1
CASE0=2
CASE0=100
```

For each case, the harness prints the value returned by `solve`.

## Examples

| n     | Output | Primes < n                          |
|-------|--------|-------------------------------------|
| 10    | 4      | 2, 3, 5, 7                          |
| 0     | 0      | —                                   |
| 1     | 0      | —                                   |
| 2     | 1      | 2                                   |
| 100   | 25     | 2, 3, 5, 7, 11, …, 97              |

## Notes

- `n` itself is **not** counted, even if it is prime (the count is strictly less than `n`).
- Use the Sieve of Eratosthenes for an efficient solution; a boolean array of size `n` is sufficient.
- Edge cases: `n <= 2` should return `0`.
