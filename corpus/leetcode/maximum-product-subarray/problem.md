# Maximum Product Subarray

## Problem

Given an integer array `nums` (length `n ≥ 1`), find the contiguous subarray whose elements have the **largest product**, and return that product.

A subarray is a non-empty contiguous sequence of elements.

**Notes:**

- The array may contain positive numbers, negative numbers, and zeros.
- A single element is a valid subarray.
- When the maximum product is large, return it as a standard 64-bit integer. Inputs are chosen so that the result fits in a signed 64-bit integer.
- This is a pure function problem: each case is independent and `solve` is called once per case.

## Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input / Output Convention

This problem uses the **Aura** I/O format. Each test case is provided on `stdin` as a single line and the result is written to `stdout`. There are no multiple cases.

Aura parses input using a fixed set of keys. The relevant line for this problem is:

```
CASE0=nums=<json array>
```

For example:

```
CASE0=nums=[2,3,-2,4]
```

The array is given as a JSON list of integers. The solver must parse `nums` from this line, call `solve(nums)`, and write the integer answer on its own line.

**Example**

```
CASE0=nums=[2,3,-2,4]
```

Output:

```
6
```

(because the subarray `[2, 3]` has product `6`, which is larger than any other contiguous subarray).
