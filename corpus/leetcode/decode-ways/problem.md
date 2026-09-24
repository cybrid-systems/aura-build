# Decode Ways

## Problem

A message consisting only of digits has been encoded using the classic A–Z mapping:

```
1 → A, 2 → B, ..., 9 → I,
10 → J, 11 → K, ..., 26 → Z
```

Given a string `s` of digits (length `1 ≤ n ≤ 5000`), count the number of distinct ways it can be **decoded** into a sequence of letters. The decoded sequence must cover the entire string, and each group of one or two consecutive digits must represent a value from `1` to `26`. Leading zeros are not allowed.

Return the count. Since the answer can be very large, output it modulo `10^9 + 7`.

## Function Signature

```lisp
(defun solve ()
  ;; reads a single line from input
  ;; returns the answer)
```

In other languages exposed by the harness, the equivalent is:

```python
def solve() -> int:
    ...
```

## Input

A single line containing the digit string `s`.

```
CASE0=12
CASE0_ANS=2
```

Explanation: `12` can be decoded as `(1)(2) → "AB"` or `(12) → "L"`, so the answer is `2`.

## Output

Print the number of decodings modulo `10^9 + 7`.

## Notes

- `s` may contain leading zeros. Any decoding that requires a leading zero is invalid, so the answer may be `0` (e.g., `"06"`).
- Use the recurrence `dp[i] = dp[i-1] + dp[i-2]` with appropriate validity checks on the last one and last two digits. Alternatively, walk the string once with constant auxiliary state.
- Modulus is `10^9 + 7`.
