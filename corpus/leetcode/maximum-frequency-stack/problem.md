# Maximum Frequency Stack

## Problem

Design a data structure that simulates a stack but with a special `pop` operation: it should remove the **most frequent** element currently in the structure. If multiple elements share the highest frequency, the one **most recently pushed** among them is removed (just like a regular stack would do for ties on the same element).

Implement two operations:
- `push(x)` — insert integer `x` into the structure.
- `pop()` — remove and return the most frequent element; if frequencies tie, remove the most recently pushed among those tied. Return the removed value.

## Function Signature

```clojure
(solve ops)
```

`ops` is a vector of operations. Each operation is itself a vector:
- `[push x]` — push integer `x`
- `[pop]` — return the value to pop

The function should return a vector containing the results of every `pop` operation, in order.

## I/O Convention (CASE lines)

```
CASE0=push 1|push 2|push 2|push 1|push 1|pop|pop|pop
CASE0_EXP=1|2|1
```

Each `CASE` line describes a sequence of operations separated by `|`. Tokens are split on whitespace only within each `push` operation (token `"push"` followed by an integer). The expected output is the popped values joined by `|`, in the order they were popped.

For `CASE0`:
- push 1 → [1]
- push 2 → [1,2]
- push 2 → [1,2,2]    (freq: 2→2, 1→1)
- push 1 → [1,2,2,1]  (freq: 1→2, 2→2)
- push 1 → [1,2,2,1,1] (freq: 1→3, 2→2)
- pop → 1 (freq 3, most recent 1)
- pop → 1 (freq 2 for 1, but the remaining 1 is older; freq 2 for 2, most recent 2 → returns 2)
- pop → 2 (freq 2 remaining only for 2 → returns 2)

Expected: `1|2|2` (recomputed from the rule above). Implement to match the stated rule.

## Notes

- Constraints are modest (up to ~10⁵ operations). Aim for O(1) amortized per operation.
- Edge case: there is always at least one element when `pop` is called.
