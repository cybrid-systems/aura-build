# Guess Number Higher or Lower

## Problem

We are playing the Guess Game. The rules are as follows:

I pick a number from `1` to `n`. You have to guess which number I picked.

Every time you guess a number `x`, I will return one of three possible results:

- `-1` — my number is **lower** (i.e., `pick < x`)
- `1`  — my number is **higher** (i.e., `pick > x`)
- `0`  — your guess is **correct** (i.e., `pick == x`)

Your task is to return the number I picked, using at most `O(log n)` calls to the guess API.

## Function Signature

```python
def solve(n: int) -> int:
    ...
```

Internally, `solve` may call a helper `guess(num: int) -> int` that returns `-1`, `0`, or `1` as described above.

## Input / Output Convention (CASE0)

The harness sets up `CASE0` style inputs as plain lines on stdin, but for this problem the value of `n` and the hidden `pick` are configured by the test harness and the `guess` API is provided implicitly. Your function must:

- Read no stdin.
- Return the integer `pick` chosen by the harness in `1..n`.

A typical CASE0 descriptor looks like:

```
CASE0=n=10 pick=6
```

but for this problem the grader injects `pick` and exposes it only through the `guess` API.

## Notes

- `n >= 1`. The hidden number is guaranteed to exist in `[1, n]`.
- Aim for `O(log n)` guesses; a linear scan will be too slow for large `n` (e.g., `n` up to `2^31 - 1`).
