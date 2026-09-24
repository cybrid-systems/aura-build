# Valid Parentheses

## Problem Statement

Given a string `s` consisting **only** of the characters `'('`, `')'`, `'['`, `']'`, `'{'`, and `'}'`, determine whether the parentheses are properly nested and balanced.

A string is considered **valid** if:

1. Every opening bracket is matched by a closing bracket of the same type.
2. Brackets are closed in the correct order (i.e., the most recently opened unmatched bracket must be closed first — LIFO order).
3. Every closing bracket has a corresponding opening bracket of the same type before it.

Return `true` if the string is valid, otherwise return `false`.

### Examples

| Input        | Output | Explanation                                   |
|--------------|--------|-----------------------------------------------|
| `"()"`       | `true` | Simple open/close pair.                       |
| `"()[]{}"`   | `true` | Three independent valid pairs.                |
| `"(]"`       | `false`| Opening `(` is closed by `]`.                 |
| `"([)]"`     | `false`| Brackets are interleaved, not properly nested.|
| `"{[]}"`     | `true` | Nested structure is valid.                    |
| `""`         | `true` | Empty string is trivially balanced.           |
| `"["`        | `false`| Unclosed opening bracket.                     |

## Function Signature

```text
solve(s: str) -> bool
```

## Input / Output Convention

The harness reads from a structured source (no stdin). Each case is provided as a single line:

```
CASE0=()
CASE1=()[]{}
CASE2=(]
CASE3=([)]
CASE4={[]}
CASE5=
CASE6=[
```

For each case, your `solve` function receives the string value (without the `CASEi=` prefix) and must return `true` or `false`.

## Notes

- The string may be empty (`""`); treat it as valid.
- Only the six bracket characters appear in the input — no need to validate other characters.
- A stack is the natural data structure for this problem: push opening brackets, and on a closing bracket check that the top of the stack matches its pair.
