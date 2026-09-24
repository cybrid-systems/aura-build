def solve(s):
    if not s or len(s) <= 1:
        return True
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            # Try skipping either left or right character
            return _is_palindrome_range(s, left + 1, right) or _is_palindrome_range(s, left, right - 1)
        left += 1
        right -= 1
    return True

def _is_palindrome_range(s, left, right):
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True

CASES = [
    {"s": "aba"},
    {"s": "abca"},
    {"s": "abc"},
    {"s": ""},
    {"s": "a"},
    {"s": "ab"},
    {"s": "abbaa"},
    {"s": "racecar"},
    {"s": "deeee"},
    {"s": "abcdcba"},
    {"s": "abcdba"},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["s"])
        results.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
