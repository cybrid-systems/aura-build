# Two City Scheduling

## Problem

A company is planning to send `2n` people on a trip: exactly `n` people must go to City **A** and exactly `n` people must go to City **B**. For each person `i`, two costs are given:

- `cost[i][0]` — the cost of sending person `i` to City A.
- `cost[i][1]` — the cost of sending person `i` to City B.

Assign each person to exactly one of the two cities so that each city receives exactly `n` people, and the **sum of all costs is minimized**. Return that minimum total cost.

## Input

The input is provided via standard input using the following harness convention. Lines prefixed `CASE0=` are metadata and should be ignored for solving; the first non-`CASE0=` line contains `n`, followed by `2 * n` lines, each containing two integers `a b` (the costs of sending a person to City A and City B).

```
CASE0=...
n
a1 b1
a2 b2
...
a_{2n} b_{2n}
```

## Output

Print a single integer: the minimum total cost of sending `2n` people to the two cities with exactly `n` in each.

## Function Signature

```
long long solve(int n, vector<vector<int>>& cost);
```

`n` is the number of people who must go to each city (so the total number of people is `2*n`). `cost[i][0]` is the cost to send person `i` to city A and `cost[i][1]` is the cost to send person `i` to city B. Return the minimum total cost.

## Examples

### Example 1
```
2
10 20
30 200
400 50
30 20
```
Output:
```
110
```

The optimal split (2 to A, 2 to B) gives `10 + 30 + 50 + 20 = 110`.

## Constraints

- `1 <= n <= 50`
- `0 <= cost[i][j] <= 1000`

## Notes

- A greedy approach works: send the `n` people with the smallest `(cost to B) - (cost to A)` to city A, and the remaining to city B. Equivalently, sort by the "savings" of choosing A over B and pick the `n` most advantageous assignments for city A.
- Use 64-bit integer arithmetic when summing costs, since `cost[i][j] <= 1000` and up to `100` people yields totals up to `10^5` (still fits, but 64-bit is safe practice).
