# Regular Expression Matching

Implement regular expression matching that supports two special characters:

- `.` matches any single character.
- `*` matches **zero or more** of the *preceding* element. (It is **not** standalone — `*` is always preceded by a character, either a literal or `.`.)

The match must cover the **entire** input string (and the entire pattern), not a substring.

## Function signature

```lisp
(defun solve (s p)
  ;; returns T if s fully matches pattern p, NIL otherwise
  ...)
```

- `s` — the input string (may be empty).
- `p` — the pattern string (may be empty).

## Input convention

The harness is **stdin-less**. Each test case is provided as a top-level form read by the REPL, in the following order on consecutive lines:

```
CASE0=(solve "aa" "a")
CASE1=(solve "aa" "a*")
CASE2=(solve "ab" ".*")
CASE3=(solve "aab" "c*a*b")
CASE4=(solve "mississippi" "mis*is*p*.")
CASE5=(solve "" "")
CASE6=(solve "" "a*")
```

Each line is a single form evaluating to a boolean (`T` / `NIL`). The expected outputs are respectively:

```
T -> NIL
NIL -> T
T -> T
T -> T
NIL -> NIL
T -> T
T -> T
```

(Equivalently: `F T T T F T T` in truthy/falsy form.)

## Notes

- A `*` must have a valid preceding character; the pattern `p` is guaranteed well-formed (no leading `*`, no consecutive `*`).
- Recursion with memoization (top-down DP) or a 2D table (bottom-up DP) over `(i, j)` = position in `s` and `p` is the canonical approach.
- Watch the base case: if the pattern runs out (`j == len(p)`), the string must also be exhausted. If the string runs out but the pattern remains, only patterns ending in `x*` (with optional repetition) can still match the empty string.
