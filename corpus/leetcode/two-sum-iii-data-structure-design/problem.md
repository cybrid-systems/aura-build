# Two Sum III – Data structure design

Design a data structure that supports the following two operations:

- `add(number)` – add a number to the data structure.
- `find(value)` – return `true` if there exists **any** pair of numbers in the structure whose sum equals `value`, otherwise return `false`.

The same number may be added multiple times and may be paired with itself (i.e. two copies of the same added value count as a valid pair, provided it was added at least twice).

## Function signature

```lisp
(defun solve (opcodes-and-args) ...)
```

`opcodes-and-args` is a list of operations to perform in order. Each operation is one of:

- `(:add n)` — store the integer `n`.
- `(:find v)` — return `true` or `false` depending on whether some pair sums to `v`.

The function should return a list containing the result of every `:find` operation, in the order they were issued.

## Input / Output convention (Aura / stdin-less)

The harness describes a single test case as `CASE0=...` lines on standard input, where each line is one operation:

```
CASE0=
:add 1
:add 3
:add 5
:find 4
:find 7
```

The expected stdout is one line per `:find`, in order:

```
true
false
```

If a case has no `:find` operations, output nothing for that case.

## Examples

```
CASE0=
:add 1
:add 3
:add 5
:find 4
:find 7
CASE1=
:add 0
:add 0
:find 0
```
→
```
true
false
true
```

## Notes

- You may assume that all input integers fit comfortably in a standard signed integer range.
- Aim for amortized performance that is clearly better than the naïve `O(n)` per `find` over all stored elements. A hash-map of counts (`O(1)` `add`, expected `O(n)` `find`) is the typical target.
- The order of operations matters: only numbers that have been `:add`-ed **before** a `:find` may be used to satisfy it.
