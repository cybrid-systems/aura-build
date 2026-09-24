import sys
import json
from typing import Optional, List

def solve(case0: list) -> bool:
    if not case0:
        return True
    
    # Build tree from level-order array
    # Use index-based approach to avoid recursion depth issues
    n = len(case0)
    nodes = [None] * n
    for i in range(n):
        if case0[i] is not None:
            nodes[i] = {'val': case0[i], 'left': None, 'right': None}
    
    for i in range(n):
        if nodes[i] is not None:
            left_idx = 2 * i + 1
            right_idx = 2 * i + 2
            if left_idx < n:
                nodes[i]['left'] = nodes[left_idx]
            if right_idx < n:
                nodes[i]['right'] = nodes[right_idx]
    
    root = nodes[0]
    
    # Iterative in-order traversal to check strict ordering
    stack = []
    curr = root
    prev_val = None
    while stack or curr is not None:
        while curr is not None:
            stack.append(curr)
            curr = curr['left']
        curr = stack.pop()
        if prev_val is not None and curr['val'] <= prev_val:
            return False
        prev_val = curr['val']
        curr = curr['right']
    
    return True


CASES = [
    {"case0": []},
    {"case0": [2, 1, 3]},
    {"case0": [5, 1, 4, None, None, 3, 6]},
    {"case0": [1]},
    {"case0": [1, 1]},
    {"case0": [2, 2, 2]},
    {"case0": [5, 3, 7, 1, 4, 6, 8]},
    {"case0": [3, 2, 4, 1, None, None, None]},
]

if __name__ == '__main__':
    results = []
    for i, c in enumerate(CASES):
        result = solve(c['case0'])
        expected_str = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        results.append({
            "id": i,
            "input": {"case0": c['case0']},
            "expected": expected_str
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
