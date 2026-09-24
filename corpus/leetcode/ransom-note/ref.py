def solve(ransomNote: str, magazine: str) -> bool:
    if len(ransomNote) > len(magazine):
        return False
    counts = [0] * 26
    for ch in magazine:
        counts[ord(ch) - ord('a')] += 1
    for ch in ransomNote:
        idx = ord(ch) - ord('a')
        counts[idx] -= 1
        if counts[idx] < 0:
            return False
    return True


CASES = [
    {"ransomNote": "a", "magazine": "b"},
    {"ransomNote": "aa", "magazine": "ab"},
    {"ransomNote": "aa", "magazine": "aab"},
    {"ransomNote": "abc", "magazine": "aabbcc"},
    {"ransomNote": "abc", "magazine": "abcc"},
    {"ransomNote": "abcd", "magazine": "abc"},
    {"ransomNote": "", "magazine": "abc"},
    {"ransomNote": "aabbcc", "magazine": "abcabc"},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["ransomNote"], case["magazine"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
