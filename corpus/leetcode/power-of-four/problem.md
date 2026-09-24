# Power of Four

## Problem

Given an integer `n`, determine whether it is a power of four. Return `true` if `n` is a power of four, and `false` otherwise.

An integer `n` is a power of four if there exists an integer `x` such that `n == 4^x`.

**Constraints:**
- `-2^31 <= n <= 2^31 - 1`

## Function Signature

```clojure
(defn solve [n] ...)
```

## Input

The input is provided on standard input as a single integer. The Aura harness exposes the value via the `solve` function.

## Output

Print `"true"` if `n` is a power of four, otherwise print `"false"`.

## Examples

```
CASE0=16
CASE0out=true

CASE1=5
CASE1out=false

CASE2=1
CASE2out=true

CASE3=-4
CASE3out=false
```

## Notes

- `1` is considered a power of four (`4^0 = 1`).
- Negative numbers and zero are not powers of four.
- A useful observation: powers of four have exactly one bit set, and that bit is positioned at an even index (0, 2, 4, ...). This can be checked efficiently with a single bitwise mask such as `0x55555555` (hex).
- The solution should run in **O(1)** time using only constant extra work.
