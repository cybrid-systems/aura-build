# Insert Delete GetRandom O(1)

## Problem Statement

Design a data structure that supports the following operations in **average O(1)** time:

- `insert(val)`: Inserts an item `val` into the set if not already present. Returns `true` if the insertion was successful, `false` otherwise.
- `remove(val)`: Removes an item `val` from the set if present. Returns `true` if the removal was successful, `false` otherwise.
- `getRandom()`: Returns a random element from the current set of elements. The probability of each element being returned must be **uniform** (i.e., equal probability for all elements). This operation must be implemented using the built-in `random` function (or equivalent) and is only valid when the set is non-empty.

Your task is to implement such a data structure.

## Function Signature

Implement the following methods on a class `RandomizedSet`:

```
class RandomizedSet:
    def __init__(self): ...
    def insert(self, val: int) -> bool: ...
    def remove(self, val: int) -> bool: ...
    def getRandom(self) -> int: ...
```

For the harness, expose a top-level function:

```
def solve(operations: list[str], args: list[list[int]]) -> list:
    # Initialize structure, apply each operation in order, return results.
```

## I/O Convention

The harness reads from `CASE0` style lines. Example input format:

```
CASE0
5
insert 1
remove 2
insert 2
getRandom
remove 1
```

Output: each operation's return value on its own line, e.g.:

```
true
false
true
2
true
```

- Line 1: test case label (`CASE0`).
- Line 2: integer `Q` (number of operations).
- Next `Q` lines: one operation per line, with the operation name followed by its (optional) integer argument.

Operations to support:
- `insert <int>`
- `remove <int>`
- `getRandom` (no argument)

## Notes

- All operations must run in **average O(1)** time. A naive approach using only a hash set will fail because `getRandom` would be O(n).
- Hint: combine a **hash map** (mapping value → index) with a **dynamic array** (list) so removals can be done in O(1) by swapping the element to remove with the last element of the array, then popping.
- The number of valid `getRandom` calls is guaranteed; you may assume the structure is non-empty when `getRandom` is invoked.
- Constraints (typical): up to ~2×10⁵ operations total; values fit in a 32-bit signed integer.
