import json
from typing import List


def solve(customers: List[int], grumpy: List[int], k: int) -> int:
    n = len(customers)
    # Base satisfied: those naturally satisfied (grumpy[i]==0 or customers[i]<=grumpy[i])
    base = 0
    extra = []  # extra satisfaction gained if minute i is covered by technique
    for i in range(n):
        if grumpy[i] == 0:
            base += customers[i]
            extra.append(0)
        else:
            # grumpy minute: naturally satisfied only if customers[i] <= grumpy[i]
            # The "extra" is customers[i] if not naturally satisfied, else 0
            if customers[i] <= grumpy[i]:
                base += customers[i]
                extra.append(0)
            else:
                extra.append(customers[i])
    # Sliding window of size k on extra to find max additional satisfaction
    window = sum(extra[:k])
    best = window
    for i in range(k, n):
        window += extra[i] - extra[i - k]
        if window > best:
            best = window
    return base + best


CASES = [
    {
        "id": 0,
        "input": {
            "customers": [1, 0, 1, 2, 1, 1, 7, 5],
            "grumpy": [0, 1, 0, 1, 0, 1, 0, 1],
            "k": 3,
        },
        # Expected: 16
    },
    {
        "id": 1,
        "input": {
            "customers": [1],
            "grumpy": [0],
            "k": 1,
        },
        # Expected: 1
    },
    {
        "id": 2,
        "input": {
            "customers": [5],
            "grumpy": [3],
            "k": 1,
        },
        # Expected: 5 (technique covers it)
    },
    {
        "id": 3,
        "input": {
            "customers": [5, 5, 5, 5, 5],
            "grumpy": [0, 0, 0, 0, 0],
            "k": 2,
        },
        # Expected: 25
    },
    {
        "id": 4,
        "input": {
            "customers": [10, 1, 0, 10],
            "grumpy": [1, 0, 1, 1],
            "k": 2,
        },
        # Expected: 21 (base 1, best extra window [10] or [10]=10, so 11... let's compute)
        # Actually base=1, extra=[10,0,0,10], window k=2: 10, 0, 10 -> max 10, total 11
    },
    {
        "id": 5,
        "input": {
            "customers": [2, 6, 3, 1, 2, 4, 1, 2, 8, 2],
            "grumpy": [1, 0, 1, 1, 0, 1, 1, 1, 0, 1],
            "k": 3,
        },
        # Leetcode classic: expected 21
    },
    {
        "id": 6,
        "input": {
            "customers": [1, 2, 3, 4, 5],
            "grumpy": [1, 1, 1, 1, 1],
            "k": 5,
        },
        # Expected: 15
    },
]


if __name__ == "__main__":
    results = []
    for case in CASES:
        inp = case["input"]
        out = solve(inp["customers"], inp["grumpy"], inp["k"])
        results.append({
            "id": case["id"],
            "input": inp,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
