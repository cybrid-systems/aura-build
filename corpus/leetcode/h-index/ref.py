import sys, json

def solve(citations):
    if not citations:
        return 0
    n = len(citations)
    # Counting sort approach O(n) given bounded citations, fallback to sort O(n log n)
    max_cit = max(citations)
    # Use sort for generality; still O(n log n) which is fine for n up to 1e5
    citations.sort(reverse=True)
    h = 0
    for i, c in enumerate(citations):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h

CASES = [
    {"citations": [3, 0, 6, 1, 5]},
    {"citations": [0]},
    {"citations": [1]},
    {"citations": [0, 0, 0]},
    {"citations": [100]},
    {"citations": [1, 2, 3, 4, 5]},
    {"citations": [5, 5, 5, 5, 5]},
    {"citations": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(list(c["citations"]))
        out.append({"id": i, "input": {"citations": c["citations"]},
                    "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
