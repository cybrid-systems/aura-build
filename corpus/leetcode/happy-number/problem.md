# Happy Number

## Problem

A number is called **happy** if repeatedly replacing it with the **sum of the squares of its digits** eventually reaches `1`. If it instead enters a cycle that does not include `1`, the number is **unhappy**.

Given a positive integer `n`, determine whether it is a happy number.

### Examples

| Input `n` | Happy? | Sequence (truncated) |
|-----------|--------|----------------------|
| 19        | Yes    | 19 → 82 → 68 → 100 → 1 |
| 2         | No     | 2 → 4 → 16 → 37 → 58 → 89 → 145 → 42 → 20 → 4 (cycle) |
| 1         | Yes    | 1 |

## Function Signature

```python
def solve(n: int) -> bool:
    """Return True if n is a happy number, False otherwise."""
```

## Input / Output (Harness Convention)

The harness reads `CASE0=...` lines from the problem and invokes `solve` directly (no stdin/stdout). Each case provides the integer to test.

Example cases provided to `solve`:

```
CASE0=19
CASE1=2
CASE2=7
CASE3=1
CASE4=111111111
```

## Notes

- Any non-happy sequence must eventually revisit a previously seen value; tracking seen sums in a set lets you detect the cycle.
- The maximum digit-square sum for a 32-bit integer is bounded, so the loop terminates quickly.
- Return `True` for `1` immediately (it is trivially happy).
