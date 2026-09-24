# Kth Largest Element in an Array

Given an unsorted array of integers, find the **k-th largest element** in the array.

Note that it is the k-th largest element in the sorted order, not the k-th distinct element. You may assume `k` is always valid: `1 ≤ k ≤ n` where `n` is the length of the array.

## Function Signature

```lisp
(defun solve (nums k)
  ;; returns the k-th largest element of nums
  )
```

## Input / Output Convention

Input is provided via a `CASE0` source form on a single line, followed by the function call. Parse the array and integer from this form.

For example, given the input line:

```
CASE0=((3 2 1 5 6 4) 2)
```

Your implementation should interpret `nums = [3, 2, 1, 5, 6, 4]` and `k = 2`, and return the result `5` (the 2nd largest element is 5, since the sorted array is `[1, 2, 3, 4, 5, 6]`).

Output the answer as a single integer printed to stdout.

## Examples

| Input (`CASE0`)              | k | Sorted Array         | Output |
|------------------------------|---|----------------------|--------|
| `((3 2 1 5 6 4) 2)`          | 2 | `[1, 2, 3, 4, 5, 6]`  | `5`    |
| `((3 2 3 1 2 4 5 5 6) 4)`    | 4 | `[1, 2, 2, 3, 3, 4, 5, 5, 6]` | `4` |
| `((1) 1)`                    | 1 | `[1]`                | `1`    |

## Notes

- The array may contain duplicates; count duplicates as separate entries when sorting.
- Aim for better than O(n log n) if possible — selection algorithms (e.g., quickselect) achieve expected O(n) time.
- Constraints: `-10^4 ≤ nums[i] ≤ 10^4`, array length up to `10^5`.
