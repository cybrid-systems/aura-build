import sys
import json
from collections import Counter

def solve(s: str) -> int:
    counts = Counter(s)
    length = 0
    odd_found = False
    for c in counts.values():
        if c % 2 == 0:
            length += c
        else:
            length += c - 1
            odd_found = True
    if odd_found:
        length += 1
    return length

CASES = [
    {"id": 0, "input": {"s": "abccccdd"}},
    {"id": 1, "input": {"s": "a"}},
    {"id": 2, "input": {"s": ""}},
    {"id": 3, "input": {"s": "aa"}},
    {"id": 4, "input": {"s": "abc"}},
    {"id": 5, "input": {"s": "AaBb"}},
    {"id": 6, "input": {"s": "aabbcc"}},
    {"id": 7, "input": {"s": "aAaaA"}},
]

if __name__ == '__main__':
    results = []
    for case in CASES:
        s = case["input"]["s"]
        result = solve(s)
        results.append({
            "id": case["id"],
            "input": case["input"],
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
