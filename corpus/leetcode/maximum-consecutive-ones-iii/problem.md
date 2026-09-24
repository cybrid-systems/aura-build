# Max Consecutive Ones III

Given a binary array `nums` and an integer `k`, you may flip at most `k` zeroes to ones. Return the length of the longest contiguous subarray containing only ones after performing at most `k` flips.

## Function Signature

```python
def solve(nums: list[int], k: int) -> int:
    ...
```

## Input

The harness feeds parameters directly to `solve`. There is no stdin. For local sanity checks, the equivalent raw form is:

```
CASE0=1 1 1 0 0 0 1 1 1 1 0 | k=2
CASE1=0 0 1 1 0 0 1 1 1 0 0 0 1 1 1 1 0 | k=3
```

Each `CASE` line is `nums | k=n`, where `nums` is space-separated `0`/`1` values and `k` is the maximum number of zeroes you are allowed to flip.

## Output

`solve` returns a single integer: the maximum length of a subarray achievable by flipping at most `k` zeroes.

## Examples

| nums                          | k  | Output | Explanation                                 |
| ----------------------------- | -- | ------ | ------------------------------------------- |
| `[1,1,1,0,0,0,1,1,1,1,0]`     | 2  | 6      | Flip the two zeros at indices 3-4           |
| `[0,0,1,1,0,0,1,1,1,0,0,0,1,1,1,1,0]` | 3 | 10 | Flip up to 3 zeros in the long middle block |
| `[1,1,1,1]`                   | 0  | 4      | No flips needed                             |

## Constraints

- `1 <= len(nums) <= 10^5`
- `nums[i]` is `0` or `1`
- `0 <= k <= len(nums)`

## Notes

- A sliding window maintaining a count of zeroes inside the window works in `O(n)` time and `O(1)` extra space.
- Expand the right edge, and when the zero count exceeds `k`, shrink from the left until it is back within budget; track the window length.
