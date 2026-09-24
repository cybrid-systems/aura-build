# Next Permutation

## Statement

Given a sequence of integers, rearrange its elements **in-place** to obtain the lexicographically next greater permutation. If the sequence is already the highest possible permutation (i.e., sorted in strictly descending order), rearrange it into the lowest possible permutation (i.e., sorted in strictly ascending order).

The rearrangement must be performed **in-place** on the input array, meaning no additional array of size proportional to the input may be allocated. Constant extra space is allowed.

## Function Signature

```clojure
(solve n arr)
```

- `n` — an integer, the number of elements.
- `arr` — a vector of `n` integers.

The function should mutate `arr` in-place and return the resulting vector (or sequence) representing the next lexicographic permutation.

## Input Convention

The harness feeds **no stdin**. Instead, each test case is expressed as a set of `CASE` constants in the source. Each `CASE0`, `CASE1`, ... declares the inputs in order:

```
CASE0 = 3
CASE0_ARR = [1 2 3]
CASE0_EXPECTED = [1 3 2]

CASE1 = 3
CASE1_ARR = [3 2 1]
CASE1_EXPECTED = [1 2 3]

CASE2 = 4
CASE2_ARR = [1 1 5]
CASE2_EXPECTED = [1 5 1]
```

The solver is invoked once per case as `(solve N ARR)`, and the returned value is compared against `EXPECTED`.

## Examples

| Input `arr`      | Output `arr`     |
|------------------|------------------|
| `[1 2 3]`        | `[1 3 2]`        |
| `[3 2 1]`        | `[1 2 3]`        |
| `[1 1 5]`        | `[1 5 1]`        |
| `[1 3 2 4]`      | `[1 3 4 2]`      |

## Notes

- The array may contain duplicate values; the algorithm must handle them correctly.
- The transformation must be done **in-place**; using an auxiliary array sized by `n` is not permitted.
