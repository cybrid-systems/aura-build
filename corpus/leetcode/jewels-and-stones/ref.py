import json
import sys

def solve(jewels: str, stones: str) -> int:
    jewel_set = set(jewels)
    return sum(1 for s in stones if s in jewel_set)

CASES = [
    {"jewels": "aA", "stones": "aAAbbbb"},
    {"jewels": "z", "stones": "ZZ"},
    {"jewels": "", "stones": "abc"},
    {"jewels": "abc", "stones": ""},
    {"jewels": "aAbBcC", "stones": "aabbccddeeff"},
    {"jewels": "abcdefghijklmnopqrstuvwxyz", "stones": "TheQuickBrownFoxJumpsOverTheLazyDog"},
    {"jewels": "abc", "stones": "aabbccabc"},
    {"jewels": "ZZ", "stones": "zZzZzZ"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["jewels"], case["stones"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
