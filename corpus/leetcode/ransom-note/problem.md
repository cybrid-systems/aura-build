# Ransom Note

## Problem

Given two strings, `ransomNote` and `magazine`, determine whether the `ransomNote` can be constructed by using the letters from the `magazine`. Each letter in the `magazine` can only be used once in the `ransomNote`.

Return `true` if the `ransomNote` can be constructed, otherwise return `false`.

## Function Signature

```python
def solve(ransomNote: str, magazine: str) -> bool:
```

## Input

The harness reads a single test case from the input. The first line contains `ransomNote` and the second line contains `magazine`. Both strings consist only of lowercase English letters.

Lines use the form:

```
CASE0_RANSOMNOTE=<ransomNote string>
CASE0_MAGAZINE=<magazine string>
```

## Output

Print `true` if the `ransomNote` can be built from the letters of `magazine`, otherwise print `false`.

## Examples

Example 1:
- Input:
  ```
  a
  b
  ```
- Output:
  ```
  false
  ```

Example 2:
- Input:
  ```
  aa
  ab
  ```
- Output:
  ```
  false
  ```

Example 3:
- Input:
  ```
  aa
  aab
  ```
- Output:
  ```
  true
  ```

## Notes

- If the length of `ransomNote` exceeds the length of `magazine`, the answer must be `false` (a quick early-exit check is useful).
- A frequency counter (hash map / array of size 26) over the characters in `magazine` is sufficient; for each character in `ransomNote`, decrement its count and fail if any count drops below zero.
