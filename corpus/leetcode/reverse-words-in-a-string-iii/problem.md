# Reverse Words in a String III

## Problem

You are given a lowercase string `s` consisting of letters and spaces. Words are separated by exactly one space. For every word in the string, reverse the characters **within** that word, while keeping the words themselves (and the spaces) in their original positions.

The operation must be performed **in place** using the two-pointer technique on each word independently.

## Function Signature

```scheme
(define (solve s)
  ;; s is a mutable string (or bytevector) of lowercase letters and spaces.
  ;; Reverse each word in place and return the modified string.
  )
```

## Input Convention

- A single test case is provided as the program argument string.
- The input has no quotes; it is a single line read from stdin in standalone mode, or passed directly to the harness.
- **CASE0=**`abc def` → expected output **CASE0=**`cba fed`
- **CASE1=**`the sky is blue` → expected output **CASE1=**`eht yks si eulb`
- **CASE2=**`a` → expected output **CASE2=**`a`

## Output Convention

Print the transformed string followed by a newline.

## Notes

- Words are separated by exactly one space; no leading or trailing spaces.
- Use a left and right pointer that converge on each word, swapping characters, then advance both pointers past the next space.
- Time complexity should be O(n) and space complexity O(1) auxiliary.
