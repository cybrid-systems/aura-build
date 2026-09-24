# Car Fleet

There are `n` cars traveling towards a destination at mile `target`. Each car has a starting position and a speed. Cars cannot overtake each other; a faster car behind a slower one must slow down to match the slower car's speed, forming a **fleet**. A car that reaches the destination alone forms its own fleet. Cars are assumed to start simultaneously.

Given the starting positions, speeds, and target, determine how many car fleets arrive at the destination.

## Input Format

```
n
target
position[0] position[1] ... position[n-1]
speed[0] speed[1] ... speed[n-1]
```

## Output Format

A single integer: the number of car fleets that reach the destination.

## Function Signature Hint

```python
def solve(n: int, target: int, position: list[int], speed: list[int]) -> int:
    ...
```

## Notes

- `1 <= n <= 10^5`
- `position[i]` and `target` are in miles, with `position[i] < target`
- A car's time to reach the destination is `(target - position[i]) / speed[i]`
- A faster car behind a slower one catches up only if its arrival time is strictly less than the car ahead; equal arrival times still count as separate fleets arriving at the same moment.

## Example

**CASE0**
```
3
12
10 8 0
2 4 1
```

- Car 0 → time = (12-10)/2 = 1.0
- Car 1 → time = (12-8)/4 = 1.0
- Car 2 → time = (12-0)/1 = 12.0

Sorted by position descending (closest first): Car 0 (pos=10, t=1.0), Car 1 (pos=8, t=1.0), Car 2 (pos=0, t=12.0).
Car 1's time (1.0) is not strictly less than Car 0's time (1.0), so they form **2 fleets** with Car 2 alone making **3 total**.

**Output:** `3`
