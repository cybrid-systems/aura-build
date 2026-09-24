# Container With Most Water

## Problem

You are given an integer array `heights` where `heights[i]` represents the height of a vertical line drawn at coordinate `i` on the x-axis. The width between line `i` and line `j` is `|i - j|`.

Choose two distinct lines that, together with the x-axis, form a container holding the most water. Return the maximum possible area (in square units).

The area formed by lines at indices `i` and `j` (with `i < j`) is:

```
area = (j - i) * min(heights[i], heights[j])
```

## Function Signature

```clojure
(defn solve [heights]
  ;; returns the maximum water container area as a Long
  )
```

## Input

The input is provided as a single `CASE0` line on standard input:

```
CASE0=heights
```

- `heights` is a Clojure vector literal containing integers, e.g. `[1 8 6 2 5 4 8 3 7]`.
- The vector has at least 2 elements.
- Each element fits in a 32-bit signed integer (non-negative).
- Length of the vector is at most 100,000.

## Output

Print a single integer (or `Long` token) to standard output: the maximum area achievable.

## Examples

```
CASE0=[1 8 6 2 5 4 8 3 7]
=> 49
```

Explanation: choosing indices `1` (height `8`) and `8` (height `7`) gives area `(8 - 1) * min(8, 7) = 7 * 7 = 49`.

```
CASE0=[1 1]
=> 1
```

## Notes

- A two-pointer approach starting at the two ends runs in `O(n)` time after sorting is not needed (the array order is fixed).
- The answer always fits in a 64-bit signed integer when interpreted as a `Long`, but printing it as a plain integer literal is fine for typical inputs.
- Indices in the vector are 0-based; use the distance between indices as the width.
