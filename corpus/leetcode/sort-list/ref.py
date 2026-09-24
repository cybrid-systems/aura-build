def solve(head):
    # Input is a Python list representing the linked list.
    # Return a Python list representing the sorted linked list.
    if not head or len(head) <= 1:
        return list(head) if head else []
    # Use sort - but problem asks for O(n log n) linked list style.
    # We interpret "linked list" loosely: input is a sequence; output a sequence.
    # For correctness within constraints, just sort the list.
    return sorted(head)


CASES = [
    {"head": [4, 2, 1, 3]},
    {"head": [-1, 5, 3, 4, 0]},
    {"head": []},
    {"head": [1]},
    {"head": [2, 1]},
    {"head": [1, 2, 3, 4, 5]},
    {"head": [5, 4, 3, 2, 1]},
    {"head": [3, 3, 1, 2, 3, 1]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(**c)
        # Recompute expected from result for canonical form
        # Expected is the sorted version of input
        inp = c["head"]
        expected = sorted(inp)
        out.append({
            "id": i,
            "input": {"head": inp},
            "expected": json.dumps(expected, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
