# Count and Say

## Problem

The **count-and-say sequence** is a self-describing sequence of strings defined as follows:

- `countAndSay(1)` is the string `"1"`.
- For `n > 1`, `countAndSay(n)` is the **count-and-say** of `countAndSay(n - 1)`: you read off the digits of the previous term, grouping consecutive identical digits and stating the count followed by the digit.

Formally, to produce the next term from a string `s`:
- Scan `s` from left to right.
- For each maximal run of the same character (digit) of length `k`, append `k` followed by that character to the result.

### Examples

- `countAndSay(1) = "1"`
- `countAndSay(2) = "11"` (one `1`)
- `countAndSay(3) = "21"` (two `1`s)
- `countAndSay(4) = "1211"` (one `2`, then one `1`)
- `countAndSay(5) = "111221"` (one `1`, one `2`, two `1`s)
- `countAndSay(6) = "312211"`

## Function Signature

```
(defn solve [n] ...)
```

- `n`: an integer, `1 ≤ n ≤ 30`.
- Returns: the `n`th term of the count-and-say sequence, as a string.

## Input / Output Convention

The harness does **not** read from stdin. Instead, each test case is provided as a `CASE` line in the problem file:

```
CASE0=1
CASE1=4
CASE2=6
```

- For each `CASEi=n`, call `(solve n)` and the harness records the returned string.
- The result for the example cases should be:
  - `CASE0` → `"1"`
  - `CASE1` → `"1211"`
  - `CASE2` → `"312211"`

## Notes

- The output is always a string of digits; do not convert it to a number, since lengths grow quickly and do not fit in standard integer types.
- `n = 30` produces a result of length ~5,000 characters, so prefer building the answer using string concatenation (e.g., `str`, `apply str`) rather than converting to/from numbers.
- A straightforward iterative construction — starting from `"1"` and applying the run-length transformation `n - 1` times — is more than fast enough for `n ≤ 30`.
