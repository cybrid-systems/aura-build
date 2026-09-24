# Intersection of Two Arrays II

## Problem Statement

Given two integer arrays `nums1` and `nums2`, return an array containing the **intersection** of the two arrays. Each element in the result must appear as many times as it shows in both arrays (i.e., the multiplicity of each value is the minimum of its count in `nums1` and its count in `nums2`). The order of the returned values does not matter.

You may implement any approach that runs within the required time and space constraints.

## Function Signature

```
def solve(nums1: list[int], nums2: list[int]) -> list[int]:
    ...
```

## Input / Output Convention

The harness feeds the solver through a CASE-style block on standard input (no command-line arguments). Each case is described by a small set of `CASE0=...` lines that you may parse however you like.

Example:

```
CASE0_NUMS1=1 2 2 1
CASE0_NUMS2=2 2
CASE0_EXPECTED=2 2
```

- `CASE0_NUMS1` — space-separated integers for the first array.
- `CASE0_NUMS2` — space-separated integers for the second array.
- `CASE0_EXPECTED` — space-separated integers representing one valid intersection (any permutation is accepted).

The solver should consume every `CASE<n>_*` block it sees and emit one result line per case in the form:

```
RESULT=<space-separated answer>
```

## Notes

- Counts matter: if `nums1` contains `2` twice and `nums2` contains `2` three times, the answer should contain `2` exactly twice.
- The output order is not enforced; any permutation of the correct multiset is accepted.
- An efficient solution typically uses a hash map to count elements in the smaller array and then iterates through the other, decrementing counts as matches are produced.
