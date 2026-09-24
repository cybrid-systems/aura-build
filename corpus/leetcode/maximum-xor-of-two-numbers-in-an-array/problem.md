# Maximum XOR of Two Numbers in an Array

Given an array of non-negative integers `nums`, find the **maximum XOR** value obtainable by picking any two distinct numbers from the array. If the array has fewer than two numbers, return `0`.

## Function Signature

```clojure
(solve nums)
```

- `nums` — a vector of non-negative integers (`0 ≤ nums[i] ≤ 10^9`).
- Returns the maximum XOR of any pair `(i, j)` with `i ≠ j`, or `0` if fewer than two elements exist.

## I/O Convention (CASE0)

```
CASE0_input=4 1 2 3
CASE0_output=3
```

- **Input line**: the array `nums` as space-separated integers on a single line.
- **Output line**: a single integer — the maximum XOR of any two numbers in `nums`.

### Examples

| Input              | Output | Explanation                                          |
|--------------------|--------|------------------------------------------------------|
| `4 1 2 3`          | `3`    | `1 ^ 2 = 3` is the largest among all pairs.          |
| `8 10 2`           | `10`   | `8 ^ 2 = 10`.                                         |
| `0 0`              | `0`    | Any pair gives `0 ^ 0 = 0`.                          |
| `5`                | `0`    | Only one element → no pair exists, return `0`.        |

## Notes

- The "bitwise trie" approach inserts each number's binary representation (from the most significant bit down) into a binary trie, then for each number greedily traverses the trie favoring the **opposite** bit to maximize the resulting XOR.
- Time complexity: `O(n · b)` where `b` is the bit length (≤ 31 for the given bounds), and space complexity is `O(n · b)`.
- Assume `n` can be up to roughly `2·10^4`; a single-pass building of the trie and a single-pass query suffices.
