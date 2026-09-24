import json
import sys
from typing import Optional, Dict, Any, List

def solve(root: Optional[Dict[str, Any]]) -> int:
    best = [float('-inf')]
    
    def gain(node):
        if node is None:
            return 0
        left = gain(node.get(':left'))
        right = gain(node.get(':right'))
        left_max = max(0, left)
        right_max = max(0, right)
        cand = node.get(':val', 0) + left_max + right_max
        if cand > best[0]:
            best[0] = cand
        return node.get(':val', 0) + max(left_max, right_max)
    
    gain(root)
    return best[0]


def build_tree(values):
    if not values:
        return None
    nodes = [None if v is None else {':val': v, ':left': None, ':right': None} for v in values]
    kids = nodes[::-1]
    root = kids.pop()
    for node in nodes:
        if node:
            if kids:
                node[':left'] = kids.pop()
            if kids:
                node[':right'] = kids.pop()
    return root


CASES = [
    {"id": 0, "input": {"root": build_tree([1, 2, 3])}, "expected": None},
    {"id": 1, "input": {"root": build_tree([-10, 9, 20, None, None, 15, 7])}, "expected": None},
    {"id": 2, "input": {"root": build_tree([-3])}, "expected": None},
    {"id": 3, "input": {"root": build_tree([2, -1])}, "expected": None},
    {"id": 4, "input": {"root": build_tree([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1])}, "expected": None},
    {"id": 5, "input": {"root": build_tree([-1, -2, -3])}, "expected": None},
    {"id": 6, "input": {"root": build_tree([1, -2, 3])}, "expected": None},
    {"id": 7, "input": {"root": build_tree([0])}, "expected": None},
]


if __name__ == '__main__':
    out = []
    for case in CASES:
        result = solve(case['input']['root'])
        out.append({
            "id": case['id'],
            "input": case['input'],
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
