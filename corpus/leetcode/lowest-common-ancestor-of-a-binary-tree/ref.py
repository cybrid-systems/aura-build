import json

class Node:
    __slots__ = ('val', 'left', 'right')
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_tree(arr):
    if not arr or arr[0] is None:
        return None
    nodes = [None if v is None else Node(v) for v in arr]
    n = len(nodes)
    for i, node in enumerate(nodes):
        if node is None:
            continue
        li = 2*i + 1
        ri = 2*i + 2
        if li < n:
            node.left = nodes[li]
        if ri < n:
            node.right = nodes[ri]
    return nodes[0]

def find_node(root, val):
    if root is None:
        return None
    if root.val == val:
        return root
    left = find_node(root.left, val)
    if left is not None:
        return left
    return find_node(root.right, val)

def lca(root, p, q):
    if root is None or root is p or root is q:
        return root
    left = lca(root.left, p, q)
    right = lca(root.right, p, q)
    if left is not None and right is not None:
        return root
    return left if left is not None else right

def solve(root, p, q):
    return lca(root, p, q)

CASES = [
    {
        'id': 0,
        'root': [3, 9, 20, None, None, 15, 7],
        'p': 9,
        'q': 20,
    },
    {
        'id': 1,
        'root': [1, 2, 3, 4, 5, None, 6],
        'p': 4,
        'q': 5,
    },
    {
        'id': 2,
        'root': [1, 2],
        'p': 1,
        'q': 2,
    },
    {
        'id': 3,
        'root': [1],
        'p': 1,
        'q': 1,
    },
    {
        'id': 4,
        'root': [3, 5, 1, 6, 2, 0, 8, None, None, 7, 4],
        'p': 5,
        'q': 1,
    },
    {
        'id': 5,
        'root': [1, 2, 3, None, 4, None, 5],
        'p': 4,
        'q': 5,
    },
    {
        'id': 6,
        'root': [10, 5, 15, 3, 7, None, 20],
        'p': 3,
        'q': 7,
    },
    {
        'id': 7,
        'root': [1, 2, 3, 4, None, None, None],
        'p': 4,
        'q': 3,
    },
]

if __name__ == '__main__':
    out = []
    for case in CASES:
        root = build_tree(case['root'])
        p = find_node(root, case['p'])
        q = find_node(root, case['q'])
        if p is None:
            p = Node(case['p'])
        if q is None:
            q = Node(case['q'])
        result = solve(root, p, q)
        if result is None:
            expected = None
        else:
            expected = result.val
        out.append({
            'id': case['id'],
            'input': {'root': case['root'], 'p': case['p'], 'q': case['q']},
            'expected': json.dumps(expected, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
