# Pascal's Triangle

## Problem

Generate the first `numRows` of Pascal's triangle and return it as a list of rows, where each row is a list of its elements.

Pascal's triangle is constructed such that:
- The first row is `[1]`.
- Each subsequent row starts and ends with `1`.
- Every interior element is the sum of the two elements directly above it from the previous row.

For example, the first 5 rows are:
```
    1
   1 1
  1 2 1
 1 3 3 1
1 4 6 4 1
```

## Function Signature

```lisp
(defun solve (numrows)
  ;; returns list of rows
  )
```

## Input

The input is provided on a single line via the `CASE0` environment variable in the form:

```
CASE0=<numrows>
```

For example:
```
CASE0=5
```

`numrows` is a non-negative integer. The expected output is the corresponding number of rows.

## Output

Print each row of Pascal's triangle on its own line, with elements separated by a single space. Print nothing for `numrows = 0`.

## Notes

- `numRows` is guaranteed to be non-negative; no input validation is required.
- The rows grow in length by one element each step (row `i` has `i+1` elements for 0-indexed rows).
- Use integer arithmetic — all values fit comfortably in standard 64-bit integers for typical inputs.
