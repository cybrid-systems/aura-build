# Longest Increasing Subsequence

## Problem

Given a sequence of integers `a[1], a[2], ..., a[n]`, find the length of the **longest strictly increasing subsequence** (LIS).

A subsequence is obtained by selecting any subset of indices `i_1 < i_2 < ... < i_k` and keeping the corresponding values. It does *not* need to be contiguous.

Compute the length of the longest such subsequence where the values are strictly increasing.

## Input

A single line containing the sequence of space-separated integers. The list may be empty.

## Output

A single integer: the length of the longest strictly increasing subsequence. Output `0` for an empty input.

## Example

### Case 0

Input:
```
1 3 2 4 3 5
```

Output:
```
4
```

Explanation: one LIS is `1, 2, 4, 5` (or `1, 3, 4, 5`), of length 4.

### Case 1

Input:
```
5 4 3 2 1
```

Output:
```
1
```

Explanation: every subsequence with more than one element is non-increasing.

### Case 2

Input:
```
```

Output:
```
0
```

## Function Signature

```clojure
(solve [args])
```

`args` is the raw input string. Return the length of the LIS as an integer.

## Notes

- Use patience sorting with binary search: maintain an array `tails` where `tails[k]` is the smallest possible tail value of an increasing subsequence of length `k+1`. For each element `x`, find the leftmost index `k` such that `tails[k] >= x` (to enforce *strictly* increasing) and replace `tails[k]` with `x`. The answer is the final length of `tails`.
- This runs in **O(n log n)** time.
- For strict increasing, use the lower bound semantics in your binary search: replace the first element `>= x`, not `> x`.
