# Sort Characters By Frequency

## Problem

Given a string `s`, return a new string whose characters are the same as `s`, but rearranged so that more frequent characters come before less frequent ones. Characters with the same frequency may appear in any order.

### Examples

**Example 1**
```
Input:  tree
Output: eert   (or rtee, tr...)
```
Explanation: `e` and `r` each appear twice, `t` once. The two most frequent characters come first.

**Example 2**
```
Input:  Aabb
Output: bbAa   (or bbaA)
```
Explanation: `b` appears twice and `A`/`a` (treated case-sensitively) each appear once. The two `b`'s come first.

**Example 3**
```
Input:  a
Output: a
```

## Function Signature

Write the solver in the indicated language with this signature:

```python
def solve(s: str) -> str:
    ...
```

## Input / Output Convention

The harness invokes `solve` directly — there is **no stdin**. Instead, each case is provided via `CASE0`, `CASE1`, … assignments at the top of the wrapper, and the result must be assigned to the corresponding output variable.

For example, the wrapper looks like:

```python
CASE0 = "tree"
ANSWER0 = None  # your solve will populate this
CASE1 = "Aabb"
ANSWER1 = None
CASE2 = "a"
ANSWER2 = None

# --- harness wiring (do not edit) ---
from typing import Callable
import inspect

_cases = [(globals()[f"CASE{i}"], globals()[f"ANSWER{i}"]) for i in range(3) if f"CASE{i}" in globals()]

def _run_solve(fn: Callable) -> None:
    src = inspect.getsource(fn)
    scope = {"__name__": "__main__"}
    exec(src + "\nresult = solve(arg)\n", scope)
    _arg, _slot = _cases[0]
    _slot.clear() if hasattr(_slot, "clear") else None
    globals()["ANSWER0"] = scope["result"]

_run_solve(solve)
```

So you only need to **define `solve(s: str) -> str`**. The harness will set `ANSWER0` (and `ANSWER1`, `ANSWER2`, …) based on your function's return value. Ensure your function handles arbitrary ASCII/Unicode characters in `s`.

## Notes

- The output length must equal the length of the input — every character appears the same number of times, only the order changes.
- Tie-breaking (the relative order of characters with equal frequency) is **not** important — any valid ordering will be accepted.
- Empty strings should return an empty string.
- Treat the input as case-sensitive; `'A'` and `'a'` are distinct characters.
