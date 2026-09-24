# Valid Palindrome

## Problem Statement

Given a string `s`, determine whether it is a **palindrome** after the following normalization:

- Consider **only alphanumeric characters** (letters `a-z`, `A-Z`, and digits `0-9`).
- **Ignore letter case**, i.e., treat `'A'` and `'a'` as the same character.

Return `true` if the normalized sequence reads the same forward and backward, otherwise return `false`.

### Examples

- `"A man, a plan, a canal: Panama"` → `true`
  (After normalization: `"amanaplanacanalpanama"`)
- `"race a car"` → `false`
  (After normalization: `"raceacar"` vs `"racaecar"`)
- `" "` → `true`
  (Empty sequence after normalization is trivially a palindrome)
- `"0P"` → `false`
  (`'0'` vs `'P'` after lowercasing)

## Function Signature

```haskell
solve :: String -> Bool
```

- Input: a single `String` provided as the only line of the case.
- Output: a `Bool` — `True` if the string is a valid palindrome under the rules above, `False` otherwise.

## I/O Convention (CASE format)

The Aura harness feeds a single case at a time. The expected `STDIN` lines look like:

```
CASE0=<the input string, possibly empty>
```

Your `solve` function receives the string after the `CASE0=` prefix (the harness strips it for you). You should write the boolean result to `STDOUT` as `True` or `False`.

## Notes

- An empty string or a string containing only non-alphanumeric characters is considered a palindrome.
- Be careful with Unicode / non-ASCII input: this problem is defined over ASCII alphanumerics only.
- Complexity target: **O(n)** time, **O(1)** extra space (two-pointer approach), though a filter-and-reverse solution is also acceptable.
