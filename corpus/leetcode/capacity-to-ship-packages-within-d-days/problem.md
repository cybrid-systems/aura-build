# Capacity to Ship Packages Within D Days

## Problem

A conveyor belt has a sequence of packages that must be shipped from one port to another within `D` days. The `i`-th package has a weight given in a 0-indexed array `weights`. Each day, we load packages onto a ship in the given order. Packages on the same day are placed contiguously on the conveyor belt. The ship's weight capacity is fixed for all days.

Given the package weights and the number of days `D`, determine the **minimum ship capacity** so that all packages can be shipped within `D` days.

## Function Signature

```python
def solve(weights: list[int], D: int) -> int:
    ...
```

## Input / Output Convention

Input is provided via the `CASE0` lines after the function header. Each case has three lines:

- `CASE0 = <weights list as JSON, e.g. [1,2,3,4,5,6,7,8,9,10]>`
- `CASE1 = <D, e.g. 5>`
- `CASE2 = <expected minimum ship capacity, e.g. 15>`

The harness parses the first three `CASE*` lines as the arguments to `solve` and checks the return value against the expected answer.

### Example

```
CASE0 = [1,2,3,4,5,6,7,8,9,10]
CASE1 = 5
CASE2 = 15
```

Expected return: `15` — a ship of capacity 15 can carry `(1,2,3,4,5)`, `(6,7)`, `(8)`, `(9)`, `(10)` across 5 days.

## Notes

- `weights` length is up to ~5·10⁴; package weights are positive integers.
- `D` is between 1 and `len(weights)` inclusive.
- The minimum capacity is at least `max(weights)` and at most `sum(weights)`.
- Hint — binary search the answer and use a greedy check: simulate loading days left-to-right, accumulating weights until the next package would exceed the candidate capacity.
