import json

def longest_palindromic_substring(s: str) -> str:
    n = len(s)
    if n <= 1:
        return s
    best_start, best_len = 0, 1
    def expand(left: int, right: int) -> tuple[int, int]:
        while left >= 0 and right < n and s[left] == s[right]:
            left -= 1
            right += 1
        return left + 1, right - left - 1
    for i in range(n):
        l1, len1 = expand(i, i)
        if len1 > best_len:
            best_start, best_len = l1, len1
        l2, len2 = expand(i, i + 1)
        if len2 > best_len:
            best_start, best_len = l2, len2
    return s[best_start:best_start + best_len]

def solve(s: str) -> str:
    return longest_palindromic_substring(s)

CASES = [
    {"s": "babad"},
    {"s": "cbbd"},
    {"s": "a"},
    {"s": ""},
    {"s": "racecar"},
    {"s": "abacdfgdcaba"},
    {"s": "aaaa"},
    {"s": "abcde"},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        out = solve(case["s"])
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
