import json

INT_MIN = -2**31
INT_MAX = 2**31 - 1

def solve(s: str) -> int:
    n = len(s)
    i = 0
    # skip whitespace
    while i < n and s[i] == ' ':
        i += 1
    if i == n:
        return 0
    # sign
    sign = 1
    if s[i] == '+':
        i += 1
    elif s[i] == '-':
        sign = -1
        i += 1
    # read digits
    num = 0
    while i < n and s[i].isdigit():
        num = num * 10 + (ord(s[i]) - ord('0'))
        i += 1
    num *= sign
    if num < INT_MIN:
        return INT_MIN
    if num > INT_MAX:
        return INT_MAX
    return num

CASES = [
    {"s": "42"},
    {"s": "   -042"},
    {"s": "1337c0d3"},
    {"s": "0-1"},
    {"s": "words and 987"},
    {"s": "-91283472332"},
    {"s": "+1"},
    {"s": "   +0 123"},
    {"s": "2147483648"},
    {"s": "-2147483649"},
    {"s": ""},
    {"s": " "},
    {"s": "+"},
    {"s": "-"},
    {"s": "+-12"},
    {"s": "  +  123"},
    {"s": "00000-42a1234"},
    {"s": "  -000000000000001"},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, ensure_ascii=False))
