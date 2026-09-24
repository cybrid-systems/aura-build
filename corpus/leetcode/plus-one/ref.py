import sys
import json

def solve(digits):
    d = list(digits)
    n = len(d)
    carry = 1
    for i in range(n - 1, -1, -1):
        s = d[i] + carry
        d[i] = s % 10
        carry = s // 10
        if carry == 0:
            break
    if carry:
        d.insert(0, 1)
    return d

CASES = [
    {"digits": [1, 2, 3]},
    {"digits": [4, 3, 2, 1]},
    {"digits": [9]},
    {"digits": [9, 9, 9, 9]},
    {"digits": [0]},
    {"digits": [1, 0, 0, 0]},
    {"digits": [8, 9, 9, 9]},
    {"digits": [2, 0, 0, 0, 0]},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        digits = case["digits"]
        result = solve(digits)
        out.append({
            "id": i,
            "input": {"digits": digits},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
