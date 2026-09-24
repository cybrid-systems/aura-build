# Open the Lock

## Problem

You are given a standard combination lock with 4 rotating dials. Each dial shows a single digit from `0` to `9`. In one turn you may pick any one dial and rotate it by **+1** or **-1** (wrapping `9 → 0` and `0 → 9`). A dial can also be rotated **freely** to any digit in one turn (this special turn does **not** rotate any other dial).

You start from the configuration `0000`. Some configurations are **forbidden** (dead ends — you cannot pass through or stop on them). You are also given a **target** configuration. Find the minimum number of turns required to reach the target from `0000`, while never visiting a forbidden configuration. If it is impossible, output `-1`.

The freely-setting turn counts as **1 turn**, the same as a ±1 step on a single dial.

## Input

- Line 1: two integers `N T` — number of forbidden configurations and the target configuration given as a 4-digit string (e.g. `0123`).
- Next `N` lines: each is a 4-digit string representing a forbidden configuration.

`0 ≤ N ≤ 10000`. The target is never in the forbidden list, and is never `0000`.

## Output

A single integer: the minimum number of turns to open the lock, or `-1` if impossible.

## Function signature

```python
def solve(N: int, target: str, deadends: list[str]) -> int:
    ...
```

## I/O convention (Aura harness)

The harness will invoke `solve(N, target, deadends)` directly. Example wrapper test:

```
CASE0=5
CASE0_N=5
CASE0_target=0202
CASE0_deadends=["0201","0101","0102","1212","2002"]
CASE0_expected=6
```

## Notes

- Use **BFS** over the 10,000 possible states (`0000` … `9999`). Each state has at most `8` neighbors (4 dials × 2 directions) **plus** the 9 special “free-set” neighbors (set one dial to any other digit). This branching is still manageable.
- Mark `0000` and all forbidden states as visited before starting.
- If the target is unreachable, return `-1`.
