# Rotate List

Given the head of a singly linked list and an integer `k`, rotate the list to the right by `k` places. Rotation moves the last `k` nodes to the front, preserving the relative order of the remaining nodes.

The list is given as a sequence of node values terminated by a sentinel value (see I/O convention). The length of the list is between `0` and `10^5`, node values fit in a 32-bit signed integer, and `k` may be larger than the list length (use `k % n`).

## Function Signature

```python
def solve(head: list[int], k: int) -> list[int]:
    ...
```

`head` is a flat list of node values in order from head to tail (with `None` represented by a sentinel, see below). Return the rotated list as a flat list of values.

## Input / Output Convention

Input is provided on a single line via the `CASE0` environment variable in the form:

```
CASE0=<sentinel> <k> <v1> <v2> ... <vN>
```

Where:

- `<sentinel>` is the integer used to terminate the list (e.g. `-1` or `0`); it does not appear in the data and must not appear in the output.
- `<k>` is a non-negative integer rotation count.
- `<v1> <v2> ... <vN>` are the node values of the list, in order from head to tail. `0 <= N <= 10^5`.

Parse the line, build the list, rotate it, and emit the result on stdout as a single space-separated line of values. If the resulting list is empty, print an empty line. Do not include the sentinel in the output.

### Example

Input (via `CASE0`):
```
CASE0=-1 2 1 2 3 4 5
```

Output:
```
4 5 1 2 3
```

## Notes

- If `N == 0`, the output is an empty line regardless of `k`.
- Normalize `k` with `k % N` to handle large rotations efficiently.
- Aim for `O(N)` time and `O(1)` extra space (in-place on the value array).
