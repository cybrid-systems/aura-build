# Queue Reconstruction by Height

## Problem

You are given a queue of people standing in a line. Each person has two attributes:
- `h`: their height (in cm)
- `k`: the number of people in front of them who are taller than or equal to their height

The original queue got shuffled, and you only know the `(h, k)` pair for each person. Your task is to reconstruct the original queue ordering.

Formally, given a set of pairs `(h, k)`, produce an ordering of them such that for every person at position `i` (0-indexed), exactly `k` of the people before them have height `≥ h`. All `(h, k)` pairs are guaranteed to be valid (i.e., at least one ordering exists) and all pairs are distinct.

## Function Signature

```clojure
(solve people) -> [vector?]
```

- `people`: a vector of `[h k]` pairs (each pair is a 2-element vector of integers).
- Returns: a single vector containing the original `[h k]` pairs in the reconstructed order.

## Input / Output

The harness runs with `CASE0=...` style invocation, so no stdin/stdout is used. Each case is provided as a Clojure literal:

```
CASE0=[[[7 0] [4 4] [7 1] [5 0] [6 1] [5 2]]]
```

Each inner vector element is a `[h k]` pair. The expected output for the example is one valid reconstructed ordering of those pairs.

## Notes

- A standard greedy approach works: sort the people in decreasing order of height, then insert each person at index `k` in the result list.
- When heights tie, the relative ordering among equal-height people does not matter as long as the `k` invariant is preserved.
- Time complexity `O(n²)` is acceptable for typical constraints; an `O(n log n)` solution using a Fenwick tree or order-statistic tree is also possible.
