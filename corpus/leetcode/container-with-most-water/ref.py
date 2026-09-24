import sys
import json
import re

def solve(heights):
    """Two-pointer approach to find max water container area."""
    if len(heights) < 2:
        return 0
    left, right = 0, len(heights) - 1
    best = 0
    while left < right:
        w = right - left
        h = min(heights[left], heights[right])
        area = w * h
        if area > best:
            best = area
        if heights[left] < heights[right]:
            left += 1
        else:
            right -= 1
    return best


def parse_vector(s):
    """Parse a Clojure vector literal like '[1 8 6 2 5 4 8 3 7]' into a list of ints."""
    s = s.strip()
    # Remove brackets
    s = s.strip('[]')
    if not s:
        return []
    # Split on whitespace
    parts = s.split()
    return [int(p) for p in parts]


def main():
    raw = sys.stdin.read()
    # Find CASE0=... line
    m = re.search(r'CASE0\s*=\s*(\[.*?\])', raw, re.DOTALL)
    if not m:
        print("0")
        return
    heights = parse_vector(m.group(1))
    result = solve(heights)
    print(result)


CASES = [
    {"heights": [1, 8, 6, 2, 5, 4, 8, 3, 7]},
    {"heights": [1, 1]},
    {"heights": [4, 3, 2, 1, 4]},
    {"heights": [1, 2, 1]},
    {"heights": [2, 3, 4, 5, 18, 17, 6]},
    {"heights": [0, 0, 0, 0]},
    {"heights": [5, 4, 3, 2, 1]},
    {"heights": [100000] * 1000},  # large uniform array
    {"heights": [1, 2]},
    {"heights": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]},
]


if __name__ == '__main__':
    # First, produce expected results from CASES for the required JSON output format
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
    # Also run main() so the script is a runnable solution when piped input
    # (commented out to avoid double-output; main() handles stdin when run normally)
    # main()
