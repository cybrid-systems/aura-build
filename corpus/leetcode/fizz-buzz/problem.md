# Fizz Buzz

## Statement

Write a program that prints the numbers from `1` to `n` (inclusive), one per line, with the following substitutions:

- If the number is a multiple of `3`, print `Fizz` instead of the number.
- If the number is a multiple of `5`, print `Buzz` instead of the number.
- If the number is a multiple of both `3` and `5`, print `FizzBuzz` instead of the number.
- Otherwise, print the number itself.

## Function Signature

```
def solve(n: int) -> list[str]:
```

The function should return a list of `n` strings (in order from `1` to `n`) suitable for joining with newlines.

## Input / Output Convention (Aura harness)

The harness reads a single line `n` from stdin and prints the result.

```
CASE0=15
CASE0_OUT=
1
2
Fizz
4
Buzz
Fizz
7
8
Fizz
Buzz
11
Fizz
13
14
FizzBuzz
```

## Notes

- `n` is a positive integer; assume `1 ≤ n ≤ 10^5` (or whatever fits in your language’s memory easily).
- Output exactly `n` lines; no trailing spaces, no extra blank line at the end beyond what the harness emits.
- The combined rule (`FizzBuzz`) must take precedence over the individual rules.
