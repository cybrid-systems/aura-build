import json
from typing import Optional

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val: int = 0, left: 'Optional[TreeNode]' = None, right: 'Optional[TreeNode]' = None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: Optional[TreeNode], targetSum: int) -> bool:
    if root is None:
        return False
    # Leaf check
    if root.left is None and root.right is None:
        return root.val == targetSum
    remaining = targetSum - root.val
    return solve(root.left, remaining) or solve(root.right, remaining)

def build_tree(level_order: str) -> Optional[TreeNode]:
    """Build a binary tree from level-order BFS representation.
    Tokens are integers or 'null'. Empty input -> None.
    """
    tokens = [t for t in level_order.strip().split(' ') if t != '']
    if not tokens:
        return None
    if tokens[0] == 'null':
        return None
    try:
        root = TreeNode(int(tokens[0]))
    except ValueError:
        return None
    
    queue = [root]
    idx = 1
    n = len(tokens)
    
    while queue and idx < n:
        node = queue.pop(0)
        # Left child
        if idx < n:
            if tokens[idx] != 'null':
                try:
                    node.left = TreeNode(int(tokens[idx]))
                    queue.append(node.left)
                except ValueError:
                    pass
            idx += 1
        # Right child
        if idx < n:
            if tokens[idx] != 'null':
                try:
                    node.right = TreeNode(int(tokens[idx]))
                    queue.append(node.right)
                except ValueError:
                    pass
            idx += 1
    return root

def parse_case(case_str: str):
    """Parse 'tree,sum=K' into (root, targetSum)."""
    # Split on first comma
    comma_idx = case_str.find(',')
    if comma_idx == -1:
        return None, 0
    tree_part = case_str[:comma_idx]
    rest = case_str[comma_idx+1:]
    # rest is like 'sum=K'
    if rest.startswith('sum='):
        target_sum = int(rest[4:])
    else:
        target_sum = 0
    root = build_tree(tree_part)
    return root, target_sum

def parse_expected(ans_str: str) -> bool:
    return ans_str.strip().lower() == 'true'

# Test cases: each is (id, input_dict)
CASES = [
    {"id": 0, "input": {"case": "-10 9 20 null null 15 7", "sum": 22}, "expected": True},
    {"id": 1, "input": {"case": "1 2 3", "sum": 5}, "expected": False},
    {"id": 2, "input": {"case": "", "sum": 0}, "expected": False},
    {"id": 3, "input": {"case": "5 4 8 11 null 13 4 7 2 null null null 1", "sum": 22}, "expected": True},
    {"id": 4, "input": {"case": "1 2", "sum": 1}, "expected": False},
    {"id": 5, "input": {"case": "1 2", "sum": 3}, "expected": True},
    {"id": 6, "input": {"case": "0", "sum": 0}, "expected": True},
    {"id": 7, "input": {"case": "-3", "sum": -3}, "expected": True},
    {"id": 8, "input": {"case": "-2 null -3", "sum": -5}, "expected": True},
]

def run_case(case_dict):
    case_str = case_dict["input"]["case"]
    target_sum = case_dict["input"]["sum"]
    root, ts = parse_case(f"{case_str},sum={target_sum}")
    result = solve(root, ts)
    return result

if __name__ == '__main__':
    output = []
    for c in CASES:
        result = run_case(c)
        expected = c["expected"]
        output.append({
            "id": c["id"],
            "input": c["input"],
            "expected": json.dumps(expected, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
