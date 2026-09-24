# Random Pick with Weight

## Problem

You are given an array of positive integer weights `w` of length `n`. Design an algorithm that picks an index `i` in `[0, n-1]` with probability proportional to `w[i]`.

That is, for each call to `pickIndex`, the chance of returning index `i` must equal `w[i] / S`, where `S = sum(w)`.

You may assume the array is fixed after construction. Multiple calls to `pickIndex` must be independent and follow the same distribution.

## Function Signature

```clojure
(solve w)
;; returns a map with:
;;   :pickIndex (fn [] -> integer)
```

The constructor takes the immutable weight array `w` and returns an object exposing `pickIndex`.

## I/O Convention

The harness provides a single function call:

```
CASE0=construct=[1,3,2,4]
CASE0=calls=pickIndex,pickIndex,pickIndex,pickIndex,pickIndex
CASE0=expect=distribution
```

- `construct` is a JSON-style list of integers (the weights).
- `calls` is a comma-separated list of method names to invoke in order. Each call here must execute the underlying method and the returned indices are checked against the expected statistical distribution.
- `expect=distribution` means the harness will run the sequence many times internally and verify the empirical frequency of each returned index matches `w[i] / S` within a tolerance. No literal expected array is required.

## Notes

- Preprocessing (e.g., prefix sums) is allowed during construction; each `pickIndex` call must run in `O(log n)`.
- Use a deterministic PRNG seeded from a fixed value so runs are reproducible; the harness will run many trials and aggregate frequencies.
- Total weight fits comfortably in a standard integer range; use 64-bit arithmetic to be safe.
- Multiple distinct correct implementations are acceptable as long as the distribution is correct and `pickIndex` is `O(log n)`.
