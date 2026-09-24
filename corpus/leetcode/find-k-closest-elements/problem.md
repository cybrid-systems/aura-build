# Find K Closest Elements

Given a **sorted** integer array `arr` and two integers `x` and `k`, return the `k` integers that are closest to `x` in `arr`. The result must be sorted in ascending order.

"Closest" is defined by absolute difference: an element `a` is closer to `x` than `b` if `|a - x| < |b - x|`. Ties are broken by the smaller value winning.

## Input Format

The first line contains three integers `n`, `k`, and `x`, where `n` is the array length.
The second line contains `n` sorted integers representing the array `arr`.

```
n k x
a0 a1 ... a(n-1)
```

## Output Format

Print the `k` closest elements to `x`, separated by spaces, in ascending order.

```
CASE0=ans0 ans1 ... ans(k-1)
```

Where `ans0 ans1 ... ans(k-1)` is the answer for the first (and only) test case.

## Constraints

- `1 <= k <= n <= 100000`
- The array `arr` is sorted in non-decreasing order.
- Values may be negative.

## Example

```
Input:
7 3 5
1 2 3 4 7 8 9

Output:
CASE0=3 4 7
```

## Notes

- Use binary search to find the leftmost index `i` such that the window `arr[i..i+k-1]` is the optimal answer. Valid range for `i` is `[0, n-k]`.
- Compare windows by the rightmost element: window `[left]` wins over `[left+1]` if `x - arr[left] <= arr[left+k] - x` (when both differences are non-negative, otherwise the side closer to `x` wins automatically).
- After binary search, simply slice `arr[i..i+k]` as the answer.
- Function signature: `(def solve (n k x arr) ...)` returning a list of `k` integers.
