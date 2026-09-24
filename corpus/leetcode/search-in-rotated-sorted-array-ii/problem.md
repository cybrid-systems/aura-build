# Search in Rotated Sorted Array II

## Problem

You are given a sorted array of integers `nums` that has been rotated at an unknown pivot (e.g., `[0,1,2,4,5,6,7]` might become `[4,5,6,7,0,1,2]`). The array may also contain **duplicates**.

Given the array `nums` and an integer `target`, return `true` if `target` exists in the array, otherwise return `false`.

Your solution should run in **O(log n)** average time, though the worst case may degrade to **O(n)** when many duplicates are present (this is expected and unavoidable for this variant).

## Function Signature

```python
def solve(nums: list[int], target: int) -> bool
```

## Input Convention (CASE format)

The harness reads lines from the `CASE` source. Each test case is two lines:

```
CASE0=nums=[4,5,6,7,0,1,2]&target=0
CASE1=nums=[2,5,6,0,0,1,2]&target=0
CASE2=nums=[1]&target=0
```

- `nums=` is a JSON-style array of integers (comma-separated, brackets required).
- `target=` is a single integer.
- The function is called with the parsed values and the expected output is the boolean result (`true`/`false`).

## Examples

| Input | Output | Explanation |
|---|---|---|
| `nums=[4,5,6,7,0,1,2], target=0` | `true` | `0` is present |
| `nums=[4,5,6,7,0,1,2], target=3` | `false` | `3` is not present |
| `nums=[2,5,6,0,0,1,2], target=0` | `true` | `0` is present (with duplicates) |
| `nums=[1], target=1` | `true` | Single-element match |
| `nums=[], target=5` | `false` | Empty array |

## Notes

- You may assume `nums` contains at least 0 elements and `len(nums) <= 10^5`.
- The "rotated sorted with duplicates" twist means the standard binary-search check must handle the case where `nums[left] == nums[mid] == nums[right]`. In that situation, simply shrink the window by moving one boundary inward — this is the only way to preserve correctness when the array cannot be cleanly halved.
- Aim for the cleanest implementation: handle the ambiguous case explicitly rather than falling back to a linear scan.
