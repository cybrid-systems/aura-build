def solve(s: str) -> int:
    values = {
        'I': 1,
        'V': 5,
        'X': 10,
        'L': 50,
        'C': 100,
        'D': 500,
        'M': 1000,
    }
    total = 0
    n = len(s)
    for i, ch in enumerate(s):
        v = values[ch]
        if i + 1 < n and v < values[s[i + 1]]:
            total -= v
        else:
            total += v
    return total


CASES = [
    {"s": "III"},
    {"s": "LVIII"},
    {"s": "MCMXCIV"},
    {"s": "IV"},
    {"s": "IX"},
    {"s": "XL"},
    {"s": "XC"},
    {"s": "CD"},
    {"s": "CM"},
    {"s": "MMMDCCCLXXXVIII"},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, kwargs in enumerate(CASES):
        result = solve(**kwargs)
        out.append({
            "id": idx,
            "input": {k: v for k, v in kwargs.items()},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
