import sys
import json

def solve(s: str) -> list[int]:
    last = {}
    for i, ch in enumerate(s):
        last[ch] = i
    result = []
    start = 0
    end = 0
    for i, ch in enumerate(s):
        end = max(end, last[ch])
        if i == end:
            result.append(end - start + 1)
            start = end + 1
    return result

CASES = [
    {"s": "ababcbacadefegdehijhklij"},
    {"s": "caedbdedda"},
    {"s": "a"},
    {"s": "aa"},
    {"s": "ab"},
    {"s": "abcabc"},
    {"s": "abcd"},
    {"s": "eccbbbbdec"},
]

if __name__ == '__main__':
    output = []
    for idx, case in enumerate(CASES):
        result = solve(**case)
        output.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
