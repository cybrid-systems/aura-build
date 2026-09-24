def monotoneIncreasingDigits(N: int) -> int:
    if N < 10:
        return N
    digits = list(str(N))
    n = len(digits)
    mark = n
    for i in range(n - 1, 0, -1):
        if digits[i] < digits[i - 1]:
            digits[i - 1] = str(int(digits[i - 1]) - 1)
            mark = i
    for i in range(mark, n):
        digits[i] = '9'
    return int(''.join(digits))


def solve(N: int) -> int:
    return monotoneIncreasingDigits(N)


CASES = [
    {"N": 332},
    {"N": 100},
    {"N": 0},
    {"N": 10},
    {"N": 9},
    {"N": 1234},
    {"N": 332111},
    {"N": 111111},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
