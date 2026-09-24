# Permutations

## Problem

Given a list of `n` distinct integers, generate all possible permutations of the elements.

A permutation is an arrangement of all `n` elements in some order. The order of permutations in the output does not matter, but every distinct ordering must appear exactly once.

### Examples

`nums = [1, 2, 3]`

All permutations:
```
[1, 2, 3]
[1, 3, 2]
[2, 1, 3]
[2, 3, 1]
[3, 1, 2]
[3, 2, 1]
```

`nums = [0, 1]`

All permutations:
```
[0, 1]
[1, 0]
```

`nums = [1]`

All permutations:
```
[1]
```

### Constraints

- `1 ≤ n ≤ 8`
- All elements in `nums` are distinct.

## Function Signature

```
solve(nums: list[int]) -> list[list[int]]
```

The function receives a list of distinct integers and must return a list containing every permutation as a separate list.

## Input Format

The harness reads cases from a built-in `CASE0` array. Each case is provided as a JSON-like declaration written before the program runs, for example:

```
CASE0=[
  {"nums": [1, 2, 3]},
  {"nums": [0, 1]},
  {"nums": [1]}
]
```

There is no stdin; values are taken directly from each `CASE0` entry.

## Output Format

Print results for each case in order. For each input list, print every permutation on its own line, with elements separated by spaces. Separate cases with a single blank line.

For example, given the three cases above, output:

```
1 2 3
1 3 2
2 1 3
2 3 1
3 1 2
3 2 1

0 1
1 0

1
```

## Notes

- The order of permutations within a single case is not graded, but every valid permutation must be produced exactly once.
- Duplicates must not appear, even though the input itself is guaranteed to have distinct elements.
- `n` is small (`n ≤ 8`), so an algorithmic solution is straightforward; an exhaustive approach that scales to `8!` results is acceptable.
