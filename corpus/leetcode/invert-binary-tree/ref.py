import json
from collections import deque

class Node:
    __slots__ = ('val', 'left', 'right')
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def parse(s):
    if s is None:
        return None
    s = s.strip()
    if s == '' or s.lower() == 'nil':
        return None
    # Try JSON list form
    if s.startswith('['):
        arr = json.loads(s)
        if not arr:
            return None
        nodes = [None if v is None else Node(v) for v in arr]
        n = len(nodes)
        for i, node in enumerate(nodes):
            if node is None:
                continue
            li = 2*i + 1
            ri = 2*i + 2
            node.left = nodes[li] if li < n else None
            node.right = nodes[ri] if ri < n else None
        return nodes[0]
    # Lisp-like form: (root (left) (right))
    # Tokenize
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in '()':
            tokens.append(c)
            i += 1
            continue
        j = i
        while j < len(s) and not s[j].isspace() and s[j] not in '()':
            j += 1
        tokens.append(s[i:j])
        i = j

    def parse_node(idx):
        if tokens[idx] == ')':
            return None, idx + 1
        # Expect '('
        if tokens[idx] != '(':
            # Shouldn't happen
            return None, idx
        idx += 1  # past '('
        # Read value
        val_token = tokens[idx]
        if val_token.lower() == 'nil':
            return None, idx + 1
        try:
            val = int(val_token)
        except ValueError:
            val = val_token
        idx += 1
        left, idx = parse_node(idx)
        right, idx = parse_node(idx)
        if tokens[idx] == ')':
            idx += 1
        return Node(val, left, right), idx

    root, _ = parse_node(0)
    return root

def serialize(root):
    if root is None:
        return None
    out = []
    queue = deque([root])
    # Gather all nodes' indices in level order
    nodes = [root]
    head = 0
    while head < len(nodes):
        n = nodes[head]
        head += 1
        if n is None:
            continue
        nodes.append(n.left)
        nodes.append(n.right)
    # Trim trailing Nones
    while nodes and nodes[-1] is None:
        nodes.pop()
    return [n.val if n is not None else None for n in nodes]

def solve(root):
    if root is None:
        return None
    # Iterative inversion using stack
    stack = [root]
    while stack:
        node = stack.pop()
        node.left, node.right = node.right, node.left
        if node.left:
            stack.append(node.left)
        if node.right:
            stack.append(node.right)
    return root

CASES = [
    {"s": "nil"},
    {"s": ""},
    {"s": "[4,2,7,1,3,6,9]"},
    {"s": "[1,2,3]"},
    {"s": "[1,2,3,4]"},
    {"s": "(root (1 (2 (4 nil nil) (5 nil nil)) (3 (6 nil nil) nil)))"},
    {"s": "[]"},
]

def result_repr(s):
    root = parse(s)
    new_root = solve(root)
    return {"input_serialization": s, "tree": serialize(new_root)}

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        s = c["s"]
        root = parse(s)
        new_root = solve(root)
        result = {"tree": serialize(new_root)}
        out.append({"id": i, "input": {"s": s}, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
