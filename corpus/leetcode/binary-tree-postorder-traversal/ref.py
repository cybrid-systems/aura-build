def solve(root):
    """Postorder traversal using two stacks iteratively."""
    if root is None:
        return []
    # Build tree nodes from the compact representation
    nodes = {}
    # Recursive construction handled by caller-style invocation? 
    # But here solve is called with root already as a dict tree.
    # The representation: root is either None or a dict with keys 'root','left','right'.
    
    def build(spec):
        if spec is None:
            return None
        node = TreeNode(spec['root'])
        node.left = build(spec.get('left'))
        node.right = build(spec.get('right'))
        return node
    
    tree = build(root)
    if tree is None:
        return []
    
    stack1 = [tree]
    stack2 = []
    while stack1:
        node = stack1.pop()
        stack2.append(node)
        if node.left:
            stack1.append(node.left)
        if node.right:
            stack1.append(node.right)
    return [n.val for n in stack2]


class TreeNode:
    __slots__ = ('val', 'left', 'right')
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


CASES = [
    # Empty tree
    {'root': None},
    # Single node
    {'root': {'root': 1}},
    # Two levels, full
    {'root': {'root': 1, 'left': {'root': 2}, 'right': {'root': 3}}},
    # Left-skewed chain: 1->2->3->4
    {'root': {'root': 1, 'left': {'root': 2, 'left': {'root': 3, 'left': {'root': 4}}}}},
    # Right-skewed chain
    {'root': {'root': 1, 'right': {'root': 2, 'right': {'root': 3, 'right': {'root': 4}}}}},
    # Mixed: example from prompt [4,5,2,3,1]
    {'root': {'root': 1, 'left': {'root': 2, 'left': {'root': 4}, 'right': {'root': 5}}, 'right': {'root': 3}}},
    # Only left child
    {'root': {'root': 1, 'left': {'root': 2}}},
    # Only right child
    {'root': {'root': 1, 'right': {'root': 2}}},
    # Larger balanced tree
    {'root': {'root': 1,
              'left': {'root': 2, 'left': {'root': 4}, 'right': {'root': 5}},
              'right': {'root': 3, 'left': {'root': 6}, 'right': {'root': 7}}}},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(case['root'])
        results.append({
            'id': i,
            'input': case,
            'expected': json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
