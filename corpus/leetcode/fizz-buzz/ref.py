def solve(n: int) -> list[str]:
    result = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append("FizzBuzz")
        elif i % 3 == 0:
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(i))
    return result


CASES = [
    {"n": 1},
    {"n": 3},
    {"n": 5},
    {"n": 15},
    {"n": 30},
    {"n": 0},
    {"n": 100},
    {"n": 7},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        n = case["n"]
        result = solve(n)
        expected = "\n".join(result)
        out.append({"id": idx, "input": {"n": n}, "expected": json.dumps(expected, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
