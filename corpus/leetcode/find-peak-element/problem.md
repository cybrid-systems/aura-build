# Find Peak Element

## Problem Statement

A **peak element** in an array is an element that is strictly greater than its immediate neighbors. More precisely, an element `arr[i]` is a peak if:

- `arr[i] > arr[i-1]` (when `i > 0`), and
- `arr[i] > arr[i+1]` (when `i < n-1`).

For boundary elements, only the one existing neighbor is considered (e.g., `arr[0]` is a peak if `arr[0] > arr[1]`, and `arr[n-1]` is a peak if `arr[n-1] > arr[n-2]`).

You are guaranteed that the input array contains **at least one peak element**.

Your task is to return the **index** of any single peak element.

## Requirements

- Achieve **O(log n)** time complexity using a binary-search style approach.

## Function Signature

```clojure
(solve arr)
```

- `arr`: a vector of integers (length `n ≥ 1`).
- Returns: a single integer — the index of a peak element.

## Input / Output Convention (stdin-less)

Each test case is provided as a single line with the prefix `CASE0=` followed by a space-separated list of integers:

```
CASE0= 1 2 3 1
```

The harness will invoke `(solve arr)` where `arr` is the parsed vector of integers from the line (excluding the `CASE0=` prefix). Output the returned index as a single integer.

### Examples

```
CASE0= 1 2 3 1
```
Output: `2` (or `1`, both are valid peaks)

```
CASE0= 1 2 1 3 5 6 4
```
Output: `5` (or `1`)

```
CASE0= 1
```
Output: `0`

## Notes

- The answer is not unique; any valid peak index is accepted.
- The array boundaries wrap conceptually — outside the array is treated as `-∞`, which is why a peak is always guaranteed to exist.
- Aim for an iterative binary-search solution comparing the middle element with its right neighbor to decide which half must contain a peak.
