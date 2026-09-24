# Intersection of Two Arrays

**Category:** Hashing

## Statement

Given two integer arrays, return the set of values that appear in both. Each value should be included at most once, and the order of the returned sequence does not matter.

## Function Signature

```python
def solve(a: list[int], b: list[int]) -> list[int]:
    ...
```

## Input Convention

The harness invokes `solve` directly with no I/O. When validating a solution against the examples, the case is encoded as lines of the form:

```
CASE0=a=[1,2,2,3] b=[2,3,4]
CASE0_OUT=[2,3]
```

Lines prefixed with `CASE0=` describe the arguments `a` and `b`. A line `CASEk_OUT=` describes the expected return value for `case k` as a list. Values may be negative and may repeat within either input.

## Notes

- Duplicates: if an element appears multiple times in either array, it still appears at most once in the output.
- The expected output is shown as a concrete list; since order is unspecified, any permutation that contains exactly the same values with the same multiplicity is accepted.
- Empty intersection should be returned as `[]`.
