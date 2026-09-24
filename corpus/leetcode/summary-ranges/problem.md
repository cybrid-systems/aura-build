# Summary Ranges

## Problem

You are given a sorted list of **distinct** integers `nums`.  
Your task is to summarize the consecutive integer sequences in `nums` as ranges.

A range is described in one of two forms:
- `a->b` when the sequence contains at least two integers, where `a` is the first and `b` is the last value in that consecutive run.
- `a` when the run contains exactly one integer.

Two integers are considered consecutive if they differ by exactly 1.

Return the list of range strings in the same order the sequences appear in `nums`.

## Function Signature

```lisp
(defun solve (nums)
  ;; returns a list of strings
  )
```

## Input

The input is provided as a single case on standard input, formatted as:

```
CASE0=1 3 4 5 7 8
```

Where the line `CASE0=` is followed by a single space and then the elements of the sorted integer array (distinct, may be negative, may be empty). There will always be at least one case (though `nums` itself may be empty).

The harness will strip the `CASE0=` prefix and the optional trailing newline, then pass the remainder as a space-separated list of integers to `solve`.

## Output

Print each range string on its own line, in the order the consecutive runs appear. The special tokens `CASE0=` and `RESULT_n=` are NOT used here — this problem writes its plain result directly to stdout, one range per line.

## Example

Input:
```
CASE0=0 1 2 4 5 7
```
Output:
```
0->2
4->5
7
```

## Notes

- The integer `-1` is considered consecutive with `0` and with `-2`.
- If `nums` is empty, print nothing (no output at all).
- Each range is separated by a newline; the last line should end with a newline.
- Use small integers only — no overflow concerns within typical 32-bit signed range.
