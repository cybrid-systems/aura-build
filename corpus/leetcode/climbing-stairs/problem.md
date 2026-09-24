# Climbing Stairs

## Problem

You are climbing a staircase of `n` steps. At each move you may take either **1 step** or **2 steps**. Count the number of distinct sequences of moves that reach exactly the top of the staircase.

Two sequences are considered different if they differ in the position at which a 2-step was taken (e.g., for `n = 3`, the sequences `1+1+1` and `1+2` and `2+1` are three different ways).

## Input

A single integer `n` (`1 ≤ n ≤ 45`).

## Output

Print the number of distinct ways to reach the top.

## Examples

### Example 0
**Input**
```
3
```
**Output**
```
3
```

### Example 1
**Input**
```
1
```
**Output**
```
1
```

### Example 2
**Input**
```
4
```
**Output**
```
5
```

## Function Signature (C++)

```cpp
long long solve(int n);
```

## Notes

- The answer fits within a 64-bit signed integer for the given constraints.
- This is the classical Fibonacci recurrence: `ways[n] = ways[n-1] + ways[n-2]` with base cases `ways[0] = 1`, `ways[1] = 1`.
- I/O follows the `CASE0=...` convention used by the harness; each test case provides one line containing `n`, and the solution must print one line with the answer.
