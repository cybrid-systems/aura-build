# First Missing Positive

**Category:** Arrays  
**Difficulty:** Hard  
**Time Limit:** 1 s  
**Memory Limit:** 256 MB

## Problem

Given an unsorted integer array `arr` of length `n`, return the **smallest missing positive integer**.

That is, find the smallest positive integer (1, 2, 3, …) that does **not** appear in `arr`.

You must solve this in **O(n)** time and **O(1)** extra space (the input array itself may be modified; output must remain allowed as a single integer return).

## Function Signature

```aura
fn solve(arr: [i64]) -> i64
```

- `arr` — non-empty array of signed integers, length up to `10^5`. Values may be negative, zero, or larger than `n`.
- **Return:** the smallest positive integer missing from `arr`.

## Input / Output Convention (CASE0)

The harness drives the `solve` function directly — there is no stdin. Test cases are encoded as:

```
CASE0 = {
    "input":    [arr]        // array literal, e.g. [3, 4, -1, 1]
    "expected": <i64>        // e.g. 2
}
CASE1 = { "input": [1, 2, 0], "expected": 3 }
```

Each `CASEk` line defines one invocation of `solve`. Multiple cases may be supplied.

## Examples

| Input | Output | Explanation |
|---|---|---|
| `[3, 4, -1, 1]` | `2` | 1 is present, 2 is missing. |
| `[1, 2, 0]`     | `3` | 1 and 2 present, 3 missing. |
| `[-5, -1, 0]`   | `1` | No positive integers present. |
| `[1, 2, 3, 4]`  | `5` | Continuous run from 1..n missing the next. |

## Constraints

- `1 ≤ n ≤ 100_000`
- `-10^9 ≤ arr[i] ≤ 10^9`

## Notes

- The naïve O(n) solution uses a hash set — that violates the **O(1) extra space** rule.
- Hint: the answer is always in the range `[1, n+1]`. You can place each value `v` (with `1 ≤ v ≤ n`) at index `v-1` via in-place swaps, then scan for the first index `i` where `arr[i] != i+1`.
- After placement, any index `i` with `arr[i] != i+1` means `i+1` is missing; if all match, the answer is `n+1`.
