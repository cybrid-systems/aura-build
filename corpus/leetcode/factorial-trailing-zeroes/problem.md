# Factorial Trailing Zeroes

## Problem

Given an integer `n`, compute how many trailing zeroes are in the decimal representation of `n!` (n factorial).

Trailing zeroes are produced by factors of `10 = 2 × 5`. Since factors of 2 are always more abundant than factors of 5 in `n!`, the number of trailing zeroes equals the total number of times `5` appears as a prime factor in the numbers `1, 2, …, n`.

## Function Signature

```lisp
(defun solve (n)
  ;; returns: integer (number of trailing zeroes in n!)
  )
```

## Input

The input consists of a single line:

```
n
```

where `n` is a non-negative integer (`0 ≤ n ≤ 10^9`).

## Output

Print a single integer: the number of trailing zeroes in `n!`.

## Examples

### Example 1
**Input:**
```
5
```
**Output:**
```
1
```
Explanation: `5! = 120` has one trailing zero.

### Example 2
**Input:**
```
100
```
**Output:**
```
24
```

### Example 3
**Input:**
```
0
```
**Output:**
```
0
```
Explanation: `0! = 1` has no trailing zeros.

## Notes

- Iterate `n / 5 + n / 25 + n / 125 + …` (each power of `5` contributes one factor of `5` per multiple it appears in). Use integer (floor) division.
- Use a `long`/`64-bit` type — the answer can exceed 32-bit range (e.g. `n = 10^9` yields ~`2.5 × 10^8`).
- Expected complexity: **O(log₅ n)** time, **O(1)** additional space.
- No secrets are exposed; the case line below is illustrative only.

### Sample I/O Convention (harness format)

```
CASE0=100
CASE0RESULT=24
```
