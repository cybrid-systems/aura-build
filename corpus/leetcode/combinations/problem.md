# Combinations

## Problem

Given two integers `n` and `k`, return all possible combinations of `k` numbers chosen from the range `1` to `n`.

You may return the combinations in any order.

## Function Signature

```clojure
(solve n k)
```

- `n` — the upper bound of the range (inclusive), `1 <= n <= 20`.
- `k` — the size of each combination, `1 <= k <= n`.

Returns a sequence of combinations, where each combination is a sequence of `k` distinct integers in strictly increasing order, drawn from `1..n`.

## Input

The input is provided via the `CASE0` environment variable as a single line:

```
CASE0=n k
```

For example:

```
CASE0=4 2
```

## Output

Print the result to stdout as a single line. Each combination is printed as space-separated integers enclosed in square brackets, and combinations are separated by commas. For the example above, the output is:

```
[1 2],[1 3],[1 4],[2 3]
```

## Notes

- The function should generate combinations in lexicographic order to ensure deterministic output, though any order is acceptable by the problem statement.
- Use backtracking: at each step, choose the next element and recurse on the remaining range, pruning branches when the combination already has `k` elements.
- If `k > n`, return an empty result.
