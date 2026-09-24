from bisect import bisect_left
import json
import sys

def solve(s: str) -> int:
    if not s.strip():
        return 0
    nums = list(map(int, s.split()))
    tails = []
    for x in nums:
        idx = bisect_left(tails, x)
        if idx == len(tails):
            tails.append(x)
        else:
            tails[idx] = x
    return len(tails)

CASES = [
    {"s": "1 3 2 4 3 5"},
    {"s": "5 4 3 2 1"},
    {"s": ""},
    {"s": "1 2 3 4 5"},
    {"s": "5 4 3 2 1 6"},
    {"s": "2 2 2"},
    {"s": "0"},
    {"s": "3 1 4 1 5 9 2 6 5 3"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["s"])
        results.append({"id": i, "input": case, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
