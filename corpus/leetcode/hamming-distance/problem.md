# Hamming Distance

## Statement

The Hamming distance between two integers is the number of bit positions at which the corresponding bits are different. Given two non-negative integers `x` and `y`, compute the Hamming distance between them.

In other words, count the number of `1`s in the binary representation of `x XOR y`.

## Input / Output Convention

Input is provided as a series of cases on standard input. The first line contains an integer `T` (the number of test cases). Each subsequent line contains two non-negative integers `x` and `y` separated by a space.

You should read every case, and for each one output the Hamming distance between `x` and `y`, one per line.

```
CASE0=
1 4
3 1
0 0
7 8
```

Expected output for `CASE0`:

```
1
1
0
4
```

## Function Signature

```clojure
(defn solve []
  ;; read from *in*, write to *out*
  )
```

## Notes

- The integers fit comfortably in a standard 32-bit unsigned range (`0 <= x, y < 2^32`).
- A clean trick is to observe that `popcount(x XOR y)` equals the Hamming distance directly, but any correct bit-by-bit comparison is also acceptable.
- Mind the `0 0` edge case: the Hamming distance between two equal numbers is always `0`.
