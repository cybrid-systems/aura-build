# Minimum Window Substring

## Problem

Given two strings `s` and `t`, find the smallest contiguous substring of `s` that contains every character from `t` (each character appearing at least as many times as it appears in `t`). Any relative ordering of the characters inside the window is acceptable.

Return the substring itself, or the empty string `""` if no such window exists.

## Function Signature

```
(solve s t)
  s : string   ;; the source string
  t : string   ;; the multiset of required characters
  -> string    ;; the minimum window substring, or "" if none exists
```

## Input / Output Convention

This problem uses the **Aura string harness**, which streams cases line-by-line on a single stdin. Each case arrives as two lines:

```
CASE0=<s>
CASE0=<t>
CASE1=<s>
CASE1=<t>
...
```

The harness automatically aligns the two lines of every case using the shared `CASEn=` prefix; your `solve` function only ever sees the raw payload strings. Decode the case as follows:

```
s, t = raw_payload.splitlines()      ;; s is line 1, t is line 2
```

Emit one line per case containing the answer for that case. No index, no prefix, no extra whitespace — just the substring (or `""`).

## Notes

- The window must be a *contiguous* slice of `s`; permutations or subsequences do not count.
- Characters may repeat. Treat `t` as a **multiset**: a window is valid only when every distinct character in `t` appears at least as many times in the window as it does in `t`.
- If multiple windows share the minimum length, any one of them is acceptable.
- An empty `t` returns `""` by convention.
