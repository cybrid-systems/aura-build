# Expression Add Operators

## Problem

Given a string `num` consisting only of digits and an integer `target`, insert one of the binary operators `+`, `-`, or `*` between any two consecutive digits (and optionally group digits into multi-digit numbers) so that the resulting expression evaluates exactly to `target`.

Return all valid expressions as a list of strings. The operands must be formed from the digits in their original order, without leading zeros unless the operand is the single digit `"0"`.

## Function Signature

```python
def solve(num: str, target: int) -> list[str]:
    ...
```

## Input / Output Convention (Aura harness, stdin-less)

The harness invokes `solve(num, target)` directly. The example block below uses the `CASE0=...` lines only for human reference and is **not** parsed as I/O.

```
CASE0=
num = "123"
target = 6
output = ["1+2+3", "1*2*3"]
```

```
CASE1=
num = "232"
target = 8
output = ["2*3+2", "2+3*2"]
```

```
CASE2=
num = "105"
target = 5
output = ["1*0+5", "10-5"]
```

```
CASE3=
num = "00"
target = 0
output = ["0+0", "0-0", "0*0"]
```

```
CASE4=
num = "3456237490"
target = 9191
output = []
```

## Notes

- `1 <= len(num) <= 10` in the reference tests; the recursive exploration must still avoid exponential blow-up on longer inputs.
- Operators have standard precedence only between `*` and `+/-` (i.e., `*` binds tighter); evaluation should still produce `target` regardless of grouping as long as standard left-to-right rules hold. Implement evaluation by tracking the running total together with the last multiplied term so that `*` does not force a full reparse on each step.
- Remember to skip operands with a leading zero: if you start a number with `'0'` and it is not the single digit `0`, do not extend it further.
- Order of the returned list does not matter, but duplicates must not appear.
