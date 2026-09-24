# Edit Distance

Given two strings `a` and `b`, find the minimum number of single-character operations required to convert `a` into `b`. Allowed operations are:

- **Insert** a character
- **Delete** a character
- **Replace** one character with another

Each operation costs `1`.

## Input

Two lines, each containing a single string:

```
a
b
```

Both strings consist of lowercase letters `a`–`z` only. Lengths are between `0` and `5000`.

## Output

A single integer: the minimum number of operations needed to transform `a` into `b`.

## Function Signature

```clojure
(solve a b) ;; -> integer
```

## Examples

**Example 1**
```
Input:
kitten
sitting

Output:
3
```
Explanation: `kitten` → `sitten` (replace `k`→`s`) → `sittin` (delete `e`) → `sitting` (insert `g`).

**Example 2**
```
Input:
abc
abc

Output:
0
```

**Example 3**
```
Input:
""
a

Output:
1
```

## Notes

- The empty string is a valid input on either line.
- This is the classic **Levenshtein distance** problem; an `O(|a|·|b|)` dynamic programming solution is sufficient given the constraints.
- Pay attention to space: a row of length `|b|+1` is enough to compute the answer in `O(min(|a|, |b|))` space if desired.
