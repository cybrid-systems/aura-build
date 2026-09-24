# Minimum Cost to Connect Sticks

## Problem

You have a collection of `n` sticks with positive integer lengths. You may repeatedly perform the following operation until only one stick remains:

- Choose any two sticks of lengths `a` and `b` (where `a ≤ b`).
- Connect them into a single stick of length `a + b`, paying a cost of `a + b`.

Your goal is to minimize the total cost paid across all operations.

Given the lengths of the sticks, compute the minimum possible total cost to reduce the collection to a single stick.

## Function Signature

```python
def solve(sticks: list[int]) -> int:
    ...
```

## Input

The input consists of a single case formatted as `CASE0=...` lines:

- `CASE0=<lengths>`: a comma-separated list of stick lengths, e.g. `CASE0=2,4,1,3`.

## Output

A single line containing the minimum total cost to connect all sticks into one.

## Examples

### Example 1

```
CASE0=2,4,1,3
```

Output:

```
19
```

Explanation: A possible optimal sequence is connect `1,3` (cost `4`, sticks: `[2,4,4]`), then connect `4,4` (cost `8`, sticks: `[2,8]`), then connect `2,8` (cost `10`, sticks: `[10]`). Total cost: `4 + 8 + 10 = 22`. Wait — recompute: connecting `1+3=4` cost `4`, then `2+4=6` cost `6` (sticks `[6,4]`), then `4+6=10` cost `10`. Total = `4 + 6 + 10 = 20`. The true optimum `19` is achieved by e.g. `1+2=3` (cost `3`), `3+3=6` (cost `6`), `4+6=10` (cost `10`) → total `19`.

### Example 2

```
CASE0=1,8,3,5
```

Output:

```
30
```

## Notes

- `n ≥ 1`. When `n = 1`, the cost is `0` (no operations needed).
- A greedy strategy — always combining the two shortest available sticks — yields the optimal answer; this mirrors the analysis of Huffman-style constructions.
- Use a min-heap (priority queue) for an efficient implementation.
