# Design Circular Queue

## Problem Statement

Implement a **circular queue** (ring buffer) of fixed capacity using an integer array. The queue must support the following operations in O(1) time:

- `enqueue(value)` — insert an element at the rear. Returns `true` if successful, `false` if the queue is full.
- `dequeue()` — remove the element at the front. Returns `true` if successful, `false` if the queue is empty.
- `front()` — return the front element without removing it. Returns `-1` if the queue is empty.
- `rear()` — return the last (rear) element without removing it. Returns `-1` if the queue is empty.
- `is_empty()` — return `true` if the queue has no elements.
- `is_full()` — return `true` if the queue has reached its capacity.

The queue uses a fixed-size array and two pointers (`head`, `tail`) that wrap around using modular arithmetic, so previously freed slots are reused.

## Function Signature

```clojure
(defn solve [commands]
  ;; commands is a vector of operation specs
  ;; returns a vector of results in order
  )
```

## Input / Output Convention

Input arrives as a single test case on `stdin`:

```
CASE0=5
[["enqueue",1],["enqueue",2],["enqueue",3],["enqueue",4],["enqueue",5],
 ["is_full"],["dequeue"],["enqueue",6],["front"],["rear"],
 ["dequeue"],["dequeue"],["dequeue"],["dequeue"],["dequeue"],
 ["is_empty"],["front"],["rear"]]
```

- The first line gives the queue capacity `k`.
- The second line is a JSON array of operations. Each operation is either:
  - `["enqueue", x]` — push integer `x`
  - `["dequeue"]` — pop front
  - `["front"]` / `["rear"]` — peek
  - `["is_empty"]` / `["is_full"]` — state query

Output one line per operation result, in order:

```
false
true
true
6
5
true
true
true
true
false
true
-1
-1
```

Mapping:

| Operation | Output |
|-----------|--------|
| `enqueue` | `true` on success, `false` when full |
| `dequeue` | `true` on success, `false` when empty |
| `front` / `rear` | the element, or `-1` if empty |
| `is_empty` / `is_full` | `true` or `false` |

## Notes

- Capacity `k` satisfies `1 ≤ k ≤ 1000`; values are integers.
- Use a count/size field (or one-slot-empty convention) to disambiguate empty vs. full — don't rely on `head == tail` alone.
- All operations must be O(1); per-call output order matches the input command order.
