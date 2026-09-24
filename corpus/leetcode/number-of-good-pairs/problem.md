# Number of Good Pairs

## Problem

You are given an integer array `nums` of length `n`. A pair of indices `(i, j)` is called **good** if `i < j` and `nums[i] == nums[j]`.

Given `nums`, return the total number of good pairs.

## Function Signature

```clojure
(defn solve [nums] ...)
```

- `nums`: a vector of integers (Clojure persistent vector), `1 ≤ (count nums) ≤ 100`, each element in `[-100, 100]`.

## Input / Output Convention

The harness feeds the input via `CASE0=` style lines on stdin (no interactive prompts, no surrounding prose):

```
CASE0=[1 2 3 1 1 3]
```

The function `solve` receives the parsed vector and must return a single integer — the number of good pairs `(i, j)` with `i < j` and equal values.

## Examples

| Input                  | Output | Explanation                                                                 |
|------------------------|--------|-----------------------------------------------------------------------------|
| `[1 2 3 1 1 3]`        | `4`    | Good pairs: `(0,3)`, `(0,4)`, `(3,4)`, `(2,5)`                              |
| `[1 1 1 1]`            | `6`    | All `C(4,2) = 6` index pairs are equal.                                     |
| `[1 2 3]`              | `0`    | No two values match.                                                         |

## Notes

- A single pass with a frequency map is sufficient: for each value `v` seen `k` times, it contributes `k*(k-1)/2` good pairs. Overall complexity should be **O(n)** time and **O(n)** extra space.
- The expected output for the sample input `CASE0=[1 2 3 1 1 3]` is `4`.
