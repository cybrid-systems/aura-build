# Rearrange String k Distance Apart

## Statement

Given a string `s` consisting of lowercase English letters and an integer `k`, rearrange the characters of `s` so that any two occurrences of the **same** character are at least `k` positions apart in the new string. Return any valid rearrangement as a string, or return an empty string `""` if no such rearrangement exists.

The original relative ordering among distinct characters does **not** need to be preserved; only the "at least `k` apart" rule must hold.

## Function Signature

```haskell
solve :: String -> Int -> String
```

- The first argument is the input string `s` (1 ≤ |s| ≤ 10^5).
- The second argument is the integer `k` (1 ≤ k ≤ |s|).

## Input / Output Convention

Input is read from standard input, one test case:

```
s
k
```

`s` is a single line containing the string. `k` is on the next line as an integer.

Output a single line containing the rearranged string, or `""` if impossible.

### Example

Input:
```
aabbcc
3
```

Output:
```
abcabc
```

Here each letter (`a`, `b`, `c`) repeats twice and the two copies of every letter are exactly 3 positions apart.

## Notes

- If a character appears more than `(n + k - 1) / k` times (where `n = |s|`), it is immediately impossible; you can short-circuit.
- A natural greedy approach repeatedly picks the currently available character with the highest remaining count that is not still "cooling down" from its last placement.
- Aim for `O(n log c)` where `c ≤ 26`; a priority queue plus a cooldown queue is sufficient.
