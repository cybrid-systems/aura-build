# Single Number III

## Problem

You are given an integer array `nums` in which exactly two elements appear **exactly once** and every other element appears **exactly twice**. Return the two elements that appear once, in any order.

You must write an algorithm that runs in **O(n)** time and uses **O(1)** extra space (the output array does not count toward the space usage).

## Function Signature

```clojure
(defn solve [nums] ...)
```

- `nums` — a vector of integers, length `n` where `2 ≤ n ≤ 3 * 10^4` and `n` is even.
- Return a vector of the two unique integers (any order).

## Input / Output Convention

Each case is provided on a single line:

```
CASE0=<space-separated integers>
CASE1=<space-separated integers>
...
```

For each `CASEi`, read the numbers after the `=` sign, run `solve`, and emit a single line:

```
ANS0=<result>
ANS1=<result>
...
```

where `<result>` is the two unique numbers written as space-separated integers. Example: `ANS0=3 5`.

## Notes

- All numbers fit in a signed 32-bit integer (each in `[-10^9, 10^9]`); the bitwise XOR approach works comfortably within this range.
- The standard trick is: XOR all values to obtain `x = a ^ b`, then isolate one differing bit (e.g., the lowest set bit) and partition the array into two groups, each of which contains exactly one of the unique elements.
- The input guarantees there is **always** exactly one valid answer; do not worry about empty or ambiguous cases.
