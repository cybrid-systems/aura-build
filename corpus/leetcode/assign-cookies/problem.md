# Assign Cookies

## Problem

You are given two integer arrays:

- `greed[]` — the greed factor of each child. A child is content if they receive a cookie whose size is **at least** their greed factor.
- `size[]` — the size of each cookie.

Each cookie can be assigned to **at most one** child, and each child can receive **at most one** cookie. Find the maximum number of children that can be made content.

## Function Signature

```python
def solve(greed: list[int], size: list[int]) -> int:
    ...
```

## Input / Output (Aura harness, no stdin)

The harness calls `solve(greed, size)` directly. For local testing, equivalent I/O lines look like:

```
CASE0=greed=[1,2,3], size=[1,1]
CASE0=1
CASE1=greed=[1,2], size=[1,2,3]
CASE1=2
```

Each `CASEn=` line is followed by an answer line containing the expected return value of `solve`.

## Notes

- `1 <= len(greed), len(size) <= 3 * 10^4`
- `0 <= greed[i], size[i] <= 10^9`
- A greedy strategy that sorts both arrays and pairs the smallest feasible cookie to each child suffices; the optimal answer equals the size of the largest matchable pairing.
- Return the maximum number of content children.
