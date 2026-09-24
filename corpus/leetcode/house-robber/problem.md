# House Robber

## Problem

You are a robber planning to steal from a row of houses on a street. Each house has a non-negative integer amount of money stashed inside. The only constraint that prevents you from robbing every house is that **two adjacent houses have security systems connected, and the police will be alerted if you rob two adjacent houses on the same night**.

Given an integer array `nums` where `nums[i]` represents the amount of money in the `i`-th house, determine the **maximum amount of money** you can rob in one night without robbing any two adjacent houses.

## Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input / Output Convention

The harness exchanges a single line of text with your `solve` function:

```
CASE0=nums=[2,7,9,3,1]
```

- `CASE0=` is the fixed prefix.
- `nums=` is followed by a JSON-style list of integers (the array of house values).
- The array length is between `0` and `10^5`, and each value is in `[0, 10^4]`.

Your `solve` must return a single integer: the maximum loot.

### Examples

```
CASE0=nums=[1,2,3,1]
→ 4
```

Explanation: Rob house `0` (money = 1) and house `2` (money = 3) → total `4`.

```
CASE0=nums=[2,7,9,3,1]
→ 12
```

Explanation: Rob house `0` (2), house `2` (9), and house `4` (1) → total `12`.

```
CASE0=nums=[]
→ 0
```

## Notes

- The answer is the maximum of two values at every step: either skip the current house or take it and add the best result from two houses back. A simple rolling state of size `O(1)` is enough.
- Empty input should return `0`.
