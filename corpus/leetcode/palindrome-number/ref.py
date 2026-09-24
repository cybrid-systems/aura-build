import json

def solve(x):
    # Negative numbers are not palindromes
    if x < 0:
        return False
    # Numbers ending in 0 (but not 0 itself) are not palindromes
    if x != 0 and x % 10 == 0:
        return False
    
    reversed_half = 0
    while x > reversed_half:
        reversed_half = reversed_half * 10 + x % 10
        x //= 10
    
    # For even digit numbers: x == reversed_half
    # For odd digit numbers: x == reversed_half // 10 (middle digit ignored)
    return x == reversed_half or x == reversed_half // 10


CASES = [
    {"x": 121},
    {"x": -121},
    {"x": 10},
    {"x": 0},
    {"x": 123},
    {"x": 1221},
    {"x": 12321},
    {"x": -2147483648},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        inp = case
        result = solve(case["x"])
        expected = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        results.append({"id": i, "input": inp, "expected": expected})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
