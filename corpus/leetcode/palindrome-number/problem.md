# Palindrome Number

## Statement

Determine whether a signed 32-bit integer reads the same forwards and backwards. The integer may be negative.

An integer is a palindrome if its decimal representation is symmetric about its centre. For example, `121` and `0` are palindromes, while `-121`, `123`, and `10` are not. Leading zeros are not permitted in the input, so any palindrome that begins with `0` must itself be `0`.

**Constraints**

- The value is a signed 32-bit integer: `-2^31 <= x <= 2^31 - 1`.

**Objective:** Decide the palindrome property without allocating auxiliary string storage proportional to the number of digits.

## Function Signature

Write the function with this exact shape:

```clojure
(defn solve [x] ...)
```

- `x` — a 32-bit signed integer (may be negative).
- Returns `true` if `x` is a palindrome, otherwise `false`.

## Input / Output Convention

The harness supplies a single integer directly to `solve`; there is no stdin or stdout. A representative `CASE0` block illustrates the expected return value for a sample input:

```
CASE0=121 => true
```

The harness runs additional private cases after `CASE0`. Your implementation must satisfy them as well.

## Notes

- A straightforward approach reverses the second half of the digits using arithmetic and compares it to the first half, avoiding the cost of building a string. The well-known `reverse-half` technique runs in `O(log_10 |x|)` time and `O(1)` extra space.
- Treat `0` as a palindrome; treat every negative number as not a palindrome because of the leading minus sign.
