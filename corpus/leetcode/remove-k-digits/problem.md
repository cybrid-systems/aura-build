# Remove K Digits

## Statement

Given a non-negative integer `num` represented as a string, remove exactly `k` digits from it so that the resulting number is the smallest possible (in numeric value). The result must not have leading zeros, except when the result is exactly `"0"`.

You may assume `k` is non-negative and `k` is at most the length of `num`.

Implement `solve` that returns the smallest resulting string.

## Function Signature

```clojure
(defn solve [num k] ...)
```

- `num`: a string of digit characters `'0'`–`'9'` (no leading sign).
- `k`: an integer, `0 <= k <= (count num)`.
- Returns: a string with leading zeros removed (or `"0"` if the value is zero).

## Input / Output (Aura harness)

The harness invokes `solve` directly with no stdin. Each case is fixed:

```
CASE0=("1432219", 3) -> "1219"
CASE1=("10200", 1)   -> "200"
CASE2=("10", 2)      -> "0"
```

These three cases are the canonical examples for this problem.

## Notes

- The greedy strategy uses a monotonic stack: pop a larger previous digit when a smaller one appears, ensuring the leftmost digits are minimized first.
- After processing, if `k > 0` the remaining suffix is trimmed; if the stack is empty, return `"0"`.
- Time complexity `O(n)` and space `O(n)` is achievable.
