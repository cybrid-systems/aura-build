# IPO

## Problem Statement

You are planning to launch projects to grow your capital. You start with an initial amount of capital `w`. There are `n` projects available, each with two attributes:

- `capital[i]`: the minimum capital required to start the project
- `profits[i]`: the profit earned after completing the project

You may select **at most `k` projects** in total. When you start a project, your capital decreases by its requirement and then increases by its profit once the project is done (i.e., the net change is `profits[i]`). At any point, you can only start a project whose requirement `capital[i]` is less than or equal to your current capital.

Choose at most `k` projects to maximize your final capital.

## Function Signature

```python
def solve(w: int, k: int, capital: list[int], profits: list[int]) -> int:
    ...
```

## Input Convention (CASE0 format)

The harness reads the entire case description from a single `CASE0` block. Each parameter appears on its own line as `key=value`. Example:

```
CASE0
w=1
k=2
capital=[0,1,1]
profits=[1,2,3]
```

- `w` — initial capital (int)
- `k` — maximum number of projects you may select (int)
- `capital` — list of minimum capital requirements (list[int], same length as `profits`)
- `profits` — list of profits per project (list[int], same length as `capital`)

Your `solve` function must return the maximum capital achievable after selecting at most `k` projects.

## Notes

- `n` is implied by `len(capital)`. Assume `len(capital) == len(profits)`.
- The selection order matters because capital changes after each completed project, unlocking new projects.
- A greedy strategy picking the currently available project with the highest profit per step is optimal for this setting.
