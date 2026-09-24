# Target Sum

You are given an integer array `nums` and an integer `target`.

For each element in `nums`, you must assign it either a `+` or a `-` sign. Build an expression by placing the chosen sign in front of each element (in order), then sum the signed values.

Count the number of ways to assign signs so that the resulting sum equals `target`.

Return that count.

## Function to implement

```python
def solve(nums: list[int], target: int) -> int:
    ...
```

## Input / Output (harness convention)

The harness invokes `solve(nums, target)` directly — no stdin/stdout.

A self-check example you can use locally:

```
CASE0=
nums = [1, 1, 1, 1, 1]
target = 3
expected = 5
```

The 5 valid sign assignments for `nums = [1,1,1,1,1]` with sum `3`:
`+1+1+1+1-1`, `+1+1+1-1+1`, `+1+1-1+1+1`, `+1-1+1+1+1`, `-1+1+1+1+1`.

## Notes

- `nums` length is at most 20, and each `|nums[i]|` is at most 1000. Brute force over `2^n` assignments works in principle, but a dynamic-programming solution is expected.
- A standard reduction: letting `P` be the sum of the positively-signed elements and `N` the sum of the negatively-signed elements (where their absolute values form the rest of `nums`), we have `P - N = target` and `P + N = total`, so `P = (total + target) / 2`. The problem then becomes counting subset-sums that equal `P` (when `(total + target)` is non-negative and even).
- Return the count as a plain integer; the value can be large, but the constraints keep it within standard integer range.
