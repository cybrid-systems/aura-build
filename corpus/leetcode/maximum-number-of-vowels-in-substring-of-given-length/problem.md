# Maximum Number of Vowels in Substring of Given Length

## Problem

Given a string `s` consisting of lowercase English letters and an integer `k`, find the **maximum** number of vowels (i.e., `'a'`, `'e'`, `'i'`, `'o'`, `'u'`) that appear in any contiguous substring of `s` whose length is exactly `k`.

If `s` has fewer than `k` characters, return `0`.

## Function Signature

```clojure
(defn solve [s k] ...)
```

- `s`: a string of lowercase English letters.
- `k`: a positive integer (the substring length).
- Returns the maximum vowel count over all length-`k` substrings of `s`.

## Input

The input consists of **multiple test cases**. Each test case is given as two lines:

```
CASE0=<s>
<k>
```

where `<s>` is a non-empty lowercase string and `<k>` is a non-negative integer. Read until EOF.

For each test case, output one line containing the maximum vowel count.

## Output

For each case, print a single integer — the answer for that case. Each answer is printed on its own line.

## Example

Input:
```
CASE0=abciiidef
3
CASE0=aeiou
2
```

Output:
```
3
2
```

## Notes

- Use a sliding window of size `k` to achieve **O(|s|)** time per case.
- Vowel check can be a small lookup set: `#{a e i o u}`.
- The result is always between `0` and `min(k, |s|)` inclusive.
