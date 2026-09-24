import sys
from typing import Optional, List

class TreeNode:
    __slots__ = ('val', 'left', 'right')
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: Optional[TreeNode]) -> Optional[TreeNode]:
    if root is None:
        return None
    root.left = solve(root.left)
    root.right = solve(root.right)
    if root.val == 0 and root.left is None and root.right is None:
        return None
    return root

def build_tree(values: List[Optional[int]]) -> Optional[TreeNode]:
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = [root]
    i = 1
    while queue and i < len(values):
        node = queue.pop(0)
        if i < len(values):
            v = values[i]
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
            i += 1
        if i < len(values):
            v = values[i]
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
            i += 1
    return root

def tree_to_level_order(root: Optional[TreeNode]) -> List[Optional[int]]:
    if root is None:
        return []
    result = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node is None:
            result.append(None)
        else:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
    # Trim trailing Nones
    while result and result[-1] is None:
        result.pop()
    return result

def parse_values(s: str) -> List[Optional[int]]:
    s = s.strip()
    if not s:
        return []
    parts = [p.strip() for p in s.split(',')]
    out = []
    for p in parts:
        if p.lower() == 'null' or p == '':
            out.append(None)
        else:
            out.append(int(p))
    return out

def format_output(vals: List[Optional[int]]) -> str:
    if not vals:
        return 'null'
    return ', '.join('null' if v is None else str(v) for v in vals)

def run_io(input_data: str) -> str:
    lines = input_data.strip().split('\n')
    idx = 0
    # First line: CASE0=<n>
    header = lines[idx].strip()
    idx += 1
    n = int(header.split('=')[1])
    outputs = []
    for i in range(n):
        m_line = lines[idx].strip()
        idx += 1
        # m is number of values, but we can ignore and just read next line
        values_line = lines[idx].strip()
        idx += 1
        values = parse_values(values_line)
        root = build_tree(values)
        pruned = solve(root)
        level = tree_to_level_order(pruned)
        outputs.append(f"OUT{i}={format_output(level)}")
    return '\n'.join(outputs)

# Define solve signature as required: also expose a callable that takes root
# But the problem requires I/O. The harness calls solve() on CASES for printing JSON.
# Per instructions, define solve(...) with clear signature.
# The problem's actual solve operates on root and returns root.
# For test cases via CASES, we test the tree-pruning logic.

def solve_root(root: Optional[TreeNode]) -> Optional[TreeNode]:
    return solve(root)

CASES = []

# Case 0: single 1
CASES.append({
    'root': build_tree([1])
})

# Case 1: single 0
CASES.append({
    'root': build_tree([0])
})

# Case 2: classic LeetCode example
CASES.append({
    'root': build_tree([1, 1, 0, 1, 1, 0, 1, None, None, None, None, None, None, None, None])
})

# Case 3: all zeros -> None
CASES.append({
    'root': build_tree([0, 0, 0, None, None, 0, 0])
})

# Case 4: only right side valid
CASES.append({
    'root': build_tree([1, 0, 1, 0, 0, 0, 1, None, None, None, None, None, None, None, None])
})

# Case 5: root is None
CASES.append({
    'root': None
})

# Case 6: tree with mixed deep structure
CASES.append({
    'root': build_tree([1, 0, 0, 0, 0, 0, 1, None, None, 0, 1, None, None, None, None])
})

# Case 7: tree that fully prunes left, keeps right
CASES.append({
    'root': build_tree([1, 0, 1, 0, 0, 1, 1])
})

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        root = case['root']
        pruned = solve(root)
        level = tree_to_level_order(pruned)
        expected_str = format_output(level)
        results.append({
            'id': i,
            'input': {'level_order_in': format_output([v if v is not None else None for v in (tree_to_level_order(root) if root else [])])},
            'expected': expected_str
        })
    # For cases where input root is None, adjust
    for i, r in enumerate(results):
        if r['expected'] == '' or r['expected'] == 'null':
            pass
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
