# Reverse String

## Problem Statement

Given a string `s` represented as a list of characters, reverse the string **in-place** — meaning you must modify the input list directly without allocating another list of the same size.

The characters in the list represent the string in order. After the operation, the first character should become the last, the second character should become the second-to-last, and so on.

Your algorithm must use **O(1)** extra auxiliary space (a few pointers/variables are fine).

## Function Signature

```python
def solve(s: list[chr]) -> None:
    ...
```

The function should mutate `s` in-place and return nothing.

## Input/Output Convention (Aura Harness)

The harness reads from a single block of text lines in the format:

```
CASE0=s e t o f
CASE1=h e l l o
```

Each `CASEn=` line is followed by **exactly one** data line containing the elements of the list, separated by spaces. The harness will:

1. Parse each `CASE` line into a `list[chr]` called `s`.
2. Call `solve(s)`.
3. Print the resulting list on one line, space-separated, prefixed by `CASE0=` (or `CASEn=`).

For example, given the input:

```
CASE0=s e t o f
```

The expected output is:

```
CASE0=f o t e s
```

## Notes

- The list length is in the range `[1, 10^5]`.
- Characters may be any ASCII character, but the harness uses simple letter sequences for testing.
- Do **not** return a new list — modify `s` directly. The two-pointer swap approach (left/right indices moving toward the center) is the canonical O(1)-space solution.
