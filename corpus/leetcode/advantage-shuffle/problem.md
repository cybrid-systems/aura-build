# Advantage Shuffle

## Problem

You are given two integer arrays `A` and `B` of equal length `n`. We say that element `a` has an **advantage** over element `b` if `a > b`.

You may reorder `A` arbitrarily, but `B` must remain fixed. After reordering, pair the elements of the new `A` with `B` by index: the element at position `i` in the rearranged `A` is compared against `B[i]`. The score is the number of positions `i` where `A[i] > B[i]`.

Return any rearrangement of `A` that maximizes this score.

## Function Signature

```python
def solve(A: list[int], B: list[int]) -> list[int]:
    ...
```

## Input / Output Convention

The harness is **stdin-less** and feeds each case as `CASE0=...` lines before invoking `solve`:

```
CASE0=A = [2, 7, 11, 15]
CASE0=B = [1, 10, 4, 11]
```

- `CASE0=` prefix denotes the **first** test case. Subsequent cases use `CASE1=`, `CASE2=`, …
- `A` and `B` are each lists of integers, written in standard Python literal form (`[a, b, c]`).
- Whitespace around the lists is optional.
- A single line beginning with `END` (after the last case) terminates input.
- For every case, print the rearranged `A` as a Python list literal on its own line.

## Notes

- `A` and `B` always have the same non-negative length; an empty pair of lists is allowed and should return `[]`.
- The function must return a permutation of the input list `A` (no other values).
- When multiple optimal rearrangements exist, any one of them is accepted.
- A clean greedy approach pairs the smallest `A` element that still beats `B[i]`, otherwise wastes the smallest `A` on the hardest `B[i]` to beat.
