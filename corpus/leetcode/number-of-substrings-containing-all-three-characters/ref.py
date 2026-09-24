import sys
import json

def solve(s: str) -> int:
    n = len(s)
    count = [0, 0, 0]
    left = 0
    result = 0
    for right in range(n):
        idx = ord(s[right]) - ord('a')
        if 0 <= idx < 3:
            count[idx] += 1
        # Shrink window from left while all three chars are present
        while count[0] > 0 and count[1] > 0 and count[2] > 0 and left <= right:
            idx_l = ord(s[left]) - ord('a')
            if 0 <= idx_l < 3:
                count[idx_l] -= 1
            left += 1
        # Now the smallest left such that window [left, right] has all three is (left - 1)
        # All windows starting at k where 0 <= k < left and ending at right are valid
        result += left
    return result

CASES = [
    {"s": "abc"},
    {"s": "aaab"},
    {"s": "aababc"},
    {"s": "abcabc"},
    {"s": "a"},
    {"s": "abca"},
    {"s": "abcabcabc"},
    {"s": "aaabbbccc"},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["s"])
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
