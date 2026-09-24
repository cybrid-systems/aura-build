def solve(n: int) -> bool:
    """Return True iff n is a positive integer whose prime factors are limited to 2, 3, and 5."""
    if not isinstance(n, int) or n <= 0:
        return False
    for p in (2, 3, 5):
        while n % p == 0:
            n //= p
    return n == 1


CASES = [
    {"n": 1},       # 1 -> true
    {"n": 6},       # 2*3 -> true
    {"n": 14},      # 2*7 -> false
    {"n": 0},       # not positive -> false
    {"n": -6},      # not positive -> false
    {"n": 25},      # 5*5 -> true
    {"n": 27},      # 3^3 -> true
    {"n": 30},      # 2*3*5 -> true
    {"n": 7},       # prime 7 -> false
    {"n": 1000000}, # 10^6 = 2^6 * 5^6 -> true
    {"n": 999983},  # large prime -> false
    {"n": 2},       # prime 2 -> true
    {"n": 3},       # prime 3 -> true
    {"n": 5},       # prime 5 -> true
    {"n": 13},      # prime 13 -> false
]


if __name__ == "__main__":
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(",", ":"), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
