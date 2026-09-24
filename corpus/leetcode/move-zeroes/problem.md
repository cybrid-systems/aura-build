# Move Zeroes

## Problem

Given an array of integers, rearrange it **in-place** so that all `0`s are moved to the end of the array, while preserving the relative order of the non-zero elements.

- You must operate on the array directly (do not allocate another array).
- The relative order of the non-zero values must stay the same as in the input.
- All zeros (if any) end up grouped at the tail of the array.
- The array length and the multiset of values are unchanged.

## Function Signature

```python
def solve(nums: list[int]) -> None:
    """Rearrange nums in-place: zeros to the end, non-zero order preserved."""
```

The function returns `None`; the input list `nums` is mutated as the output.

## Input / Output Convention

This puzzle is run via the **Aura** harness (no `stdin`). The harness feeds each case through `CASE0=...`, `CASE1=...`, ... lines and calls `solve(nums)` directly.

Each `CASES` value is a single test case encoded as a JSON array of integers, e.g.:

```
CASE0=[0,1,0,3,12]
CASE1=[1,2,3,4]
CASE2=[0,0,0,1]
CASE3=[]
CASE4=[1,0,0,0,2,0,3,0,4]
```

- `nums` is guaranteed to be a list of plain Python integers (each element is `>= 0`; the value `0` is what defines a "zero" — there are no negative numbers in this puzzle).
- The list may be empty; an empty list is already a valid result.
- The list may consist entirely of zeros, entirely of non-zeros, or any mixture.

The function must mutate `nums` such that, after the call, every element at index `i < len(nums) - z` (where `z` is the number of zeros) is non-zero, and every element at index `i >= len(nums) - z` is `0`.

## Examples

| Input              | After `solve` (mutated)  |
|--------------------|--------------------------|
| `[0, 1, 0, 3, 12]` | `[1, 3, 12, 0, 0]`       |
| `[1, 2, 3, 4]`     | `[1, 2, 3, 4]`           |
| `[0, 0, 0, 1]`     | `[1, 0, 0, 0]`           |
| `[]`               | `[]`                     |
| `[1, 0, 0, 0, 2, 0, 3, 0, 4]` | `[1, 2, 3, 4, 0, 0, 0, 0, 0]` |

## Notes

- Aim for an **O(n)** time, **O(1)** extra-space solution — a single left-to-right scan that overwrites zeros with subsequent non-zeros is enough.
- Be careful when the list contains many consecutive zeros: a naive approach that shifts elements one-by-one can degrade to O(n²). Prefer a write-pointer / two-pointer pattern.
- Equality with the expected output is checked element-by-element; order of non-zeros must match exactly.
