# Get Equal Substrings Within Budget

## Problem

You are given two strings `s` and `t` of equal length `n`, and an integer `maxCost`. You want to convert `s` into `t` by changing characters one position at a time. Changing the character at position `i` costs `|s[i] - t[i]|` (the absolute difference of their ASCII codes).

You may perform any subset of changes, but the **total cost** of all changes made must not exceed `maxCost`. A substring `s[i..j]` is considered "convertible" if every character in that range can be changed (i.e., the sum of `|s[k] - t[k]|` for `k` in `[i, j]` is at most `maxCost`).

Find the length of the longest contiguous substring of `s` whose total conversion cost does not exceed `maxCost`.

## Function Signature

```haskell
solve :: String -> String -> Int -> Int
```

- The first argument is string `s`.
- The second argument is string `t`.
- The third argument is `maxCost`.
- Return the maximum length of a contiguous substring of `s` (equivalently of `t`, since they share the same indices) whose total change cost fits within the budget.

## Input

The input is provided directly on stdin as argument-style lines (no prompts):

```
CASE0=s,t,maxCost
CASE1=s,t,maxCost
...
```

For each case:
- Line format: `CASE<i>=<s>,<t>,<maxCost>`
- `s` and `t` contain no commas (only printable ASCII letters/digits).
- `maxCost` is a non-negative integer.

Read cases until EOF. For each case, print the answer on its own line in the form:

```
CASE<i>=<answer>
```

## Notes

- Both `s` and `t` have the same length; you may assume `1 ≤ n ≤ 10^5` per case.
- A classic sliding-window / two-pointer approach works in `O(n)` per case: expand the right end, accumulate cost, and shrink the left end while the cost exceeds `maxCost`.
- The cost at each position is `abs (ord s[i] - ord t[i])`, which fits comfortably in an `Int`.
