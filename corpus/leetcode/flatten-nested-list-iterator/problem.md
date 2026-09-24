# Flatten Nested List Iterator

## Problem

You are given a **NestedInteger** structure that represents either a single integer or a list of `NestedInteger` elements (which themselves may be integers or nested lists). Your task is to implement an iterator that **flattens** this nested structure and returns the integers inside in left-to-right order, one per call to `next()`.

The iterator must support two operations:

- `next()` — returns the next integer in the flattened sequence.
- `hasNext()` — returns `true` if there is at least one integer remaining to be yielded, `false` otherwise.

The constructor receives the nested list as its input. After construction, `hasNext()` and `next()` may be interleaved in any pattern. Both operations should be efficient — `hasNext()` in **O(1)** amortized time per element overall, with **O(d)** auxiliary memory where *d* is the maximum nesting depth of the input.

## Input Specification

The input is provided as a single line on stdin in the form:

```
CASE0=<serialized nested list>
```

where the serialized nested list uses the following grammar:

- An integer is written as a decimal literal (e.g., `42`, `-7`, `0`).
- A nested list is written as a comma-separated sequence of zero or more elements enclosed in square brackets (e.g., `[1,2,3]`, `[[1,2],[3,[4]]]`, `[]`).

For example:

```
CASE0=[[1,1],2,[1,1]]
```

or

```
CASE0=[]
```

Your iterator must consume this serialized representation and produce the flat sequence by repeatedly calling `hasNext()` and `next()`.

## Output Specification

For each integer produced by the iterator, print it on its own line, in the exact order it would be yielded. After `hasNext()` returns `false`, output a final line containing the single word `END`.

For the example `CASE0=[[1,1],2,[1,1]]`, the output is:

```
1
1
2
1
1
END
```

## Function Signature

Implement the standard harness entry point:

```scheme
(define (solve) ...)
```

The `solve` function should read the `CASE0=...` line from stdin, parse the nested list, construct the iterator, then drive the iterator with repeated `hasNext` / `next` calls, printing each value followed by `END` on the final line.

## Notes

- An empty top-level list is valid; the only output should be `END`.
- The serialization is guaranteed to be well-formed.
- Integer values fit within a standard 32-bit signed range.
- Focus on lazy iteration — do not eagerly flatten the entire structure into a list before traversal begins.
