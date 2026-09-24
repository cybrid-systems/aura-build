# Power of Two

## Statement

Given a single non‑zero integer `n`, determine whether it is a power of two. Return `true` if `n` can be written as `2^k` for some integer `k >= 0`, otherwise return `false`.

Note: `0` is **not** considered a power of two.

## Function Signature

```lisp
(defun solve (n)
  ;; returns T or NIL
  )
```

## Input

The input is provided via a single `CASE0` line on the first line of stdin:

```
CASE0=<integer>
```

Where `<integer>` is a non‑zero signed integer (positive or negative). Your function receives this value as its argument.

## Output

Write `"true"` to stdout if `n` is a power of two, otherwise write `"false"`.

## Examples

```
CASE0=1
-> true
```

```
CASE0=16
-> true
```

```
CASE0=3
-> false
```

```
CASE0=-4
-> false
```

```
CASE0=1024
-> true
```

## Notes

- Use the binary representation of `n`: a positive power of two has exactly one bit set.
- A fast check for positive `n` is that `n & (n - 1) == 0`. Combined with `n > 0`, this fully characterizes powers of two.
- Negative numbers are never powers of two, since powers of two are positive by definition.
