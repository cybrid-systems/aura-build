# Maximum Sum of Two Non-Overlapping Subarrays

## Problem

You are given an array of integers `nums` and two integers `firstLen` and `secondLen`. Return the **maximum** possible sum of elements in two **non-overlapping** subarrays of lengths `firstLen` and `secondLen`.

The two subarrays cannot share any index. Their order within the array does not matter — the subarray of length `firstLen` may appear either before or after the subarray of length `secondLen`. Return the maximum achievable total sum.

## Function Signature

```python
def solve(nums: list[int], firstLen: int, secondLen: int) -> int
```

## Input / Output Convention

The harness invokes `solve` directly. There is no stdin/stdout. Tests adapt the inputs as follows, shown for reference:

```
CASE0=  nums = [0,6,5,2,2,5,1,9,4]; firstLen = 1; secondLen = 2
CASE1=  nums = [3,8,1,3,2,1,4,4];   firstLen = 2; secondLen = 3
CASE2=  nums = [2,1,5,6,0,9,5,0,3,8]; firstLen = 1; secondLen = 1
```

For each case, the harness calls `solve(nums, firstLen, secondLen)` and checks the returned integer.

## Notes

- `len(nums) >= firstLen + secondLen` is guaranteed.
- The two candidate subarrays are disjoint by index, but they may touch at a boundary (i.e., the end of one can be adjacent to the start of the other).
- A natural approach is a sliding window of one length while tracking the best prefix (or suffix) sum for the other length; compute the answer in both orders and take the maximum.
- Complexity target: `O(n)` time and `O(1)` extra space (excluding the input array).
