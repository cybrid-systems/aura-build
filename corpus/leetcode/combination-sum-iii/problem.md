# Combination Sum III

## Problem

Find all valid combinations of `k` numbers chosen from the digits `1` through `9` (each digit used **at most once**) whose sum equals `n`.

Return all such combinations as a list of lists of integers. The order of combinations in the result does not matter, and within each combination the numbers must be sorted in ascending order.

If no valid combination exists, return an empty list.

## Constraints

- `2 ≤ k ≤ 9`
- `1 ≤ n ≤ 60`
- All numbers in each combination are distinct and drawn from `{1, 2, ..., 9}`.

## Function Signature

```clojure
(defn solve [k n]
  ;; returns seq of combinations (each a seq of integers)
  )
```

## Input / Output Convention

The harness reads from `CASE0` style input. Each case is two integers: `k` then `n`.

Input format:
```
CASE0=3 7
CASE1=3 9
CASE2=4 1
```

Each `CASE<n>=` line provides the two arguments for `solve` in order: `k` followed by `n`. Output each combination on its own line (numbers space-separated), and separate cases with a blank line. An empty result should produce a blank line for that case.

## Examples

- `solve 3 7` → `[[1,2,4]]`
- `solve 3 9` → `[[1,2,6], [1,3,5], [2,3,4]]`
- `solve 4 1` → `[]` (impossible since the minimum sum of 4 distinct digits 1..4 is 10)

## Notes

- Since the digit pool is fixed at `1..9`, the search space is small enough to explore exhaustively with backtracking.
- Pruning candidates whose partial sum already exceeds `n`, or whose remaining positions cannot possibly reach `n`, will keep the search efficient.
- Outputting combinations in ascending order (both within and across combinations) makes results deterministic.
