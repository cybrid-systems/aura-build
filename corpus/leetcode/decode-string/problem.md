# Decode String

## Problem

An encoded string is given where letters are grouped with repetitions written in the form `k[encoded_string]`, where `k` is a non-negative integer and `encoded_string` is a sequence of letters and/or further such groups. The integer `k` is guaranteed to fit in a 32-bit signed integer.

Your task is to decode the string and return its fully expanded form. The decoded string contains only lowercase English letters and has no square brackets.

## Examples

- `3[a]2[bc]` → `aaabcbc`
- `3[a2[c]]` → `accaccacc`
- `2[abc]3[cd]ef` → `abcabc.cdcd.cdcd.ef` ... actually `abcabccdcdcdef`

## Function Signature

```lisp
(defun solve (s)
  ;; returns the decoded string
  )
```

## Input

A single line read from `*standard-input*` containing the encoded string `s`.

- `1 ≤ |s| ≤ 30`
- `s` consists only of digits `0-9`, lowercase English letters `a-z`, and the characters `[` and `]`.
- Every decoded length is guaranteed to be ≤ 10^5.

## Output

Print the decoded string to `*standard-output*`.

## I/O Convention (Harness)

The harness sets up the input as follows:

```
CASE0=3[a2[c]]
CASE1=2[abc]3[cd]ef
CASE2=10[a]
```

Each line beginning with `CASEi=` is consumed; the value after `=` is passed to `solve` as the argument `s`, and the string returned by `solve` is compared to the expected decoded output.

## Notes

- The repetition count `k` may have multiple digits; accumulate them until you hit `[`.
- Nested groups are allowed; a stack-based approach (pushing partial results and counts) is the typical pattern.
- After closing a bracket, repeat the current group's string `k` times and append it to the parent group's partial result.
