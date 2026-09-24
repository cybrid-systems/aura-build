# Evaluate Reverse Polish Notation

## Problem

You are given an arithmetic expression written in **Reverse Polish Notation (RPN)** — also known as postfix notation. In RPN, operators are placed *after* their operands, and there are no parentheses. For example, the infix expression `(3 + 4) * 5` is written in RPN as `3 4 + 5 *`.

Each token is either:
- An integer operand (there may be negative numbers)
- One of the four binary operators: `+`, `-`, `*`, `/`

Your task is to evaluate the expression and return its single integer result.

Assume:
- The input is always a **valid** RPN expression.
- Intermediate values are always 32-bit integers.
- Division `/` is **integer division truncated toward zero** (e.g., `7 / 2 == 3`, `-7 / 2 == -3`).
- The result fits in a 32-bit signed integer.

## Function Signature

```
def solve(tokens: list[str]) -> int:
    ...
```

## Input / Output Convention

The harness reads a single line of whitespace-separated tokens from the test case file.

**Format:**
```
CASE0=3 4 + 5 *
```

- `CASE0=` prefix is stripped before the tokens are passed to `solve`.
- The remaining tokens are split on whitespace into a list of strings.
- `solve` must return the integer result of evaluating the RPN expression.

**Example:**
```
CASE0=15 7 1 1 + - / 3 * 2 1 1 + + -
```
Expected output: `0`

## Notes

- Use a **stack**: push numbers, and when you see an operator, pop the two top operands (right operand first), apply the operation, and push the result back.
- You can assume the expression always evaluates without error (no division by zero, always enough operands on the stack).
- The list will have length up to ~10,000 tokens.
