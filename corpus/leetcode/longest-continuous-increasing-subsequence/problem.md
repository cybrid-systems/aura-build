# Longest Continuous Increasing Subsequence

## Statement

Given an array of integers `nums`, find the length of the longest **continuous** (contiguous) strictly increasing subsequence.

A continuous strictly increasing subsequence is a maximal run of consecutive elements where each element is strictly greater than the one before it.

Return its length.

## Input Format

The input is provided on standard input.

- Line 1: an integer `N`, the number of elements.
- Line 2: `N` space-separated integers `nums[0] … nums[N-1]`.

## Output Format

A single integer: the length of the longest continuous strictly increasing run.

## Function Signature

```haskell
solve :: [Int] -> Int
```

The driver reads `N` and the list, then prints `solve nums`.

## Constraints

- `1 <= N <= 10^5`
- `-10^9 <= nums[i] <= 10^9`

## Examples

### Example 0

Input:
```
6
1 2 3 2 4 5
```

Output:
```
3
```
(Explanation: the run `1,2,3` has length 3; `2,4,5` also length 3.)

### Example 1

Input:
```
5
5 4 3 2 1
```

Output:
```
1
```
(Explanation: no adjacent pair is strictly increasing.)

### Example 2

Input:
```
1
7
```

Output:
```
1
```

## Notes

- "Continuous" / "contiguous" means the elements must be adjacent in the original array; this is **not** the classic LIS problem.
- A single pass with a running counter (resetting whenever the next element is not strictly larger) is sufficient and runs in `O(N)` time and `O(1)` extra space.
- Edge cases to consider: `N = 0` or `N = 1`, strictly decreasing arrays, equal consecutive elements (which must **break** the run, since the requirement is strictly increasing), and runs that span the entire array.
