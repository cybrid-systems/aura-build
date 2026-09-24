# Implement Queue using Stacks

## Problem

Implement a first-in-first-out (FIFO) queue using only two stacks. The implemented queue must support all the operations of a normal queue:

- `enqueue(x)` — Pushes element `x` to the back of the queue.
- `dequeue()` — Removes the element from the front of the queue and returns it.
- `peek()` — Returns the front element of the queue without removing it.
- `empty()` — Returns `true` if the queue is empty, otherwise `false`.

You may only use standard stack operations: `push`, `pop`, `peek` (or `top`), and `size`. The amortized time complexity of each operation must be **O(1)**.

## Input / Output Convention (Harness Format)

The harness drives your solution through a single entry point. Implement the queue as state retained across calls.

### Lines

Each line is one command. Lines are one of:

```
ENQUEUE <int>
DEQUEUE
PEEK
EMPTY
```

- `ENQUEUE k` — call `enqueue(k)`.
- `DEQUEUE` — call `dequeue()`; on its own line the harness prints the returned integer.
- `PEEK` — call `peek()`; harness prints the returned integer.
- `EMPTY` — call `empty()`; harness prints `TRUE` or `FALSE`.

For invalid operations (e.g., `DEQUEUE` or `PEEK` on an empty queue) print `ERROR`.

## Function Signature

```
solve():
    read commands from stdin in the harness format
    maintain two stacks as the queue backing storage
    print results for DEQUEUE / PEEK / EMPTY as described
```

## Notes

- Operations must run in **amortized O(1)** — lazily transfer elements between the two stacks only when the output stack is empty.
- Use `CASE0=...` style I/O if your harness requires it (commands followed by results, one per line).
- Do not use any external data structures beyond two stacks; no deque, no list-as-queue.
