# Restore IP Addresses

## Problem

Given a string `s` consisting only of digits, return all valid IP addresses that can be formed by inserting three dots into `s` so that each segment between dots is a valid IP octet.

An IP octet must satisfy:
- It contains between 1 and 3 digits.
- It has no leading zeros (unless the octet itself is exactly `"0"`).
- Its integer value is between 0 and 255 inclusive.

The four octets together must use **all** characters of `s` exactly once.

Return the addresses as strings in the `"a.b.c.d"` format.

## Function Signature

```python
def solve(s: str) -> list[str]:
    ...
```

## Input / Output Convention

The harness reads and writes nothing via `stdin`/`stdout`. Instead, the driver calls `solve(s)` directly with values produced from the `CASE0`...`CASEn` lines below.

Lines in the input file are of two kinds:

```
CASE0 = "25525511135"
CASE1 = "00000"
CASE2 = "101023"
```

Each `CASEk = "..."` line defines the string `s` used as the argument to `solve` for case index `k`. Quoted string literals are passed as plain Python strings (no surrounding quotes).

The function `solve` must return a `list[str]` containing every valid IP address. The expected ordering is the lexicographic order produced by the canonical backtracking traversal (placing dots from left to right).

## Notes

- If `s` has fewer than 4 or more than 12 characters, the result is `[]`.
- The same address should appear only once in the output list (duplicates cannot occur under correct pruning, but treat the output as a set semantically).
- Time complexity is bounded by the number of valid placements of three dots, which is at most `O(3^3) = 27` per call after length pruning.
