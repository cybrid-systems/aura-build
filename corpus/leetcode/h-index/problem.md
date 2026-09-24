# H-Index

## Problem

A researcher's h-index is defined as the maximum integer `h` such that the researcher has at least `h` papers with **at least** `h` citations each.

Given an array of citation counts for a researcher's papers, compute their h-index.

## Function Signature

```lisp
(defun solve (citations)
  ;; returns the h-index
  )
```

## Input Format

The input is read from standard input as a single test case of the following form:

```
CASE0=<n>
<array of n integers, space-separated>
```

For example:

```
CASE0=5
3 0 6 1 5
```

- Line 1: `CASE0=` followed by `n`, the number of papers.
- Line 2: `n` non-negative integers — the citation count for each paper.

## Output Format

Print a single integer — the researcher's h-index.

## Example

**Input**
```
CASE0=5
3 0 6 1 5
```

**Output**
```
3
```

**Explanation**: The researcher has 3 papers with at least 3 citations (the papers with 6, 5, and 3 citations). It is not possible to have `h = 4` because only 2 papers have at least 4 citations.

## Notes

- `n` can be up to `10^5`, and each citation count can be up to `10^5` (or larger in edge variants); favor an `O(n log n)` or `O(n)` solution over the naive `O(n^2)`.
- A paper with 0 citations cannot contribute to any positive h-index value.
