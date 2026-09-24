# Maximum Points You Can Obtain from Cards

## Problem

You are given an array of `n` integers and an integer `k`. In one operation you may take either the leftmost or the rightmost remaining card and add its value to your score; the card is then removed. After exactly `k` operations, the remaining cards are discarded.

Determine the maximum total score you can obtain by choosing optimally which end to take from at each step.

## Function Signature

```python
def solve(card_points: list[int], k: int) -> int:
    ...
```

## Input / Output

The harness reads from a file named `CASE0` written directly into the working directory (no stdin). The first line is a JSON header containing the fields `card_points` (list of ints) and `k` (int). You should parse it and write your answer to `CASE0.out` as a single integer followed by a newline.

Example `CASE0` file:

```
{"card_points": [1,2,3,4,5,6,1], "k": 3}
```

Expected `CASE0.out`:

```
12
```

## Notes

- `1 <= k <= n <= 10^5`; card values may be negative.
- Equivalent reformulation: among all contiguous subarrays of length `n - k`, find the one with the **minimum** sum; the answer is `total_sum - min_subarray_sum_of_length_n_minus_k`.
- A single sliding window over `card_points` runs in O(n) time and O(1) extra space.
