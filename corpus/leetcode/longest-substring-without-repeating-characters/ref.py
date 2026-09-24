import json
import sys

def solve(s: str) -> int:
    last_seen = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        if ch in last_seen and last_seen[ch] >= left:
            left = last_seen[ch] + 1
        last_seen[ch] = right
        best = max(best, right - left + 1)
    return best

CASES = [
    {"s": "abcabcbb"},
    {"s": "bbbbb"},
    {"s": "pwwkew"},
    {"s": ""},
    {"s": "a"},
    {"s": "au"},
    {"s": "dvdf"},
    {"s": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    sys.stdout.write(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
