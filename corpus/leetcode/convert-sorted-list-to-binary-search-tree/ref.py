import json
import sys
from typing import Optional

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(head: Optional[ListNode]) -> Optional[TreeNode]:
    # Convert linked list to array for easier indexing
    values = []
    curr = head
    while curr is not None:
        values.append(curr.val)
        curr = curr.next
    
    def build(left: int, right: int) -> Optional[TreeNode]:
        if left > right:
            return None
        mid = (left + right) // 2
        node = TreeNode(values[mid])
        node.left = build(left, mid - 1)
        node.right = build(mid + 1, right)
        return node
    
    return build(0, len(values) - 1)

def build_list(vals):
    if not vals:
        return None
    head = ListNode(vals[0])
    curr = head
    for v in vals[1:]:
        curr.next = ListNode(v)
        curr = curr.next
    return head

def tree_to_list(root):
    """Serialize tree to level-order list for comparison."""
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
    # Remove trailing Nones for cleaner output
    while result and result[-1] is None:
        result.pop()
    return result

def is_balanced_and_bst(root, values_set):
    """Verify the result is a valid height-balanced BST with correct values."""
    if root is None:
        return True
    
    def check(node, min_val, max_val):
        if node is None:
            return True, 0
        if node.val <= min_val or node.val >= max_val:
            return False, 0
        left_ok, left_h = check(node.left, min_val, node.val)
        if not left_ok:
            return False, 0
        right_ok, right_h = check(node.right, node.val, max_val)
        if not right_ok:
            return False, 0
        if abs(left_h - right_h) > 1:
            return False, 0
        return True, max(left_h, right_h) + 1
    
    ok, _ = check(root, float('-inf'), float('inf'))
    
    # Collect values via inorder
    inorder = []
    def inord(n):
        if n is None:
            return
        inord(n.left)
        inorder.append(n.val)
        inord(n.right)
    inord(root)
    
    return ok and sorted(inorder) == sorted(values_set) and len(inorder) == len(values_set)

CASES = [
    {"vals": []},
    {"vals": [0]},
    {"vals": [1, 2, 3]},
    {"vals": [-10, -3, 0, 5, 9]},
    {"vals": [1, 2, 3, 4, 5, 6, 7, 8]},
    {"vals": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
    {"vals": [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]},
    {"vals": [42]},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        vals = case["vals"]
        head = build_list(vals)
        result = solve(head)
        results.append({
            "id": i,
            "input": {"length": len(vals), "vals": vals},
            "expected": json.dumps(tree_to_list(result), separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
