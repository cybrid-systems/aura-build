# Majority Element

## Problem

Given an integer array `nums` of length `n`, find the element that appears strictly more than `⌊n/2⌋` times. You may assume that such an element always exists.

Return that element.

## Function Signature

```clojure
(solve nums)
```

- `nums` — a vector of integers, length `n` (1 ≤ n ≤ 10^5, |nums[i]| ≤ 10^9).
- Return the majority element.

## Input / Output Convention

Input arrives on standard input, **no prompt strings**. The harness reads a single test case of the following shape:

```
CASE0=<json-encoded vector of integers>
```

For example:

```
CASE0=[2,2,1,1,1,2,2]
```

The expected output is the majority element printed on its own line:

```
2
```

For multiple cases, additional `CASE1=…`, `CASE2=…` lines may follow; print one result per line, in order.

## Notes

- Aim for **O(n)** time and **O(1)** extra space (Boyer–Moore voting algorithm fits perfectly).
- The problem guarantees a majority element exists, so a second verification pass is optional but recommended in adversarial tests.
- The input is JSON-encoded; do not assume it is whitespace-separated numbers.
