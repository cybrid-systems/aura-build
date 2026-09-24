# Design Circular Deque

## Problem

Design and implement a circular **deque** (double-ended queue) that supports the following operations in **O(1)** time:

- `insertFront(value)` — Add an item to the front. Return `false` if the deque is full.
- `insertLast(value)` — Add an item to the rear. Return `false` if the deque is full.
- `deleteFront()` — Remove and return the front item. Return `-1` if the deque is empty.
- `deleteLast()` — Remove and return the last item. Return `-1` if the deque is empty.
- `getFront()` — Return the front item without removing. Return `-1` if the deque is empty.
- `getRear()` — Return the last item without removing. Return `-1` if the deque is empty.
- `isEmpty()` — Return whether the deque is empty.
- `isFull()` — Return whether the deque is full.

The deque is backed by a circular buffer of fixed capacity `k` passed in the constructor.

Your implementation must produce the correct return value for every operation listed above, given the query sequence.

## Function Signature

```
(solve (deque-init k) operations)
```

The entry point receives:
- `k` — the deque capacity (positive integer).
- `operations` — a vector of operation descriptors (see I/O convention below).

Return a vector containing the result for every operation that yields one. Operations that return `bool` should yield a boolean; operations that return `int` should yield an integer.

## I/O Convention (CASE0 / CASE1 …)

Input is provided on stdin in lines of the form:

```
CASE0 = <k>
CASE0_ops = [insertLast,1,insertFront,2,getFront,isEmpty,deleteFront,getRear,...]
```

- `CASE0` provides the integer `k` (the capacity).
- `CASE0_ops` is a flat list: operation name followed by its argument (when applicable). Arguments are integers; no argument is required for `isEmpty`, `isFull`, `getFront`, or `getRear`.

You may print diagnostic lines as needed; a stub harness will compare the returned vector of results against the expected outputs.

## Notes

- Use a circular buffer (array + head/tail indices with modular arithmetic) so that every operation stays O(1) and uses exactly `k` slots.
- Be careful distinguishing the **full** and **empty** states when `head == tail`; a common technique is to keep one slot unused (capacity `k` but usable length `k - 1`), or to store an explicit count.
- All return values follow the conventions above (booleans for the two `insert*`, `-1` for "empty" queries).
