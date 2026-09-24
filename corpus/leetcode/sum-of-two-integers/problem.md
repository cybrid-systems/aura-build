# Sum of Two Integers

## Problem

Given two 32-bit signed integers `a` and `b`, return the sum of `a` and `b` **without using the `+` or `-` operators**. You may use any other operators (bitwise, comparison, logical, shifts, etc.).

### Function signature

```clojure
(defn solve [a b] ...)
```

## Input / Output

The harness reads `CASE0=` style lines from `clojure.core/*in*`. Each line provides the values for a single test case.

**Input format**

```
CASE0=2 3
CASE1=-1 1
CASE2=0 0
```

- Each `CASE<n>=` line contains two space-separated 32-bit signed integers.

**Output format**

```
ANS0=5
ANS1=0
ANS2=0
```

- For each `CASE<n>=` line, print `ANS<n>=` followed by the decimal integer result on its own line.

## Notes

- The range of inputs and outputs fits within a 32-bit signed integer (`-2^31` to `2^31 - 1`).
- Use bitwise operations (`bit-and`, `bit-or`, `bit-xor`, `bit-shift-left`, `bit-shift-right`, `bit-not`) to simulate addition: XOR gives the sum without carry, AND followed by a left shift gives the carry, and the process repeats until there is no carry.
- Handle negative numbers correctly using two's-complement representation.
