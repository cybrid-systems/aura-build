import json
import os

def solve(s: str) -> int:
    vowels = set('aeiouAEIOU')
    n = len(s)
    count = 0
    i = 0
    while i < n:
        if s[i] in vowels:
            j = i
            while j < n and s[j] in vowels:
                j += 1
            length = j - i
            if length >= 2:
                count += length * (length - 1) // 2
            i = j
        else:
            i += 1
    return count

CASES = [
    {"s": "aeiou"},
    {"s": "abc"},
    {"s": "aab"},
    {"s": "a"},
    {"s": "aa"},
    {"s": "AaAa"},
    {"s": "bcd"},
    {"s": "aeiaaiooau"},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        s = case["s"]
        result = solve(s)
        results.append({
            "id": idx,
            "input": {"s": s},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
