# Gray Code

## Problem

An **n-bit Gray code** is a sequence of `2^n` distinct integers in the range `[0, 2^n)` such that any two consecutive integers (including the last and the first) differ in exactly one bit in their binary representation.

Given an integer `n`, return **any** valid n-bit Gray code sequence.

## Function Signature

```python
def solve(n: int) -> list[int]:
    ...
```

## Input

A single integer `n` (`1 ≤ n ≤ 16`) provided via a `CASE0=` line:

```
CASE0=2
```

## Output

Print one valid Gray code sequence on a single line as space-separated integers. The sequence must contain exactly `2^n` values, all within `[0, 2^n)`, with each consecutive pair (and the wrap-around pair) differing in exactly one bit.

For the example above, a valid output is:

```
0 1 3 2
```

(equivalently, `00 → 01 → 11 → 10`, each step flips a single bit).

## Notes

- There are many valid Gray codes for a given `n`; any one of them is accepted.
- A simple construction: take the `(n-1)`-bit Gray code `G`, then output `G` followed by `reverse(G)` with each element XORed with `2^(n-1)`.
