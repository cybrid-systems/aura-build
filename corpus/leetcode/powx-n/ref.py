import json

def solve(x: float, n: int) -> float:
    # Handle special case x == 0
    if x == 0.0:
        if n == 0:
            return 1.0
        # 0^negative is undefined, but we'll return inf-like behavior
        return 0.0
    
    # For n == 0, result is 1
    if n == 0:
        return 1.0
    
    # Work with positive exponent using Python's arbitrary precision int
    exp = n
    result = 1.0
    base = x
    
    if exp < 0:
        base = 1.0 / base
        exp = -exp
    
    # Iterative binary exponentiation
    while exp > 0:
        if exp & 1:
            result *= base
        base *= base
        exp >>= 1
    
    return result


CASES = [
    {"x": 2.0, "n": 10},
    {"x": 2.1, "n": 3},
    {"x": 2.0, "n": -2},
    {"x": 1.0, "n": 0},
    {"x": 0.0, "n": 0},
    {"x": 0.0, "n": 5},
    {"x": -2.0, "n": 3},
    {"x": -2.0, "n": 4},
    {"x": 2.0, "n": -2147483648},
    {"x": 1.5, "n": 20},
    {"x": 0.5, "n": -3},
    {"x": 1.0, "n": 2147483647},
]


if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["x"], case["n"])
        out.append({
            "id": i,
            "input": {"x": case["x"], "n": case["n"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
