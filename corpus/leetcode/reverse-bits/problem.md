# Reverse Bits

## Problem

Given an unsigned 32-bit integer `n`, return its bits reversed. In other words, treat `n` as a 32-bit binary number (with `n` occupying the lower 32 bits and bits above 32 considered zero) and produce the integer whose 32-bit representation is `n` read from LSB to MSB.

### Function Signature

```elixir
def solve(n) :: integer
```

`n` is a non-negative integer that fits within 32 bits (i.e. `0 ≤ n < 2³²`). The result must also be non-negative and fit within 32 bits.

## Input / Output

The harness will read no input from stdin. Instead, multiple test cases are provided inline as a module attribute:

```elixir
CASE0 = {123456, 2069330688}  # 0x0001E240 → 0x7B561200
CASE1 = {0, 0}
CASE2 = {4294967295, 4294967295}  # 0xFFFFFFFF → 0xFFFFFFFF
CASE3 = {1, 2147483648}  # 0x00000001 → 0x80000000
CASE4 = {1431655765, 2863311530}  # 0x55555555 → 0xAAAAAAAA
```

`solve/1` is called for each tuple `{input, expected}` in the `CASE` list, and the harness checks that `solve(input) === expected`.

## Notes

- The reversal operates on exactly **32 bits**, so the bit at position `i` of `n` (0 ≤ i < 32) becomes the bit at position `31 - i` of the result.
- A simple shift-and-accumulate loop (`for i in 0..31` building `result = result << 1 | (n >>> i) & 1`) is sufficient.
- `n` is guaranteed non-negative, so plain `bsl`/`bsr` shifts work without sign-extension surprises.
- Edge cases to verify: `0` (all zeros stays all zeros), `2³² − 1` (all ones stays all ones), and values with bits concentrated at one end (e.g. `1`, `0x80000000`).
