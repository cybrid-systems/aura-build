# Number of Recent Calls

## Problem

You are given a stream of timestamped ping requests (in strictly increasing order of time). Implement a data structure that supports a single operation: given the current timestamp `t`, count how many requests have occurred in the time window `[t - 3000, t]` (inclusive of both ends).

## Function Signature

```lisp
(defun solve (n op-seq)
  ;; n      : number of operations
  ;; op-seq : list of timestamps t (1-based order)
  ;; Return: list of counts, one per operation
  )
```

## Input

The input is given via the `CASE0` line as a single S-expression. For example:

```lisp
CASE0=(4 ((1) (100) (3001) (3002)))
```

This means there are `n = 4` operations with timestamps `[1, 100, 3001, 3002]`, in that order.

## Output

Print one line containing the `n` counts, in order, space-separated.

For the example above, the expected output is:

```
1 2 3 3
```

Explanation:
- At `t = 1`, the window `[−2999, 1]` contains only `1` → count `1`.
- At `t = 100`, the window `[−2900, 100]` contains `1, 100` → count `2`.
- At `t = 3001`, the window `[1, 3001]` contains `1, 100, 3001` → count `3`.
- At `t = 3002`, the window `[2, 3002]` contains `100, 3001, 3002` → count `3`.

## Notes

- Timestamps are strictly increasing across operations.
- Each timestamp fits in a 32-bit signed integer.
- A queue (FIFO) is the natural data structure: enqueue each new `t`, then dequeue from the front while the front is `< t - 3000`.
- The answer for each operation equals the current queue size after the cleanup step.
