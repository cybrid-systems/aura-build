# Tuple with Same Product

## Problem

You are given an array `nums` of **distinct** integers. Count the number of ordered tuples `(a, b, c, d)` of **four distinct elements** taken from `nums` (positions matter, values are distinct) such that:

```
nums[a] * nums[b] == nums[c] * nums[d]
```

Note that `(a, b, c, d)` and `(b, a, c, d)` are considered different ordered tuples, as are `(a, b, d, c)`, etc. — only the equality of the product of the first two and the product of the last two positions matters, along with the distinctness constraint.

Return the total count of such tuples.

## Function Signature

```clojure
(defn solve [nums] ...)
```

- `nums` — a Java `int[]` (or vector of integers) of length `n` (`2 ≤ n ≤ 1000`), all values distinct.
- Return: a single integer `long` — the number of valid ordered tuples. The answer fits in 64-bit signed integer.

## Input

The harness feeds `solve` directly; there is no `stdin`. Each test case is a single array. The harness evaluates your solution on multiple cases.

## I/O Convention (Harness)

```
CASE0=
[1,2,3,4,5,6]
EXPECT0=8
CASE1=
[2,3,4,6]
EXPECT1=8
```

- `CASE0=` and following lines: a literal Clojure vector representing `nums`.
- `EXPECT0=` followed by the expected `long` return value.

## Notes

- A standard approach: count how many unordered pairs `(i,j)` with `i<j` produce each product `p`. If `cnt[p] = k`, then the number of ordered pairs of pairs with product `p` is `k * (k-1) * 2` (pick two distinct unordered pairs — order matters between the two pairs), and each selection yields `2 * 2 = 4` ordered `(a,b,c,d)` tuples (swaps within each pair). Equivalently the contribution is `cnt[p] * (cnt[p] - 1) * 8`.
- Watch out for overflow in the per-product counts before the final multiplication; use `long` arithmetic throughout.
- Distinctness of values guarantees no pair `(i,j)` duplicates another in `nums` order, but does **not** eliminate products like `1*6 == 2*3`.
