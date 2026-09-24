# Partition Array Into Three Parts With Equal Sum

## Problem

You are given an array of `n` integers, `arr`. Determine whether it can be split into three **contiguous** (non-overlapping, covering every element) parts whose sums are all equal.

Formally, find indices `i` and `j` (`1 ≤ i < j ≤ n−1`) such that:

```
sum(arr[0..i]) == sum(arr[i+1..j]) == sum(arr[j+1..n-1])
```

Return `"YES"` if such a partition exists, otherwise `"NO"`.

## Function Signature

```clojure
(solve arr)
```

- `arr` — a vector of integers (may contain negative values).
- Returns a string: `"YES"` or `"NO"`.

## Input

The harness reads from `CASE0`. The value following `CASE0=` is the JSON-encoded array, e.g.:

```
CASE0=[0,2,1,-6,6,-7,9,1,2,0,1]
```

## Output

Write a single line to stdout:

```
YES
```

or

```
NO
```

## Notes

- Each element is an integer in the range `[-10^4, 10^4]`; length of the array is between `1` and `10^5`.
- If the total sum of the array is not divisible by `3`, the answer is immediately `"NO"`.
- When the array size is less than `3`, it is impossible to form three non-empty contiguous parts, so the answer is `"NO"`.
