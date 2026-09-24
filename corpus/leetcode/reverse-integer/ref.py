import json

def solve(x: int) -> int:
    INT_MIN, INT_MAX = -2**31, 2**31 - 1
    sign = -1 if x < 0 else 1
    x = abs(x)
    rev = 0
    while x > 0:
        digit = x % 10
        x //= 10
        # Check overflow before multiplying and adding
        if rev > (INT_MAX - digit) // 10:
            return 0
        rev = rev * 10 + digit
    rev *= sign
    if rev < INT_MIN or rev > INT_MAX:
        return 0
    return rev


CASES = [
    {"x": -123},
    {"x": 1534236469},
    {"x": -2147483412},
    {"x": 0},
    {"x": 120},
    {"x": 1},
    {"x": -1},
    {"x": 2**31 - 1},
    {"x": -2**31},
    {"x": 2147483647},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
