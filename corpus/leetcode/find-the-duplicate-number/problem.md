# Find the Duplicate Number

Given an array of integers `nums` containing `n + 1` integers where each integer is in the range `[1, n]` inclusive, prove that at least one duplicate number must exist. By the pigeonhole principle, there will always be at least one repeated number.

Assume there is **only one duplicate number**, but it could be repeated more than once.

Find and return the duplicate number **without modifying the array** and using **only constant extra space**.

## Function Signature

```python
def solve(nums: list[int]) -> int:
    ...
```

## Input

The input is provided as a single test case via standard input using the following `CASE0`-style format:

```
CASE0
<count of numbers>
<n_0> <n_1> <n_2> ... <n_count-1>
```

- Line 1: the literal token `CASE0`.
- Line 2: an integer `n+1` giving the length of the array.
- Line 3: `n+1` space-separated integers in the range `[1, n]` with no other digits.

## Output

Print a single line containing the duplicated number.

## Examples

### Example 1
Input:
```
CASE0
5
1 3 4 2 2
```
Output:
```
2
```

### Example 2
Input:
```
CASE0
8
3 1 3 4 2 5 6 7
```
Output:
```
3
```

## Notes

- The array cannot be modified; you must operate as if it were read-only.
- You may use any constant-space method, including Floyd's Tortoise and Hare (cycle detection) by treating values as `next` pointers into indices.
- The duplicate is guaranteed to exist and exactly one value is repeated (possibly multiple times).
