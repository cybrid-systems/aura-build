# Total Hamming Distance

## Problem

Given an integer array `nums`, compute the **sum of Hamming distances** between all pairs of indices `(i, j)` where `0 ≤ i < j < n`.

The Hamming distance between two integers is the number of bit positions in which their binary representations differ.

### Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input

The harness feeds the function a single argument `nums`:

- `nums`: a list of non-negative integers.

## Output

Return a single integer: the total Hamming distance across all `n*(n-1)/2` pairs.

## Convention (Aura CASE0)

The first example line declares the argument and the expected result:

```
CASE0 = [4, 14, 2]
EXPECTED0 = 6
```

Subsequent examples follow the same `CASEk = ...` / `EXPECTEDk = ...` pattern.

## Notes

- A classic trick is to count, for each bit position independently, how many numbers have that bit set. If `c` numbers have the bit set among `n` numbers, that bit contributes `c * (n - c)` to the total Hamming distance (since every set-vs-unset pair differs at that bit).
- The answer can exceed 32-bit range; use 64-bit (Python `int` is unbounded, so this is automatic).
- An `O(n * B)` solution (`B` = number of bit positions, up to 32 for typical inputs) is expected; the naive `O(n²)` pairwise comparison will time out on large inputs.
