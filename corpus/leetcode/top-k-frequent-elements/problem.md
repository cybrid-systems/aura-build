# Top K Frequent Elements

## Problem

Given an integer array `nums` and an integer `k`, return the `k` most frequent elements. The answer may be returned in any order.

Your task is to write a function `solve` that, given `nums` (a list of integers) and `k` (an integer), returns a list of the `k` most frequent integers. Ties in frequency can be broken arbitrarily (any `k` elements sharing a top frequency set is acceptable).

### Function Signature

```
def solve(nums: list[int], k: int) -> list[int]:
```

### Constraints

- `1 <= len(nums) <= 10^5`
- `-10^4 <= nums[i] <= 10^4`
- `1 <= k <= number of distinct elements in nums`

## Input / Output (Aura harness)

The harness reads the following `CASE0=...` style lines from the prompt payload and passes them directly to your `solve` function (no stdin):

```
CASE0.nums=[1,1,1,2,2,3]
CASE0.k=2
```

Your `solve` must return a list of integers. For the example above, both `[1, 2]` and `[2, 1]` are accepted.

### Example 1

```
CASE0.nums=[1,1,1,2,2,3]
CASE0.k=2
```

Expected output (order may vary): `[1, 2]`

### Example 2

```
CASE0.nums=[1]
CASE0.k=1
```

Expected output: `[1]`

### Example 3

```
CASE0.nums=[4,4,4,5,5,6,7,7,7,7,8]
CASE0.k=3
```

Expected output (any order): one of `[7, 4, 5]`, `[7, 4, 8]`, etc., as long as the three returned elements are among the top-3 by frequency.

## Notes

- Aim for `O(n)` average time using a hash map for counting plus a bucket / heap selection step. An `O(n log n)` sort-based solution will also be accepted.
- The output list length must equal `k`. The harness compares as a multiset, so element order does not matter.
- Do not mutate the input list `nums`.
