import sys
import json


def solve(s: str, k: int) -> int:
    if k <= 0 or len(s) < k:
        return 0
    vowels = set('aeiou')
    count = sum(1 for c in s[:k] if c in vowels)
    best = count
    for i in range(k, len(s)):
        if s[i] in vowels:
            count += 1
        if s[i - k] in vowels:
            count -= 1
        if count > best:
            best = count
    return best


CASES = [
    {"s": "abciiidef", "k": 3},
    {"s": "aeiou", "k": 2},
    {"s": "bcdfg", "k": 3},
    {"s": "a", "k": 1},
    {"s": "a", "k": 2},
    {"s": "aaaaa", "k": 3},
    {"s": "abcdefghijklmnopqrstuvwxyz", "k": 5},
    {"s": "leetcode", "k": 0},
]


if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        result = solve(case["s"], case["k"])
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
