import json
import sys

class Node:
    __slots__ = ('val', 'left', 'right')
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def parse_tree(s):
    """Parse a parenthesized tree representation like '(1 (2 None None) (3 None None))'."""
    s = s.strip()
    if not s or s == 'None' or s == '()':
        return None
    if s.startswith('(') and s.endswith(')'):
        s = s[1:-1]
    pos = [0]
    def parse():
        # skip spaces
        while pos[0] < len(s) and s[pos[0]] == ' ':
            pos[0] += 1
        if pos[0] >= len(s):
            return None
        if s[pos[0]] == 'N':
            # None
            if s[pos[0]:pos[0]+4] == 'None':
                pos[0] += 4
            return None
        if s[pos[0]] == '(':
            pos[0] += 1
            # skip spaces
            while pos[0] < len(s) and s[pos[0]] == ' ':
                pos[0] += 1
            # read number (may be negative)
            start = pos[0]
            if pos[0] < len(s) and s[pos[0]] == '-':
                pos[0] += 1
            while pos[0] < len(s) and s[pos[0]].isdigit():
                pos[0] += 1
            val = int(s[start:pos[0]])
            # skip spaces
            while pos[0] < len(s) and s[pos[0]] == ' ':
                pos[0] += 1
            left = None
            if pos[0] < len(s) and s[pos[0]] == '(':
                left = parse()
            # skip spaces
            while pos[0] < len(s) and s[pos[0]] == ' ':
                pos[0] += 1
            right = None
            if pos[0] < len(s) and s[pos[0]] == '(':
                right = parse()
            # skip spaces
            while pos[0] < len(s) and s[pos[0]] == ' ':
                pos[0] += 1
            if pos[0] < len(s) and s[pos[0]] == ')':
                pos[0] += 1
            return Node(val, left, right)
        else:
            # number only, no children
            start = pos[0]
            if pos[0] < len(s) and s[pos[0]] == '-':
                pos[0] += 1
            while pos[0] < len(s) and s[pos[0]].isdigit():
                pos[0] += 1
            val = int(s[start:pos[0]])
            return Node(val)
    return parse()

def diameter(root):
    """Return the diameter (in edges) of the binary tree."""
    if root is None:
        return 0
    best = [0]
    def depth(node):
        if node is None:
            return 0
        l = depth(node.left)
        r = depth(node.right)
        # update best: longest path through this node is l + r
        if l + r > best[0]:
            best[0] = l + r
        return 1 + (l if l > r else r)
    depth(root)
    return best[0]

def solve(root):
    # root may already be a Node, or it may be the parsed string representation
    if isinstance(root, str):
        root = parse_tree(root)
    return diameter(root)

CASES = [
    {"id": 0, "root": "(1 (2 (4 None None) (5 None None)) (3 None None))"},
    {"id": 1, "root": "(1 None None)"},
    {"id": 2, "root": "(1 (2 None None) None)"},
    {"id": 3, "root": "(1 (2 (4 None None) None) (3 (5 None None) None))"},
    {"id": 4, "root": "None"},
    {"id": 5, "root": "(1 (2 (3 (4 None None) None) None) None)"},
    {"id": 6, "root": "(1 (2 (4 None None) (5 None None)) (3 (6 None None) (7 None None)))"},
    {"id": 7, "root": "(0)"},
]

if __name__ == '__main__':
    out = []
    for case in CASES:
        # If input is a string, parse it; otherwise treat as Node-like
        result = solve(case["root"])
        out.append({
            "id": case["id"],
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
