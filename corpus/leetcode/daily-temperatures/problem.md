# Daily Temperatures

## Problem

Given an array `temps` of daily temperatures, for each day `i` compute the number of days you must wait until a warmer temperature occurs. If no such future day exists, use `0`.

Formally, for each index `i`, find the smallest `j > i` such that `temps[j] > temps[i]`, and output `j - i`. If no such `j` exists, output `0`.

## Function Signature

```
(solve [temps])
```

- `temps`: vector of integers (length `n`, `1 <= n <= 10^5`, `-100 <= temps[i] <= 100`).
- Returns a vector of integers of the same length where position `i` holds the wait count `j - i`, or `0` if none.

## Input

The Aura harness supplies a single case via standard input, formatted as:

```
CASE0=<json-array-of-temps>
```

For example:

```
CASE0=[73,74,75,71,69,72,76,73]
```

The solution must read this single `CASE0=` line and parse the JSON array as the `temps` argument.

## Output

Print the resulting vector as a JSON array on one line, for example:

```
[1,1,4,2,1,1,0,0]
```

## Notes

- Expected time complexity is `O(n)` using a monotonic (decreasing) stack of indices. Brute force `O(n^2)` will be too slow for the upper bound.
- Values may be negative; do not assume strictly positive temperatures.
- Multiple correct answers cannot exist; output is uniquely determined by the input.
