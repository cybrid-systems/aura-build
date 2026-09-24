def solve(n: int) -> str:
    pairs = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = []
    for value, symbol in pairs:
        while n >= value:
            result.append(symbol)
            n -= value
    return "".join(result)

CASES = [
    {"n": 58},
    {"n": 1994},
    {"n": 9},
    {"n": 3999},
    {"n": 4},
    {"n": 40},
    {"n": 90},
    {"n": 400},
    {"n": 900},
    {"n": 1},
    {"n": 3888},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
