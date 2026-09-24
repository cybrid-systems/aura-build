# Jump Game

## Problem

You are given an array of non‑negative integers `nums` where each element represents your **maximum jump length** from that position. Starting at index `0`, determine whether it is possible to reach the **last index**.

Return `true` if the last index is reachable, otherwise `false`.

## Function Signature

```python
def solve(nums: list[int]) -> bool:
    ...
```

## Input / Output

The harness reads the case description from variables and writes the result to standard output.

- **Input (`CASE0` line):** a single JSON array of non‑negative integers, e.g.  
  `CASE0=[2,3,1,1,4]`
- **Output:** print `True` or `False` (Python literal style) followed by a newline.

### Examples

| `CASE0` | Output |
|---|---|
| `[2,3,1,1,4]` | `True` |
| `[3,2,1,0,4]` | `False` |
| `[0]` | `True` |
| `[1,0,1,0]` | `False` |

## Notes

- `nums` has length `1 ≤ n ≤ 10^4`, with values in `0 ≤ nums[i] ≤ 10^5`.
- A classic greedy approach works in O(n) time and O(1) extra space: track the farthest index reachable so far while scanning left‑to‑right.
- No jump is needed when the array has a single element — consider it already reached.
