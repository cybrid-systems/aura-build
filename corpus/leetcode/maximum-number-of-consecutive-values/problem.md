# Maximum Number of Consecutive Values

## Problem

You are given a sequence of `N` integers `a[1], a[2], ..., a[N]`. From this sequence, select a subset of values such that **no two selected values are consecutive in the original sequence**. Your goal is to select as many values as possible.

Formally, find the maximum size of a subset `S ⊆ {1, 2, ..., N}` such that for any `i, j ∈ S` with `i < j`, we have `j > i + 1`.

Output only the size of this maximum subset.

## Input

The input is provided via the Aura harness as `CASE0` lines. Each case contains:

```
CASE0=N
CASE0=a_1 a_2 ... a_N
```

- `N` — the length of the sequence (integer, `1 ≤ N ≤ 1000`).
- `a_i` — the integer values of the sequence (`-10^9 ≤ a_i ≤ 10^9`). The values themselves are not used for comparison; only their **positions** matter.

Read until a case with `N = 0` is encountered, which terminates the input.

## Output

For each case, print a single line containing the maximum number of non-consecutive values that can be selected.

## Function Signature (hint)

```scheme
(define (solve N a) -> integer)
```

Where:

- `N` is the number of elements.
- `a` is a list (vector) of `N` integers.
- Returns the maximum count of selectable elements with no two adjacent in position.

## Example

For the input:

```
CASE0=5
CASE0=10 20 30 40 50
CASE0=4
CASE0=1 2 3 4
CASE0=0
```

The outputs are:

```
3
2
```

**Explanation:**

- Case 1: There are 5 elements. Choose positions `{1, 3, 5}` → values `10, 30, 50` → size **3**.
- Case 2: There are 4 elements. Choose positions `{1, 3}` or `{2, 4}` → size **2**.

## Notes

- The actual numeric values of `a_i` are irrelevant; only the sequence length and positions determine the answer.
- The optimal answer for any sequence of length `N` follows the pattern: `⌈N / 2⌉`. However, write your solution generally in case the rule is generalized in future variants.
- A simple greedy works: scan from left to right, and whenever the current position is not adjacent to the last chosen position, pick it.
