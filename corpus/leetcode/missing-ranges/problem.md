# Missing Ranges

## Problem

You are given a **sorted array of unique integers** `nums` and an inclusive integer range `[lower, upper]`. Your task is to find all the **missing ranges** — the ranges of integers that are not present in `nums` but should be inside `[lower, upper]`.

For each missing interval, format it using the following rules:

- A **single missing integer** is written as `"a"` (e.g., `2`).
- A **range of missing integers** is written as `"a->b"` (e.g., `1->3`).

Return the formatted ranges as a list of strings, in the order they appear in `[lower, upper]`.

## Examples

### Example 1

```
Input:
lower = 0, upper = 99
nums   = [0, 1, 3, 50, 75]

Output:
["2", "4->49", "51->74", "76->99"]
```

Explanation:
- `0` and `1` are present, so `2` is missing.
- `3` is present, so `4->49` is missing.
- `50` is present, so `51->74` is missing.
- `75` is present, so `76->99` is missing.

### Example 2

```
Input:
lower = -10, upper = -1
nums   = []

Output:
["-10->-1"]
```

Explanation: The array is empty, so the entire range is missing.

## Function Signature

```python
def solve(nums: list[int], lower: int, upper: int) -> list[str]:
    ...
```

## Input / Output Convention (Aura harness)

The harness reads **one case per invocation** from a driver script and calls `solve(nums, lower, upper)`. There is no stdin/stdout. Tests are wired as:

```
CASE0= nums=[0,1,3,50,75]  lower=0  upper=99  -> ["2","4->49","51->74","76->99"]
CASE1= nums=[]              lower=-10 upper=-1 -> ["-10->-1"]
CASE2= nums=[-1]            lower=-1  upper=-1 -> []
CASE3= nums=[5]             lower=1   upper=10 -> ["1->4","6->10"]
```

Your `solve` function must return the exact list of strings expected per case.

## Notes

- `nums` is sorted in strictly increasing order and contains no duplicates.
- Edge cases to consider:
  - `nums` is **empty**.
  - The first element of `nums` equals `lower` (no leading missing range).
  - The last element of `nums` equals `upper` (no trailing missing range).
  - Adjacent elements in `nums` differ by exactly `1` (no missing range between them).
- The returned strings must use `"->"` as the separator for multi-element ranges and no separator for single integers.
