# Longest Common Prefix

## Problem

Given an array of strings, write a function to find the **longest common prefix** string that is shared amongst all strings in the array. A common prefix is a leading substring that appears at the start of every string in the input. If no such common prefix exists, return an empty string.

For example:
- Input: `["flower", "flow", "flight"]` → Output: `"fl"`
- Input: `["dog", "racecar", "car"]` → Output: `""`
- Input: `["intersect", "interstate", "intercom"]` → Output: `"inter"`

## Function Signature

```lisp
(defun solve (strs)
  ;; strs: list of strings (list of simple-strings)
  ;; returns: longest common prefix as a simple-string
  )
```

## Input / Output Convention

Input is provided as a single test case via the `CASE0` variable, a simple-string containing one entry per line:

```
CASE0="flower
flow
flight"
```

A blank line (`""`) terminates the list of strings. Parse `CASE0` by splitting on newlines, dropping the trailing empty line, and passing the resulting list to `solve`. The harness will compare the returned simple-string against the expected answer, and also report the per-test runtime.

## Notes

- An empty input list (only a terminating blank line) should return `""`.
- The result must be a valid common prefix of **every** string; a prefix of only some strings does not count.
- Aim for the simplest correct algorithm — sorting-then-compare and vertical / horizontal scanning are all acceptable. Only the correctness of the final answer is evaluated, not the algorithm used.
