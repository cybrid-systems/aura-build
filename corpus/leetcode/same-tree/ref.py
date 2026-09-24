import json

class TreeNode:
    __slots__ = ('val', 'left', 'right')
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_tree(level_order):
    if not level_order:
        return None
    vals = list(level_order)
    if vals[0] is None:
        return None
    root = TreeNode(vals[0])
    queue = [root]
    i = 1
    n = len(vals)
    while queue and i < n:
        node = queue.pop(0)
        # left child
        if i < n:
            if vals[i] is not None:
                node.left = TreeNode(vals[i])
                queue.append(node.left)
            i += 1
        # right child
        if i < n:
            if vals[i] is not None:
                node.right = TreeNode(vals[i])
                queue.append(node.right)
            i += 1
    return root

def is_same(p, q):
    if p is None and q is None:
        return True
    if p is None or q is None:
        return False
    if p.val != q.val:
        return False
    return is_same(p.left, q.left) and is_same(p.right, q.right)

def solve(p, q):
    # Accept either tree nodes or level-order lists
    def _to_root(x):
        if x is None:
            return None
        if isinstance(x, TreeNode):
            return x
        return build_tree(x)
    return is_same(_to_root(p), _to_root(q))

CASES = [
    {'p': [1, 2, 3], 'q': [1, 2, 3]},
    {'p': [1, 2], 'q': [1, None, 2]},
    {'p': [1, 2, 1], 'q': [1, 1, 2]},
    {'p': [], 'q': []},
    {'p': [], 'q': [1]},
    {'p': [1, None, 2, None, 3], 'q': [1, None, 2, None, 3]},
    {'p': [1, 2, None, None, 3], 'q': [1, 2, None, None, 3]},
    {'p': [1, 2, 3, None, None, None, 4], 'q': [1, 2, 3, None, None, None, 4]},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        p = case.get('p')
        q = case.get('q')
        result = solve(p, q)
        input_repr = {'p': p, 'q': q}
        # expected is the computed result (self-consistent check via JSON serialization)
        expected_repr = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        results.append({
            'id': idx,
            'input': input_repr,
            'expected': expected_repr,
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
