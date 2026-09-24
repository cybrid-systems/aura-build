import json
from collections import Counter

def solve(tasks: str) -> int:
    if not tasks:
        return 0
    counts = Counter(tasks)
    f_max = max(counts.values())
    n_max = sum(1 for v in counts.values() if v == f_max)
    # Frame: (f_max - 1) gaps, each n_max slots wide + 1 cooldown slot
    frame_len = (f_max - 1) * n_max + (f_max - 1) + n_max
    # Equivalent: (f_max - 1) * (n_max + 1) + n_max
    return max(frame_len, len(tasks))

CASES = [
    {"tasks": "AAABBC"},
    {"tasks": "A"},
    {"tasks": "ABC"},
    {"tasks": "AAAA"},
    {"tasks": "ABABAB"},
    {"tasks": "AAABBB"},
    {"tasks": "AAAAA"},
    {"tasks": "AAABBCC"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
