import sys
import json

class Node:
    def __init__(self, val=0, left=None, right=None, nxt=None):
        self.val = val
        self.left = left
        self.right = right
        self.next = nxt

def solve(root: Node) -> Node:
    if root is None:
        return root
    leftmost = root
    while leftmost.left is not None:
        dummy = Node(0)
        prev = dummy
        curr = leftmost
        while curr is not None:
            prev.next = curr.left
            prev = prev.next
            prev.next = curr.right
            prev = prev.next
            curr = curr.next
        leftmost = dummy.next
    return root

def build_tree(level_order):
    if not level_order:
        return None
    nodes = [None if v == 'N' else Node(int(v)) for v in level_order]
    n = len(nodes)
    for i in range(n):
        if nodes[i] is None:
            continue
        li = 2 * i + 1
        ri = 2 * i + 2
        if li < n and nodes[li] is not None:
            nodes[i].left = nodes[li]
        if ri < n and nodes[ri] is not None:
            nodes[i].right = nodes[ri]
    return nodes[0]

def level_order_with_next(root):
    if root is None:
        return []
    result = []
    level = root
    while level is not None:
        curr = level
        level_vals = []
        next_level = None
        while curr is not None:
            level_vals.append(curr.val)
            if next_level is None and curr.left is not None:
                next_level = curr.left
            curr = curr.next
        result.append(level_vals)
        level = next_level
    return result

CASES = [
    {"size": 1, "level_order": ["1"]},
    {"size": 3, "level_order": ["1", "2", "3"]},
    {"size": 7, "level_order": ["1", "2", "3", "4", "5", "6", "7"]},
    {"size": 15, "level_order": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]},
    {"size": 2, "level_order": ["1", "2"]},
]

def main():
    arr = []
    for i, c in enumerate(CASES):
        root = build_tree(c["level_order"])
        solve(root)
        result = level_order_with_next(root)
        arr.append({
            "id": i,
            "input": {"size": c["size"], "level_order": c["level_order"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(arr, separators=(',', ':'), ensure_ascii=False))

if __name__ == '__main__':
    main()
