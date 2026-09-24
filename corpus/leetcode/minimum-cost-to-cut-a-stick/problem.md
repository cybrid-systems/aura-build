# Minimum Cost to Cut a Stick

## Problem

You have a wooden stick of length **L** (the stick extends from position `0` to position `L`). Along the stick there are `n` marked cut positions (distinct integer positions strictly between `0` and `L`) at which you must eventually separate the stick into pieces.

Cutting works as follows: at any moment, you have a collection of stick pieces. Choosing one piece of length `x` and cutting it at a marked position inside that piece incurs a cost equal to `x` (the current length of the piece you are cutting). The two resulting pieces then become independent and can each be cut further.

Your task is to choose the order of cuts so that the **total cost** is minimized, and report that minimum total cost.

## Function Signature

```python
def solve(L: int, cuts: list[int]) -> int:
    ...
```

## Input / Output Convention (CASE0 format)

The harness reads/writes one case. The input line `CASE0=` is followed by two lines:

```
CASE0=
<L>
<c1> <c2> ... <cn>
```

- `L` — the length of the stick (integer).
- The second line lists the `n` cut positions as space-separated integers.

The program must write a single line `ANS=<answer>` where `<answer>` is the minimum total cutting cost as an integer.

**Example:**

```
CASE0=
7
1 3 5
```

Expected output:

```
ANS=16
```

## Notes

- A classic greedy solution sorts the cut positions and always picks the cut with the smallest current piece length (ties may be broken arbitrarily). After cutting at that position, the piece is split and the two new sub-piece lengths are inserted back into the priority of candidate pieces.
- Equivalently, this can be modeled with a min-heap initialized with the lengths of the segments created by the sorted cuts, repeatedly extracting the smallest length, adding it to the answer, and replacing it with its two halves — yielding the same minimum cost.
- The number of cuts `n` and positions fit comfortably within standard integer ranges; the answer fits in 64-bit.
