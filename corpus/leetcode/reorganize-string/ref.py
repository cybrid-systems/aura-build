import sys
import json
import heapq
from collections import Counter

def solve(s: str) -> str:
    if not s:
        return ""
    n = len(s)
    counts = Counter(s)
    # Check feasibility
    max_count = max(counts.values())
    if max_count > (n + 1) // 2:
        return ""
    # Max-heap by count (use negative for heapq)
    heap = [(-c, ch) for ch, c in counts.items()]
    heapq.heapify(heap)
    result = []
    prev_count = 0
    prev_char = ''
    while heap:
        count, ch = heapq.heappop(heap)
        result.append(ch)
        # Since count is negative, add 1 to make it closer to 0
        if count + 1 < 0:
            heapq.heappush(heap, (count + 1, ch))
    # Verify no two adjacent are same (sanity)
    res_str = ''.join(result)
    for i in range(len(res_str) - 1):
        if res_str[i] == res_str[i+1]:
            return ""
    return res_str

CASES = [
    {"s": ""},
    {"s": "a"},
    {"s": "aa"},
    {"s": "aaab"},
    {"s": "aab"},
    {"s": "abc"},
    {"s": "aabbcc"},
    {"s": "aaabc"},
    {"s": "vvvlo"},
    {"s": "aaaaaaaaaab"},
    {"s": "bbbbbbaaa"},
    {"s": "ababab"},
    {"s": "aaabbbccc"},
    {"s": "aabbc"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["s"])
        results.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
