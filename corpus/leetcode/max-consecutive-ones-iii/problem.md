# Max Consecutive Ones III

## Problem

Given a binary array `nums` (each element is `0` or `1`) and an integer `k`, you may flip at most `k` zeros into ones. Return the length of the longest contiguous subarray containing only `1`s after performing at most `k` such flips.

## Function Signature

```python
def solve(nums: list[int], k: int) -> int:
    ...
```

## Input / Output Convention

The harness supplies the inputs as two `CASE0_...` lines, read in order:

```
CASE0_NUMS=[0,1,1,0,0,0,1,1,0,0,1,1,0,0,0,1,1,1,0]
CASE0_K=3
```

- `CASE0_NUMS` is a JSON array of integers (each `0` or `1`).
- `CASE0_K` is a JSON integer (`0 <= k <= len(nums)`).

Your `solve` function receives the parsed `nums` and `k` and must return a single integer: the maximum length of a subarray of `1`s achievable by flipping at most `k` zeros.

### Example

Input:
```
CASE0_NUMS=[1,1,1,0,0,0,1,1,1,1,0]
CASE0_K=2
```

Output:
```
6
```

(The subarray `0,0,0,1,1,1,1,0` — flipping the two zeros at positions 4–5 yields six consecutive `1`s.)

## Notes

- A two-pointer / sliding window approach is natural: maintain a window with at most `k` zeros inside it and track the maximum window length.
- When `k == 0`, the answer reduces to the longest run of `1`s already present in the array.
- Time complexity `O(n)` with `O(1)` extra space is easily achievable.
