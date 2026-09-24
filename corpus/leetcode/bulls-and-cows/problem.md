# Bulls and Cows

## Problem

You are given two strings `secret` and `guess` representing a codebreaker's guess and the secret code in a Mastermind-style game. Both strings have the same length `N` (with `4 ≤ N ≤ 1000`) and consist only of digits (`'0'`-`'9'`). Your task is to compute the **bulls** and **cows**:

- A **bull** is a digit that appears at the same position in both `secret` and `guess`.
- A **cow** is a digit that appears in both strings but at a **different** position. Cows do not double-count digits that already matched as bulls, and each shared digit contributes at most one cow overall.

Return the two counts as a pair `(bulls, cows)`.

## Function Signature

```python
def solve(secret: str, guess: str) -> tuple[int, int]:
    ...
```

## Input

The harness feeds the function directly. For reference, the on-disk case file uses:

```
CASE0=secret="1807",guess="7810"
CASE0_EXPECTED=(bulls=1,cows=3)
CASE1=secret="1123",guess="0111"
CASE1_EXPECTED=(bulls=1,cows=1)
```

## Output

A tuple `(bulls, cows)` of two non-negative integers. The sum of bulls and cows is at most `N`.

## Notes

- Digits that already count as bulls must be excluded from cow counting (the classic Mastermind rule).
- `secret` and `guess` are guaranteed to have equal length and to contain only ASCII digits.
- A clean linear-time solution using a digit frequency array of size 10 is expected.
