# Min Stack

**Category:** stack / queue  
**Slug:** `min-stack`

## Problem

Design a stack data structure that supports the following operations, all in **O(1)** time:

- `push(x)` — push element `x` onto the stack.
- `pop()` — remove the top element from the stack.
- `top()` — return the top element without removing it.
- `get_min()` — return the minimum element currently in the stack (without removing it).

You will be given a sequence of operations to perform on the stack. After each `get_min` operation, output the current minimum.

### Input

Operations appear one per line, in order. Each line is one of:

- `1 x`   — push the integer `x`
- `2`     — pop the top element (the stack is guaranteed to be non-empty)
- `3`     — get_min: output the current minimum (the stack is guaranteed to be non-empty)
- `4`     — top: ignored (not required for the answer)

For this puzzle the operation sequence is fixed and provided directly to your function — no parsing is required.

### Output

For each `get_min` (operation `3`) in the sequence, print the minimum value on the stack at that moment, in order.

The input is guaranteed to be valid: `pop`, `get_min`, and `top` are never called on an empty stack.

### Function signature

```clojure
(solve ops)
;; ops: vector of [op-type & payload] tuples describing the operations in order
;; returns: vector of answers (one per get_min call)
```

### Example

Sequence of operations:

```
1 5     ; push 5
1 2     ; push 2
1 8     ; push 8
3       ; get_min  -> 2
2       ; pop       (removes 8)
2       ; pop       (removes 2)
1 3     ; push 3
3       ; get_min  -> 3
2       ; pop
2       ; pop
```

Output:

```
2
3
```

### Notes

- Aim for **O(1)** amortized per operation. A common trick is to keep a parallel "running minimums" stack (or store pairs on the main stack) so that `get_min` never has to scan.
- Integer values fit in a standard signed 32-bit range.
- Assume operations are well-formed; no empty-stack error handling is required.
