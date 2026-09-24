# Rotate Array by K

## Problem

You are given an array of `n` integers and an integer `k`. Rotate the array to the right by `k` steps, modifying it in-place (no extra array of size `n` allowed). Rotating right by one step moves every element one position to the right, with the last element wrapping around to the front.

Rotation must be performed `k mod n` steps; if `k` is larger than `n`, only the effective rotation matters.

## Function Signature

```clojure
(defn solve [arr k] ...)
```

- `arr` — a vector (Clojure) / list / mutable array of integers.
- `k` — non-negative integer.
- Returns the rotated sequence (or mutates and returns `arr`, depending on the harness).

## Input

The harness reads the case from a literal source. Each case uses the form:

```
CASE0=[1,2,3,4,5,6,7] k=3
```

- The array is provided in JSON-like bracket form on the `CASE0=` line.
- `k` is provided on a separate `k=` line.
- The case is a single test; multi-case is not expected.

## Output

Print the rotated array in the same bracket format, one line, followed by a newline:

```
[5,6,7,1,2,3,4]
```

## Example

Input
```
CASE0=[1,2,3,4,5,6,7]
k=3
```

Output
```
[5,6,7,1,2,3,4]
```

## Notes

- Aim for O(n) time and O(1) extra space (excluding the output buffer).
- The classic three-reverse trick works here: reverse the whole array, then reverse the first `k` and the remaining `n-k` segments.
- Treat `k >= n` by reducing with `(mod k n)` before rotating; if `n == 0`, return the array unchanged.
- The harness prints the result directly, so ensure the return value serializes to the bracket form shown above.
