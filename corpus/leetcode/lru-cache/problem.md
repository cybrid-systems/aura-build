# LRU Cache

## Problem

Design a **Least Recently Used (LRU) cache** data structure that supports the following operations in **O(1) average time**:

- `get(key)` — Return the value associated with the given `key`. If the key does not exist, return `-1`. Accessing an item makes it the **most recently used**.
- `put(key, value)` — Insert or update the value for the given `key`. If inserting causes the total number of keys to exceed the cache's `capacity`, **evict the least recently used key** before inserting the new one. Inserting/updating an item makes it the **most recently used**.

Implement the cache class so that both operations run in constant amortized time.

---

## Function Signature (hint)

```python
class LRUCache:
    def __init__(self, capacity: int): ...
    def get(self, key: int) -> int: ...
    def put(self, key: int, value: int) -> None: ...
```

(Equivalent signatures in other languages are acceptable.)

---

## Input / Output Convention (Aura harness, stdin-less)

The driver constructs the cache and calls methods directly; there is **no stdin**. However, the harness also accepts a textual log format on `CASE0=...` lines for reference and replay:

```
CASE0=init 2
CASE0=put 1 1
CASE0=put 2 2
CASE0=get 1     -> 1
CASE0=put 3 3   -> evicts key 2
CASE0=get 2     -> -1
CASE0=put 4 4   -> evicts key 1
CASE0=get 1     -> -1
CASE0=get 3     -> 3
CASE0=get 4     -> 4
```

Where:
- `init C` constructs an LRU cache of capacity `C`.
- `put K V` inserts/updates key `K` with value `V`.
- `get K` returns the value for key `K`, or `-1` if absent (and prints `-> V`).
- A `-> evicts key K` annotation is informational (it is **not** a separate command — it is what the correct implementation must do as a side effect of the preceding `put` when capacity is exceeded).

The final answer is the list of values produced by every `get` call, in order.

---

## Notes

- Both `get` and `put` must be **O(1)** amortized. The classical solution combines a **hash map** (key → node) with a **doubly linked list** (ordering by recency: head = most recent, tail = least recent).
- Updating or accessing an existing key counts as a "use" — the node must be moved to the front of the list.
- Eviction only happens on `put` when the new key is **not already present** and the cache is at capacity.
- Capacity is at least `1`. Keys and values fit in a 32-bit signed integer.
