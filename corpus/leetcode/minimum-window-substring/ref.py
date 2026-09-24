import sys
import json
from collections import Counter

def min_window(s, t):
    if not t or not s:
        return ""
    need = Counter(t)
    missing = len(t)
    left = 0
    best = ""
    best_len = float('inf')
    window = Counter()
    for right, ch in enumerate(s):
        if ch in need:
            if window[ch] < need[ch]:
                missing -= 1
            window[ch] += 1
        while missing == 0:
            cur_len = right - left + 1
            if cur_len < best_len:
                best_len = cur_len
                best = s[left:right+1]
            ch_left = s[left]
            left += 1
            if ch_left in need:
                window[ch_left] -= 1
                if window[ch_left] < need[ch_left]:
                    missing += 1
    return best

def solve(s, t):
    return min_window(s, t)

CASES = [
    {"s": "ADOBECODEBANC", "t": "ABC"},
    {"s": "a", "t": "a"},
    {"s": "a", "t": "aa"},
    {"s": "aa", "t": "aa"},
    {"s": "ab", "t": "b"},
    {"s": "bba", "t": "ab"},
    {"s": "cabwefgewcwaefklwjefw", "t": "vjj"},
    {"s": "", "t": "a"},
    {"s": "abc", "t": ""},
    {"s": "ADOBECODEBANC", "t": "ABBC"},
    {"s": "aaflslflsldkaflslf", "t": "afsl"},
    {"s": "aaaaaaaa", "t": "aaa"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        inp = {"s": case["s"], "t": case["t"]}
        expected = solve(case["s"], case["t"])
        results.append({"id": i, "input": inp, "expected": expected})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
