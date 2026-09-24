# Trapping Rain Water

## Problem

Given `n` non-negative integers representing an elevation map where the width of each bar is `1`, compute how much water it can trap after raining.

Formally, given an array `heights` of length `n`, the water trapped above position `i` is:

```
min(max_left[i], max_right[i]) - heights[i]
```

(if this value is negative, treat it as `0`). The total trapped water is the sum of this value over all positions.

### Example

```
heights = [0,1,0,2,1,0,1,3,2,1,2,1]
```
- Total trapped water: **6**

```
heights = [4,2,0,3,2,5]
```
- Total trapped water: **9**

## Function Signature

```haskell
solve :: [Int] -> Int
```

- **Input:** A list of non-negative integers `heights`.
- **Output:** A single integer — the total units of trapped water.

## I/O Convention

The harness drives I/O through `CASE0` lines on stdout. Your `solve` function receives the elevation map and must return the answer.

```
CASE0=[0,1,0,2,1,0,1,3,2,1,2,1]
CASE0_answer=6
```

```
CASE0=[4,2,0,3,2,5]
CASE0_answer=9
```

## Notes

- The empty list (`[]`) and a single-element list both yield `0`.
- A classic two-pointer solution maintains `left` and `right` indices along with `max_left` and `max_right` running maxima, processing the side with the smaller current maximum each step — this runs in O(n) time and O(1) extra space.
- Values are bounded by the integer range; the answer fits in a standard `Int` for the given constraints.
