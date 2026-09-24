import json
import sys
from typing import List

def solve(characters: str, words: List[str]) -> int:
    def freq(s):
        f = [0] * 26
        for c in s:
            f[ord(c) - ord('a')] += 1
        return f

    chars_freq = freq(characters)
    total = 0
    for w in words:
        wf = freq(w)
        if all(wf[i] <= chars_freq[i] for i in range(26)):
            total += len(w)
    return total


CASES = [
    {"characters": "welcometocoding", "words": ["welcome", "to", "coding", "leet", "code"]},
    {"characters": "abc", "words": ["a", "b", "c", "ab", "ac", "bc", "abc", "aab", "abcd"]},
    {"characters": "aaaa", "words": ["a", "aa", "aaa", "aaaa", "aaaaa"]},
    {"characters": "abcdefghijklmnopqrstuvwxyz", "words": ["abc", "xyz", "zyx", "abcd"]},
    {"characters": "a", "words": []},
    {"characters": "abcabc", "words": ["aabbcc", "abc", "abca", "aabb", "abcabc"]},
    {"characters": "zzz", "words": ["z", "zz", "zzz", "zzzz", "zzx"]},
    {"characters": "ilovepython", "words": ["i", "love", "python", "pyth", "py", "loves"]},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["characters"], case["words"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
