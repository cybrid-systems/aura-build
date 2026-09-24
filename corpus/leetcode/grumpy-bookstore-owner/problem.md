# Grumpy Bookstore Owner

## Problem

There is a bookstore, and its owner is grumpy. There are `n` customers queued up, and the owner has a "secret technique" that can suppress his grumpiness for `k` consecutive minutes. When the owner is not grumpy, customers are satisfied regardless of their patience. When he is grumpy, the `i`-th customer is satisfied only if `customers[i]` is less than or equal to their patience `grumpy[i]` (the customer may still wait up to that many minutes).

You are given two integer arrays `customers` and `grumpy` of length `n`, and an integer `k`. Initially, the owner is grumpy for all minutes. You may pick **one** contiguous window of `k` consecutive minutes during which the secret technique is active (the owner is not grumpy). Find the maximum total number of satisfied customers.

## Function Signature

```python
def solve(customers: list[int], grumpy: list[int], k: int) -> int:
    ...
```

## Input / Output Convention

The harness reads a single test case from `STDIN` in the form:

```
CASE0=customers=[1,0,1,2,1,1,7,5]; grumpy=[0,1,0,1,0,1,0,1]; k=3
```

- `customers` and `grumpy` are JSON-style integer arrays (no spaces inside the brackets).
- `k` is a plain integer.
- Output the single integer answer on its own line via `print`.

## Notes

- A customer is satisfied either naturally (grumpy minute, but `customers[i] <= grumpy[i]`) or because the technique covered their minute.
- `1 <= k <= n`, and `1 <= n <= 10^5`.
- Aim for `O(n)` time — a sliding window on the "extra" satisfaction gained by the technique works well.
