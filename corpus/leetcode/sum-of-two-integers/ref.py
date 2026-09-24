def solve(a: int, b: int) -> int:
    # 32-bit mask
    MASK = 0xFFFFFFFF
    MAX_INT = 0x7FFFFFFF

    # work with values masked to 32 bits
    x = a & MASK
    y = b & MASK

    while y != 0:
        # sum without carry (XOR), carry shifted left
        carry = ((x & y) << 1) & MASK
        x = (x ^ y) & MASK
        y = carry

    # convert back to signed 32-bit
    if x > MAX_INT:
        x = ~(x ^ MASK)
    return x


CASES = [
    {"a": 2, "b": 3},
    {"a": -1, "b": 1},
    {"a": 0, "b": 0},
    {"a": -12, "b": -8},
    {"a": 100, "b": -200},
    {"a": 2147483647, "b": 0},
    {"a": -2147483648, "b": -1},
    {"a": 123456789, "b": -987654321},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
