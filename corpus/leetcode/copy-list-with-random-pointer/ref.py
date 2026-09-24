import json
import sys

def solve(n, nodes):
    if n == 0:
        return -1
    
    # Build original list representation
    originals = []
    for i in range(n):
        val, nxt, rnd = nodes[i]
        originals.append((val, nxt, rnd))
    
    # Build mapping from original index to new index
    orig_to_new = {i: i for i in range(n)}
    
    # Build the deep copy's next pointers based on original next pointers
    # The new nodes are just allocated at the same indices for simplicity
    
    # Actually, we need to construct the new list and return head index
    # The new list has the same structure (same indices work)
    
    # Verify we can build the copy properly
    new_nodes = []
    for i in range(n):
        val = originals[i][0]
        new_nodes.append([val, -1, -1])  # val, next, random
    
    # Set next pointers
    for i in range(n):
        nxt = originals[i][1]
        if nxt != -1:
            new_nodes[i][1] = nxt
    
    # Set random pointers
    for i in range(n):
        rnd = originals[i][2]
        if rnd != -1:
            new_nodes[i][2] = rnd
    
    # Return head index, which is 0 (since the input list starts at index 0)
    return 0


CASES = [
    {"n": 0, "nodes": []},
    {"n": 1, "nodes": [(10, -1, -1)]},
    {"n": 3, "nodes": [
        (10, 1, 2),
        (20, 2, -1),
        (30, -1, 1),
    ]},
    {"n": 5, "nodes": [
        (10, -1, -1),
        (20, 0, 2),
        (30, 1, -1),
        (40, 2, 0),
        (50, 3, 1),
    ]},
    {"n": 4, "nodes": [
        (1, 1, 2),
        (2, 2, 2),
        (3, 3, 0),
        (4, -1, -1),
    ]},
    {"n": 2, "nodes": [
        (5, 1, 1),
        (7, -1, -1),
    ]},
    {"n": 6, "nodes": [
        (1, 1, -1),
        (2, 2, 4),
        (3, 3, 0),
        (4, 4, 2),
        (5, 5, 5),
        (6, -1, -1),
    ]},
]


if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        n = case["n"]
        nodes = case["nodes"]
        result = solve(n, nodes)
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
