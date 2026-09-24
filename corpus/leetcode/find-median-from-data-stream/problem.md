# Find Median from Data Stream

## Problem

Design a data structure that efficiently supports the following operations on a stream of integers:

- **Add a number** to the data structure.
- **Find the median** of all numbers added so far.

The median of a finite list of numbers is:
- The middle element when the count is odd.
- The average of the two middle elements when the count is even.

Your implementation must support adding a number and querying the median in **O(log n)** time per operation, where *n* is the number of elements stored.

## Function Signature

```text
solve
```

- `add(num)`: insert `num` into the structure (return value is not used).
- `median()`: return the current median as a number.

(Exact method names may be `add`/`median` or exposed via a small driver; the harness handles the I/O described below.)

## Input / Output Convention

The harness reads commands from standard input and prints results to standard output.

For each test case, the input has the following form:

```
CASE0=<count>
<count> lines, each one of:
  ADD <integer>
  MEDIAN
```

For every `MEDIAN` command, print the current median on its own line, formatted with sufficient precision (an absolute or relative error of at most 1e-5 is acceptable).

### Example

```
CASE0=6
ADD 1
MEDIAN
ADD 2
MEDIAN
ADD 3
MEDIAN
```

Expected output (one number per line):

```
1
1.5
2
```

## Notes

- Numbers can be negative, and `ADD` values may be given in any order; the structure must handle them correctly.
- A standard approach is to maintain two heaps: a **max-heap** for the lower half and a **min-heap** for the upper half, keeping their sizes balanced to within one element. The median is then always at the top of one heap (or the average of both tops).
