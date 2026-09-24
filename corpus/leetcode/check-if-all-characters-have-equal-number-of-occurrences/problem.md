# Check if All Characters Have Equal Number of Occurrences

Given a string `s`, determine whether all characters that appear in `s` occur the same number of times.

Equivalently, the frequency of every distinct character must be identical (i.e., the string is "balanced" in the sense that no character appears more or fewer times than another).

## Function Signature

```python
def solve(s: str) -> bool:
    ...
```

## Input / Output Convention (Aura harness, no stdin)

Each case is provided on a single line as `CASE0=<value>` (the harness strips the prefix and passes the value to `solve`):

```
CASE0=ababab
```

Output is written by the harness based on the return value of `solve`. For boolean problems the harness prints `True` / `False` (or `1` / `0` depending on configuration); assume `True` means "yes, all characters occur the same number of times" and `False` otherwise.

### Examples

| Input line          | Return | Reason                                                       |
|---------------------|--------|--------------------------------------------------------------|
| `CASE0=ababab`      | `True` | `'a'` appears 3 times, `'b'` appears 3 times.                |
| `CASE0=aaaaabbbbb`  | `True` | `'a'` appears 5 times, `'b'` appears 5 times.                |
| `CASE0=abc`         | `True` | Each of `'a'`, `'b'`, `'c'` appears exactly 1 time.          |
| `CASE0=aabbcc`      | `True` | Each of `'a'`, `'b'`, `'c'` appears 2 times.                 |
| `CASE0=aabbccc`     | `False`| `'a'`/`'b'` appear 2 times but `'c'` appears 3 times.        |
| `CASE0=aaaa`        | `True` | Only one distinct character — trivially balanced.            |
| `CASE0=`            | `True` | Empty string has no characters, vacuously balanced.          |

## Notes

- An empty string and any single-character string should return `True`.
- The string may contain any characters (letters, digits, symbols, whitespace); treat each character as a distinct key.
- Complexity target: `O(n)` time, `O(k)` auxiliary space where `k` is the number of distinct characters (bounded by the size of the alphabet or `n`).
