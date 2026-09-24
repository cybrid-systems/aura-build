# Simplify Path

## Problem

Given an **absolute Unix-style file path** as a string, simplify it by resolving `.` and `..` segments and collapsing any redundant or trailing slashes.

Rules:
- `.` (current directory) has no effect and should be removed.
- `..` (parent directory) should remove the preceding valid directory segment, unless we are already at the root.
- Adjacent `/` are merged into one.
- The result **must** begin with a single `/`, and there are **no trailing slashes** (except that the root path itself is just `/`).

The path consists only of alphanumeric characters, dots `.`, and slashes `/`.

## Function Signature

```python
def solve(path: str) -> str:
    """
    Return the canonical, simplified version of the absolute Unix path.
    """
```

## Input

The input is provided via the special harness variables (stdin-less mode). A single test case is supplied as:

```
CASE0=/a/./b/../../c/
```

Each `CASEn=...` line provides one string value to be passed as the `path` argument.

## Output

Your `solve` function must return the canonical simplified path as a string.

## Examples

```
CASE0=/a/./b/../../c/        ->  /c
CASE1=/home//foo/            ->  /home/foo
CASE2=/../                   ->  /
CASE3=/a/b/c/d/./e/../f     ->  /a/b/c/d/f
```

## Notes

- Splitting by `/` and using a stack is the canonical approach.
- Remember: you cannot pop past the root — `/..` still resolves to `/`.
