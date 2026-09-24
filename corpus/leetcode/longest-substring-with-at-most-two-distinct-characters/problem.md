# Longest Substring with At Most Two Distinct Characters

Given a string `s`, find the length of the longest contiguous substring that contains **at most two distinct characters**.

## Function Signature

```python
def solve(s: str) -> int:
    ...
```

## Input

A single line containing the string `s` (1 ≤ |s| ≤ 10^5). The string consists of printable ASCII characters.

## Output

Print a single integer: the length of the longest substring of `s` that uses at most two distinct characters.

## I/O Convention (Aura harness)

- `CASE0=<input>` — the input line(s) for case 0, provided to your `solve` as `s`.
- Your `solve` must return the integer answer; the harness writes it to `CASE0.out`.
- Standard streams (`stdin`/`stdout`) are not used; read only from the function argument.

## Examples

| `s` | Output |
|-----|--------|
| `eceba` | `3` (substring `"ece"`) |
| `ccaabbb` | `5` (substring `"aabbb"` or `"ccaab"`) |
| `a` | `1` |
| `abcd` | `2` (any two-character substring) |

## Notes

- The empty substring has length 0, but `s` is guaranteed to be non-empty.
- An O(n) sliding window with two character counters is sufficient; a hashmap of size ≤ 2 tracks the window's composition.
