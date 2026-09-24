# Remove All Adjacent Duplicates in String

## Problem

You are given a string `s` consisting of lowercase English letters. Repeatedly perform the following operation until the string stops changing:

- If two **adjacent** characters in the string are equal, remove both of them.

Return the final string after no more deletions can be made. The order of the remaining characters is preserved.

## Function Signature

```python
def solve(s: str) -> str:
    ...
```

## Input

A single line containing the string `s` (only lowercase letters, length `1 ≤ |s| ≤ 1000`).

```
CASE0=abbaca
CASE1=azxxzy
```

## Output

For each test case, print the final string after all possible adjacent-duplicate removals.

```
abca
ay
```

## Notes

- A stack works naturally: push each character, and pop it if the top of the stack equals the incoming character.
- After processing the whole string, join the stack contents to form the answer.
- Edge case: if all characters are deleted, output an empty line.
