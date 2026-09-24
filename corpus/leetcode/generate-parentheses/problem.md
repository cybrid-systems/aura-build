# Generate Parentheses

Given an integer `n`, generate **all** combinations of well-formed parentheses using exactly `n` pairs of opening and closing brackets.

A string of parentheses is *well-formed* when every opening bracket `(` has a matching closing bracket `)` that appears later in the string, and the parentheses are properly nested (no closing bracket appears before its matching opening bracket).

Your task is to return every valid combination.

## Function Signature

```lisp
(solve N)
```

- `N` — a non-negative integer representing the number of parenthesis pairs.

Returns a list (or vector) of strings, each string being a unique well-formed parenthesis combination of length `2 * N`. The order of the results does not matter, but the list must contain **all** such combinations exactly once.

## Input / Output Convention

Input is provided via the `CASE0` environment variable as a single line:

```
CASE0=3
```

The harness will set `CASE0` before invoking your solution. Parse the integer `N` from this line.

Output is written to stdout as the chosen container literal containing all valid combinations. For example, when `N = 3`, a valid output is:

```
["((()))","(()())","(())()","()(())","()()()"]
```

## Notes

- For `N = 0`, the expected output is a list containing exactly one element: the empty string `""`.
- The number of valid combinations is the *N*-th Catalan number, which grows quickly (e.g., `N = 10` yields 16796 combinations). Make sure your solution scales and does not produce duplicates.
- Backtracking with two counters — one for the number of `(` placed and one for the number of `)` placed — is the standard approach: you may add an opening bracket while you still have some left, and a closing bracket only when there are unmatched opening brackets already placed.
