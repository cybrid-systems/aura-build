# Seat Reservation Manager

## Problem

You are managing a row of `n` cinema seats numbered from `1` to `n`. Initially, every seat is **unreserved**.

Implement a reservation manager that supports the following operations:

- **`reserve()`** — Return the smallest-numbered seat that is currently unreserved, mark it as reserved, and return its number. It is guaranteed that at least one seat is unreserved when this is called.
- **`unreserve(int seatNumber)`** — Mark the given `seatNumber` as unreserved. It is guaranteed that `seatNumber` was previously reserved.

Design the data structure(s) so that both operations are efficient.

## Function Signature

```
class SeatManager:
    def __init__(self, n: int):
        # initialize manager for seats 1..n (all initially unreserved)
        pass

    def reserve(self) -> int:
        # return the smallest-numbered unreserved seat
        pass

    def unreserve(self, seatNumber: int) -> None:
        # mark seatNumber as unreserved
        pass

def solve(n: int, operations: list[tuple[str, int | None]]) -> list[int | None]:
    # Build a SeatManager over n seats and process each operation in order.
    # For a "reserve" op, append the returned seat number to the output.
    # For an "unreserve" op, append None to the output (or just skip; reserved
    # seats will be used by future reserve ops).
    # Return the list of results from "reserve" operations, in order.
    pass
```

## Input Convention (CASE0)

The harness feeds parameters directly to `solve` (no `stdin`):

```
CASE0 n=5
CASE0 CALL solve n=5 ops=[("reserve",None),("reserve",None),("unreserve",2),("reserve",None)]
```

For each `("reserve", None)` call, your `solve` should collect the seat number returned.
For each `("unreserve", k)` call, nothing is added to the output list.

The harness will compare the returned list against the expected output, for example:
`[1, 2, 3]` (since seat `1` is reserved first, then `2`, then `2` is unreserved and `3` becomes the next smallest).

## Notes

- **Time complexity goal:** each of `reserve` and `unreserve` should ideally run in `O(log n)`.
- A natural approach is a **min-heap** of unreserved seat numbers. For `n` up to large values, you may lazily push seat numbers onto the heap rather than inserting all `1..n` upfront on construction.
- The list `ops` may contain both `"reserve"` and `"unreserve"` operations intermixed; preserve their ordering when processing.
