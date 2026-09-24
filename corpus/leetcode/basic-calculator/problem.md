# Basic Calculator

## Problem

Implement a basic calculator to evaluate a simple arithmetic expression.

The expression string contains only non-negative integers and the operators `+`, `-`, along with parentheses `(`, `)`, and spaces ` `.

Calculate the final result of the expression and return it.

> Note: You may assume all operands are non-negative integers and the expression is always valid.

## Function Signature

```python
def solve(s: str) -> int:
    ...
```

## Input

A single line containing the expression string `s`.

```
s = "1 + 1"
```

## Output

Print the integer result of evaluating the expression.

```
2
```

## Examples

### Example 1
**Input:**
```
1 + 1
```
**Output:**
```
2
```

### Example 2
**Input:**
```
(1+(4+5+2)-3)+(6+8)
```
**Output:**
```
23
```

### Example 3
**Input:**
```
 2-1 + 2
```
**Output:**
```
3
```

## Notes

- Use a **stack** to track the current sign and the running total when encountering parentheses.
- When a `(` is encountered, push the current sign and accumulated value onto the stack so the parenthesized subexpression can be evaluated with the correct polarity.
- When a `)` is encountered, pop the saved value and sign, then apply them to the subexpression result before continuing.
