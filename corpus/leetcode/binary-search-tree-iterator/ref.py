import json
import sys
from typing import Optional, List

class TreeNode:
    __slots__ = ('val', 'left', 'right')
    def __init__(self, val: int = 0, left: Optional['TreeNode'] = None, right: Optional['TreeNode'] = None):
        self.val = val
        self.left = left
        self.right = right

def build_tree(arr: List[Optional[int]]) -> Optional[TreeNode]:
    if not arr or arr[0] is None:
        return None
    root = TreeNode(int(arr[0]))
    nodes = [root]
    i = 1
    while i < len(arr):
        if not nodes:
            break
        parent = nodes.pop(0)
        # left
        if i < len(arr):
            v = arr[i]
            i += 1
            if v is not None:
                parent.left = TreeNode(int(v))
                nodes.append(parent.left)
        else:
            break
        # right
        if i < len(arr):
            v = arr[i]
            i += 1
            if v is not None:
                parent.right = TreeNode(int(v))
                nodes.append(parent.right)
        else:
            break
    return root

class BSTIterator:
    def __init__(self, root: Optional[TreeNode]):
        self.root = root
        self.stack: List[TreeNode] = []
        self._cur = root
        self._init_state = (root, [])
        self._initialized = False
        # do initial traversal? We'll lazy push so has_next works without advancing
        # but we need to initialize stack to leftmost path so next() works correctly.
        self._reset_state(root)
        self._initialized = True

    def _reset_state(self, root: Optional[TreeNode]):
        self.stack = []
        node = root
        while node is not None:
            self.stack.append(node)
            node = node.left

    def reset(self, root: Optional[TreeNode] = None):
        if root is not None:
            self.root = root
        self._reset_state(self.root)

    def has_next(self) -> bool:
        return len(self.stack) > 0

    def next(self) -> int:
        if not self.stack:
            raise StopIteration
        node = self.stack.pop()
        val = node.val
        # push leftmost path of right subtree
        nxt = node.right
        while nxt is not None:
            self.stack.append(nxt)
            nxt = nxt.left
        return val

def solve(case_lines: List[str]) -> List:
    # First line must be TREE:[...]
    first = case_lines[0]
    # parse TREE:[...]
    # find first '[' and last ']'
    lb = first.index('[')
    rb = first.rindex(']')
    body = first[lb+1:rb]
    if body.strip() == '':
        arr = []
    else:
        # split by comma, allow 'null' tokens
        raw_items = [x.strip() for x in body.split(',')]
        arr = []
        for x in raw_items:
            if x.lower() == 'null':
                arr.append(None)
            else:
                arr.append(int(x))
    root = build_tree(arr)
    it = BSTIterator(root)
    outputs = []
    for line in case_lines[1:]:
        if not line.startswith('CASE0='):
            continue
        payload = line[len('CASE0='):]
        if payload.startswith('OP:'):
            op = payload[3:]
            if op == 'next':
                if it.has_next():
                    val = it.next()
                    outputs.append(("next", val))
                else:
                    outputs.append(("next", None))
            elif op == 'has_next':
                outputs.append(("has_next", it.has_next()))
            elif op == 'reset':
                it.reset(root)
            elif op == 'end':
                pass
    return outputs

CASES = [
    # Test case 0: Basic example
    {
        "lines": [
            "CASE0=TREE:[7,3,15,null,null,9,20]",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:has_next",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:has_next",
            "CASE0=OP:end",
        ]
    },
    # Test case 1: Empty tree
    {
        "lines": [
            "CASE0=TREE:[]",
            "CASE0=OP:has_next",
            "CASE0=OP:next",
            "CASE0=OP:end",
        ]
    },
    # Test case 2: Single node
    {
        "lines": [
            "CASE0=TREE:[5]",
            "CASE0=OP:has_next",
            "CASE0=OP:next",
            "CASE0=OP:has_next",
            "CASE0=OP:end",
        ]
    },
    # Test case 3: Left-skewed tree
    {
        "lines": [
            "CASE0=TREE:[5,4,null,3,null,2,null,1]",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:has_next",
            "CASE0=OP:next",
            "CASE0=OP:has_next",
            "CASE0=OP:end",
        ]
    },
    # Test case 4: Right-skewed tree
    {
        "lines": [
            "CASE0=TREE:[1,null,2,null,3,null,4,null,5]",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:has_next",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:has_next",
            "CASE0=OP:end",
        ]
    },
    # Test case 5: Reset behavior
    {
        "lines": [
            "CASE0=TREE:[10,5,15,3,7,12,20]",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:reset",
            "CASE0=OP:next",
            "CASE0=OP:has_next",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:end",
        ]
    },
    # Test case 6: Full balanced tree
    {
        "lines": [
            "CASE0=TREE:[4,2,6,1,3,5,7]",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:next",
            "CASE0=OP:has_next",
            "CASE0=OP:end",
        ]
    },
]

def main():
    results = []
    for idx, case in enumerate(CASES):
        out = solve(case["lines"])
        # Convert to canonical form for JSON output
        canonical_out = []
        for entry in out:
            canonical_out.append(entry)
        results.append({
            "id": idx,
            "input": case,
            "expected": canonical_out
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))

if __name__ == '__main__':
    main()
