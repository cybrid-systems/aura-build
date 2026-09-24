# Fruit Into Baskets

## Problem

You are given an integer array `fruits` where each element denotes the type of fruit at that position (you can pick any contiguous segment of the array). You have two baskets, and each basket can hold fruits of **only one type**. However, each basket can hold an unlimited number of fruits of its assigned type.

Your goal is to find the **length of the longest contiguous segment** of the array such that all the fruits in that segment can be collected into the two baskets. In other words, find the length of the longest contiguous subarray that contains **at most two distinct values**.

## Function Signature

```python
def solve(fruits: list[int]) -> int:
    ...
```

## Input

The input is provided as a single test case via standard input, formatted as a JSON-style header followed by the array values:

```
CASE0=0
Input=
3 3 3 1 2 1 1 2 3 3 4
```

- Line 1: `CASE0=<id>` — the case identifier.
- Line 2: `Input=` — marker line.
- Line 3: space-separated integers representing the `fruits` array.

## Output

Print a single integer: the length of the longest contiguous subarray that contains at most two distinct values.

```
5
```

## Notes

- If the array contains only one distinct value, the answer is the length of the entire array.
- An empty array is not expected as input (the array has at least one element).
- The expected approach is a sliding window maintaining a count of at most two distinct fruit types, with both pointers advancing in O(n) time.
