import sys
import json

def solve(haystack: str, needle: str) -> int:
    if needle == "":
        return 0
    n, m = len(haystack), len(needle)
    for i in range(n - m + 1):
        if haystack[i:i+m] == needle:
            return i
    return -1

CASES = [
    {"haystack": "hello", "needle": "ll"},
    {"haystack": "aaaaa", "needle": "bba"},
    {"haystack": "abc", "needle": "a"},
    {"haystack": "", "needle": ""},
    {"haystack": "abc", "needle": ""},
    {"haystack": "abc", "needle": "abcd"},
    {"haystack": "mississippi", "needle": "issip"},
    {"haystack": "a", "needle": "a"},
]

if __name__ == '__main__':
    results = []
    for case in CASES:
        result = solve(**case)
        results.append({
            "id": len(results),
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, ensure_ascii=False))
