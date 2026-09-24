import json
from typing import Optional

class Node:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_level(values):
    if not values or values[0] is None:
        return None
    root = Node(values[0])
    queue = [root]
    i = 1
    while queue and i < len(values):
        node = queue.pop(0)
        if i < len(values):
            v = values[i]; i += 1
            if v is not None:
                node.left = Node(v)
                queue.append(node.left)
        if i < len(values):
            v = values[i]; i += 1
            if v is not None:
                node.right = Node(v)
                queue.append(node.right)
    return root

def to_level(root):
    if not root:
        return []
    out = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node is None:
            out.append(None)
        else:
            out.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out

def recover(root: Optional[Node]) -> Optional[Node]:
    if not root:
        return root
    first = second = prev = None
    curr = root
    while curr:
        if not curr.left:
            # visit curr
            if prev and prev.val > curr.val:
                if not first:
                    first = prev; second = curr
                else:
                    second = curr
            prev = curr
            curr = curr.right
        else:
            # find inorder predecessor
            pred = curr.left
            while pred.right and pred.right is not curr:
                pred = pred.right
            if not pred.right:
                pred.right = curr
                curr = curr.left
            else:
                pred.right = None
                # visit curr
                if prev and prev.val > curr.val:
                    if not first:
                        first = prev; second = curr
                    else:
                        second = curr
                prev = curr
                curr = curr.right
    if first and second:
        first.val, second.val = second.val, first.val
    return root

def solve(root):
    # root may arrive as a Node or as a list (level-order)
    if isinstance(root, list):
        root = build_level(root)
    recover(root)
    return to_level(root)

CASES = [
    {'root': [4, 3, 7, None, None, 2, 6]},  # basic
    {'root': [1, 3, None, None, 2]},         # swap adjacent in in-order
    {'root': [3, None, 2, None, 1]},         # right-skewed
    {'root': [2, 1, 3]},                      # already valid (no swap needed but per problem must swap two — skip)
    {'root': [10, 5, 15, 2, 7, 12, 20]},      # valid, but problem requires swap — use it anyway
]

if __name__ == '__main__':
    results = []
    for i, c in enumerate(CASES):
        out = solve(c['root'])
        results.append({'id': i, 'input': c, 'expected': json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    # Note: this problem has no test cases with expected answers in prompt.
    # We just print outputs for verification.
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
