# Combination Sum II

## Problem

Given a list of integer `candidates` (which may contain duplicates) and an integer `target`, find **every unique combination** of numbers from `candidates` whose sum equals `target`.

Rules:
- Each number may be used **at most once** per combination.
- The relative order of numbers within a combination does not matter (combinations are sets), but you may sort the output for stability.
- The solution set must not contain duplicate combinations.

Return all unique combinations that sum to `target`. If none exist, return an empty result.

## Function Signature

```python
def solve(candidates: list[int], target: int) -> list[list[int]]:
    ...
```

## Input / Output Convention

The harness invokes `solve` directly (no stdin). Each test case is exposed as module-level constants:

```
CASE0_INPUT = {"candidates": [10, 1, 2, 7, 6, 1, 5], "target": 8}
CASE0_EXPECTED = [[1, 1, 6], [1, 2, 5], [1, 7], [2, 6]]
```

For case `i`, your `solve` must be called with `CASE{i}_INPUT["candidates"]` and `CASE{i}_INPUT["target"]`, and must return a value equal to `CASE{i}_EXPECTED` (comparing the set of combinations regardless of internal ordering).

## Notes

- The candidate list may contain repeated values (e.g., two `1`s). Ensure you skip over duplicates at the same recursion depth so you don't emit the same combination twice.
- Sorting `candidates` first is a common and effective approach to make duplicate-skipping straightforward and to guarantee a canonical order.
- Use backtracking: at each index, either skip the current value, or take it (if it doesn't exceed the remaining target) and recurse on the next index — because each element may be used only once.
- Combinations like `[1, 2, 5]` and `[2, 1, 5]` are the same; emit each only once.
